# -*- coding: utf-8 -*-
"""r2_vhodove.py - ДЪСКАТА от 7 рамки, в ДВАТА режима, и входовете от нея.

Режими:
  ОБЩИ  = РАМКИ_СВОИ_ЛИНИИ изключена: всичките 7 рамки четат ЕДНИ дневни линии
          (price_adj=0 - на СПОТ лентата дневната и интрадей кривата са ЕДНА,
          затова контрактният базис `tf_adj` е 0; в живото той е +9..+17$ и
          БУТА старото поведение още повече към лонг - казано, не премълчано)
  СВОИ  = РАМКИ_СВОИ_ЛИНИИ включена: всяка рамка смята линиите си от себе си

Присъдата на рамката: live_bot._resolve + live_bot._tier с ЖИВИТЕ ръчки
(ПОСОКА_ОТ_ЦЕНАТА=да, ПРЕМИУМ_ПО_ТОЧКИ=да, ПРЕМИУМ_ТОЧКИ=7).
Победителят: max(rank[клас], точки, БАВНОСТ) - както live_bot ред 7548.
Анти-спам ключът: от РАЗЛИЧНИТЕ отчети на дъската (live_bot ред 7590), НЕ от
победителя - точно затова разделянето на рамките мени и БРОЯ карти.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
KONV = IZM / "mer_celiyat-konveyer"
for p in (str(KONV), str(IZM / "mer_mnozhitelite"), str(IZM), str(REPO)):
    sys.path.insert(0, p)
import pq_lite as pl                                                 # noqa: E402
import live_bot as lb                                                # noqa: E402

T0 = time.time()
ИМЕНА = ["1мин", "5м", "15м", "30м", "1час", "4час", "1ден"]        # = lb.TFS редът
БАВНОСТ = {n: i for i, n in enumerate(ИМЕНА)}
TIER_NAME = np.array(["weak", "medium", "strong", "premium"])
COOL_MIN = 45          # gh.COOL_MIN - схемата, под която са мерени доставените клетки
COOL_FLIP = 15


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


def tochki(cN, hN, lN, R):
    def nn(a):
        return ~np.isnan(a)
    s50, s20, a5, a20, l20, h20 = (R["sma50"], R["sma20"], R["ago5"],
                                   R["ago20"], R["low20"], R["high20"])
    with np.errstate(invalid="ignore", divide="ignore"):
        lp = ((nn(s50) & (cN > s50)).astype(np.int8)
              + (nn(s20) & (cN > s20)).astype(np.int8)
              + (nn(a20) & (cN > a20)).astype(np.int8)
              + (nn(a5) & nn(a20) & (cN / a5 - 1 < 0) & (cN / a20 - 1 > 0)).astype(np.int8)
              + (nn(l20) & (lN <= l20 * 1.015)).astype(np.int8))
        sp = ((nn(s50) & (cN < s50)).astype(np.int8)
              + (nn(s20) & (cN < s20)).astype(np.int8)
              + (nn(a20) & (cN < a20)).astype(np.int8)
              + (nn(a5) & nn(a20) & (cN / a5 - 1 > 0) & (cN / a20 - 1 < 0)).astype(np.int8)
              + (nn(h20) & (hN >= h20 * 0.985)).astype(np.int8))
    return lp, sp


def resolve_tier(ls, ss, ml, живо=True):
    """Векторно огледало на lb._resolve + lb._tier."""
    if живо:
        assert lb.ПОСОКА_ОТ_ЦЕНАТА, "ръчката ПОСОКА_ОТ_ЦЕНАТА е изключена в живия бот"
        _lp = ls - ml
        _sp = ss - (3 - ml)
        дълъг = np.where(_lp != _sp, _lp > _sp, ml >= 2)
        d = np.where(дълъг, 1, -1).astype(np.int8)
        score = np.where(дълъг, ls, ss).astype(np.int16)
    else:
        d = np.where(ls > ss, 1, np.where(ss > ls, -1, 0)).astype(np.int8)
        score = np.where(ls > ss, ls, np.where(ss > ls, ss, np.maximum(ls, ss))).astype(np.int16)
    m3 = np.where(d == 1, ml == 3, ml == 0)
    if живо:
        assert lb.ПРЕМИУМ_ПО_ТОЧКИ and lb.ПРЕМИУМ_ТОЧКИ == 7
        t = np.where(score >= lb.ПРЕМИУМ_ТОЧКИ, 3,
                     np.where(score >= 6, 2, np.where(score >= 4, 1, 0)))
    else:
        t = np.where(m3, 3, np.where(score >= 6, 2, np.where(score >= 4, 1, 0)))
    t = np.where(d == 0, 0, t).astype(np.int8)
    return d, score, t


СВОИ_КЛЮЧОВЕ = {
    "ОБЩИ": (),
    "СВОИ": ("sma50", "sma20", "ago5", "ago20", "low20", "high20"),
    # 🔧 ЛЕКЪТ: рамката смята СРЕДНИТЕ си от себе си, но «до 20-барния край»
    # остава ДНЕВЕН въпрос. Допускът в `_scores` е ОТНОСИТЕЛЕН (1.5% / 1.5%) и
    # е избран за ДНЕВНИ барове, където 20-дневният диапазон е 3-8% от цената.
    # Върху 20 МИНУТИ диапазонът е стотни от процента → тестът пали ВИНАГИ и
    # от ДВЕТЕ страни, тоест дава +1 на ls И на ss без да носи информация.
    "СМЕС": ("sma50", "sma20", "ago5", "ago20"),
}


def дъска(Z, свои, живо=True):
    """-> (dir, score, tier, best_frame) на всеки чекпойнт + отчетите по рамка."""
    ml = Z["ml"].astype(np.int16)
    n = len(ml)
    D = np.zeros((7, n), np.int8)
    S = np.zeros((7, n), np.int16)
    T = np.zeros((7, n), np.int8)
    Rd = {k: Z["дневна_" + k] for k in ("sma50", "sma20", "ago5", "ago20", "low20", "high20")}
    for fi, име in enumerate(ИМЕНА):
        if име == "1ден":
            ls = Z["1ден_ls"].astype(np.int16)
            ss = Z["1ден_ss"].astype(np.int16)
        else:
            cN, hN, lN = Z[име + "_cN"], Z[име + "_hN"], Z[име + "_lN"]
            Rs = {k: Z[име + "_" + k] for k in Rd}
            ок = Z[име + "_свои_ок"]
            свои_кл = СВОИ_КЛЮЧОВЕ[свои] if isinstance(свои, str) else (
                СВОИ_КЛЮЧОВЕ["СВОИ"] if свои else ())
            R = {k: (np.where(ок, Rs[k], Rd[k]) if k in свои_кл else Rd[k]) for k in Rd}
            lp, sp = tochki(cN, hN, lN, R)
            ls = (ml + lp).astype(np.int16)
            ss = ((3 - ml) + sp).astype(np.int16)
        d, sc, t = resolve_tier(ls, ss, ml, живо=живо)
        D[fi], S[fi], T[fi] = d, sc, t
    rank = T.astype(np.int32)
    ключ = rank * 1000 + S.astype(np.int32) * 10 + np.arange(7, dtype=np.int32)[:, None]
    ключ = np.where(T > 0, ключ, -1)                  # weak/wait не участва
    има = (T > 0).any(axis=0)
    best = np.argmax(ключ, axis=0)
    bd = D[best, np.arange(len(ml))]
    bs = S[best, np.arange(len(ml))]
    bt = T[best, np.arange(len(ml))]
    bd = np.where(има, bd, 0).astype(np.int8)
    bt = np.where(има, bt, 0).astype(np.int8)
    bs = np.where(има, bs, 0).astype(np.int16)
    best = np.where(има, best, -1).astype(np.int8)
    return D, S, T, bd, bs, bt, best


def kluchove(D, T):
    """live_bot ред 7590: ключ от РАЗЛИЧНИТЕ отчети (посока:клас), сортирани."""
    n = D.shape[1]
    код = np.where(T > 0, (D + 1) * 4 + T, 0).astype(np.int8)     # 0 = не участва
    маска = np.zeros(n, np.int32)
    for v in np.unique(код[код > 0]):
        маска |= ((код == v).any(axis=0).astype(np.int32) << int(v))
    return маска


def antispam(act, key, dname, tier, tsmin, cool=COOL_MIN, flip=COOL_FLIP):
    last_key = -1
    last_dir = ""
    last_tier = 0
    last_ts = None
    picked = []
    for i in range(len(act)):
        if not act[i]:
            last_key = -1
            continue
        k = int(key[i])
        dr = dname[i]
        tr = int(tier[i])
        mins = None if last_ts is None else (tsmin[i] - last_ts)
        tier_up = (tr > last_tier) and (dr == last_dir)
        cool_ok = (mins is None or mins >= cool
                   or (dr != last_dir and mins >= flip) or tier_up)
        if (k != last_key or tier_up) and cool_ok:
            picked.append(i)
            last_key, last_dir, last_tier, last_ts = k, dr, tr, tsmin[i]
    return np.array(picked, np.int64)


def main():
    Z = dict(np.load(TUK / "r1_ramki.npz", allow_pickle=False))
    G = pl.read_columns(KONV / "reshetka.parquet")
    G.pop("__meta__", None)
    tsmin = G["ts"] // 60_000_000
    ok_hist = np.asarray(G["ok_hist"])
    fill_ok = np.asarray(G["fill_ok"])
    n = len(tsmin)
    лог("чекпойнти %s" % format(n, ","))

    рез = {}
    for етикет, свои in (("ОБЩИ", "ОБЩИ"), ("СВОИ", "СВОИ"), ("СМЕС", "СМЕС")):
        D, S, T, bd, bs, bt, best = дъска(Z, свои, живо=True)
        key = kluchove(D, T)
        act = ok_hist & (bt > 0) & (bd != 0)
        dname = np.where(bd == 1, "long", "short")
        picked = antispam(act, key, dname, bt, tsmin)
        pf = picked[fill_ok[picked]]
        рез[етикет] = dict(D=D, S=S, T=T, bd=bd, bs=bs, bt=bt, best=best,
                           act=act, picked=picked, pf=pf)
        # дял шорт по рамка (както бележката в live_bot)
        шорт = [(D[fi] == -1)[ok_hist].mean() * 100 for fi in range(7)]
        лог("%s · actionable %s · карти %s · изпълними %s"
            % (етикет, format(int(act.sum()), ","), format(len(picked), ","),
               format(len(pf), ",")))
        лог("   дял ШОРТ по рамка: " + " · ".join(
            "%s %.1f%%" % (ИМЕНА[i], шорт[i]) for i in range(7)))
        различни = np.array([len(np.unique(np.where(T[:, i] > 0,
                                                    (D[:, i] + 1) * 4 + T[:, i], 0)))
                             for i in range(0, n, 5000)])
        лог("   различни отчета на дъската (проба 1/5000): средно %.2f" % различни.mean())

    A, Bv = рез["ОБЩИ"], рез["СВОИ"]
    смяна_посока = int((A["bd"] != Bv["bd"])[ok_hist].sum())
    смяна_клас = int((A["bt"] != Bv["bt"])[ok_hist].sum())
    смяна_рамка = int((A["best"] != Bv["best"])[ok_hist].sum())
    лог("ЧЕКПОЙНТИ (ok_hist=%s): посоката се мени %s (%.1f%%) · класът %s (%.1f%%) · рамката-победител %s (%.1f%%)"
        % (format(int(ok_hist.sum()), ","), format(смяна_посока, ","),
           100.0 * смяна_посока / ok_hist.sum(), format(смяна_клас, ","),
           100.0 * смяна_клас / ok_hist.sum(), format(смяна_рамка, ","),
           100.0 * смяна_рамка / ok_hist.sum()))

    out = {}
    for етикет in ("ОБЩИ", "СВОИ", "СМЕС"):
        r = рез[етикет]
        pf = r["pf"]
        out[етикет + "_i"] = pf
        out[етикет + "_dir"] = r["bd"][pf]
        out[етикет + "_tier"] = r["bt"][pf]
        out[етикет + "_score"] = r["bs"][pf]
        out[етикет + "_best"] = r["best"][pf]
        out[етикет + "_bar"] = np.asarray(G["bar_index"])[pf]
        out[етикет + "_px"] = np.where(r["bd"][pf] == 1,
                                       np.asarray(G["px_long"])[pf],
                                       np.asarray(G["px_short"])[pf])
        out[етикет + "_dord"] = np.asarray(G["dord_entry"])[pf]
        out[етикет + "_ts"] = tsmin[pf]
        out[етикет + "_stl"] = np.asarray(G["streak_long"])[pf]
        out[етикет + "_sts"] = np.asarray(G["streak_short"])[pf]
        out[етикет + "_dd20"] = np.asarray(G["dd20"])[pf]
        out[етикет + "_ush"] = np.asarray(G["us_shield"])[pf]
        out[етикет + "_bd_all"] = r["bd"]
        out[етикет + "_bt_all"] = r["bt"]
        out[етикет + "_best_all"] = r["best"]
        out[етикет + "_act_all"] = r["act"]
    np.savez_compressed(TUK / "r2_vhodove.npz", **out)
    лог("записано r2_vhodove.npz")

    for етикет in ("ОБЩИ", "СВОИ", "СМЕС"):
        d = out[етикет + "_dir"]
        t = out[етикет + "_tier"]
        b = out[етикет + "_best"]
        лог("%s ВХОДОВЕ n=%d · лонг %d · шорт %d" % (етикет, len(d), int((d == 1).sum()),
                                                     int((d == -1).sum())))
        лог("   класове: " + " · ".join("%s %d" % (TIER_NAME[k], int((t == k).sum()))
                                        for k in (1, 2, 3)))
        лог("   рамка-победител: " + " · ".join(
            "%s %d" % (ИМЕНА[f], int((b == f).sum())) for f in range(7)))


if __name__ == "__main__":
    main()
