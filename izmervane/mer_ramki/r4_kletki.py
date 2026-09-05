# -*- coding: utf-8 -*-
"""r4_kletki.py - КЛЕТКИТЕ на гейта, преизмерени под ДВАТА режима на рамките.

Кофата се взима от lb._cell_name върху ЧЕСТНИЯ стрийк (streak_long/short в
решетката, смятани с .shift(1) - само ЗАВЪРШЕНИ дни, както живият `_hist`).
Бутстрапът е БЛОКОВ ПО ДЕН: преизбират се ТЪРГОВСКИ ДНИ (мултиномиални тегла),
5000 реплики, seed 20260905.

СВЕРКА С4: същата процедура върху ДОСТАВЕНИТЕ 6846 входа трябва да върне
числата, които СТОЯТ в backtest_stats.json.fresh (net/n/дни/win).
"""
from __future__ import annotations
import io
import json
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
import dvig                                                          # noqa: E402
import live_bot as lb                                                # noqa: E402
import r3_neta as r3                                                 # noqa: E402

T0 = time.time()
REPS = 5000
SEED = 20260905
КОФИ = ("day1", "fresh", "mixed", "stale")


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


class Boot:
    def __init__(self, dayid, reps=REPS, seed=SEED):
        self.u, self.inv = np.unique(dayid, return_inverse=True)
        self.k = len(self.u)
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(self.k, np.full(self.k, 1.0 / self.k),
                                 size=reps).astype(np.float64).T

    def ci(self, v, inv):
        S = np.bincount(inv, weights=v, minlength=self.k)
        C = np.bincount(inv, minlength=self.k).astype(float)
        num = S @ self.W
        den = C @ self.W
        bm = num / np.maximum(den, 1e-12)
        return S.sum() / C.sum(), np.percentile(bm, 2.5), np.percentile(bm, 97.5)


def кофи(dirs, stl, sts):
    имена = np.empty(len(dirs), dtype=object)
    for i in range(len(dirs)):
        s = int(stl[i] if dirs[i] == 1 else sts[i])
        имена[i] = lb._cell_name(s)
    return имена


def таблица(dirs, cell, net, day, dd20=None, stl=None, sts=None, заглавие=""):
    ok = np.isfinite(net)
    boot = Boot(day[ok])
    _, inv_all = np.unique(day[ok], return_inverse=True)
    карта = {d: {} for d in ("long", "short")}
    лог(заглавие)
    print("   %-6s %-9s %8s %6s %8s %9s %9s %7s  %s"
          % ("посока", "кофа", "n", "дни", "нето$", "lo", "hi", "win%", "присъда"), flush=True)
    for dn, dv in (("long", 1), ("short", -1)):
        for c in КОФИ:
            m = ok & (dirs == dv) & (cell == c)
            if m.sum() == 0:
                continue
            sub = m[ok]
            v = np.where(sub, net[ok], 0.0)
            cnt = sub.astype(float)
            S = np.bincount(inv_all, weights=v, minlength=boot.k)
            C = np.bincount(inv_all, weights=cnt, minlength=boot.k)
            num = S @ boot.W
            den = C @ boot.W
            bm = num / np.maximum(den, 1e-12)
            mean = S.sum() / max(C.sum(), 1e-12)
            lo, hi = np.percentile(bm, 2.5), np.percentile(bm, 97.5)
            дни = int((C > 0).sum())
            win = 100.0 * (net[m] > 0).mean()
            пр = "ДОКАЗАН+" if lo > 0 else ("ДОКАЗАН-" if hi < 0 else "недоказана")
            if дни < 100:
                пр += " (<100 дни)"
            карта[dn][c] = dict(win=round(float(win), 1), net=round(float(mean), 3),
                                n=int(m.sum()), дни=дни,
                                lo=round(float(lo), 3), hi=round(float(hi), 3))
            print("   %-6s %-9s %8d %6d %+8.3f %+9.3f %+9.3f %7.1f  %s"
                  % (dn, c, int(m.sum()), дни, mean, lo, hi, win, пр), flush=True)
    if dd20 is not None:
        s = np.where(dirs == -1, sts, stl)
        m = ok & (dirs == -1) & (s >= 2) & (s <= 3) & np.isfinite(dd20) & (dd20 < lb.NEAR_HIGH_DD20)
        if m.sum():
            sub = m[ok]
            S = np.bincount(inv_all, weights=np.where(sub, net[ok], 0.0), minlength=boot.k)
            C = np.bincount(inv_all, weights=sub.astype(float), minlength=boot.k)
            bm = (S @ boot.W) / np.maximum(C @ boot.W, 1e-12)
            mean = S.sum() / max(C.sum(), 1e-12)
            lo, hi = np.percentile(bm, 2.5), np.percentile(bm, 97.5)
            карта["short"]["near_high"] = dict(win=round(100.0 * float((net[m] > 0).mean()), 1),
                                               net=round(float(mean), 3), n=int(m.sum()),
                                               дни=int((C > 0).sum()),
                                               lo=round(float(lo), 3), hi=round(float(hi), 3))
            print("   %-6s %-9s %8d %6d %+8.3f %+9.3f %+9.3f %7.1f"
                  % ("short", "near_high", int(m.sum()), int((C > 0).sum()), mean, lo, hi,
                     100.0 * (net[m] > 0).mean()), flush=True)
    return карта


def main():
    B = dvig.лента()
    G = pl.read_columns(KONV / "reshetka.parquet")
    G.pop("__meta__", None)

    # ---------------- С4 · доставените 6846 -------------------------------
    import r2_vhodove as r2
    Z = dict(np.load(TUK / "r1_ramki.npz"))
    tsmin = G["ts"] // 60_000_000
    ml = Z["ml"].astype(np.int16)
    d0, sc0, t0 = r2.resolve_tier(Z["1ден_ls"].astype(np.int16),
                                  Z["1ден_ss"].astype(np.int16), ml, живо=False)
    act = np.asarray(G["ok_hist"]) & (d0 != 0) & (t0 > 0)
    key = ((d0 + 1) * 4 + t0).astype(np.int32)
    picked = r2.antispam(act, key, np.where(d0 == 1, "long", "short"), t0, tsmin)
    picked = picked[np.asarray(G["fill_ok"])[picked]]
    assert len(picked) == 6846
    net0, exi0, kind0 = r3.бяг(np.asarray(G["bar_index"])[picked], d0[picked],
                               np.where(d0[picked] == 1, np.asarray(G["px_long"])[picked],
                                        np.asarray(G["px_short"])[picked]), B)
    c0 = кофи(d0[picked], np.asarray(G["streak_long"])[picked],
              np.asarray(G["streak_short"])[picked])
    к0 = таблица(d0[picked], c0, net0, np.asarray(G["dord_entry"])[picked],
                 np.asarray(G["dd20"])[picked], np.asarray(G["streak_long"])[picked],
                 np.asarray(G["streak_short"])[picked],
                 "С4 · ДОСТАВЕНИТЕ 6846 входа, жива геометрия, 21 търг. дни")
    st = json.load(io.open(REPO / "backtest_stats.json", encoding="utf-8"))["fresh"]
    лог("С4 · срещу backtest_stats.json.fresh:")
    зле = 0
    for dn in ("long", "short"):
        for c in КОФИ:
            a = к0[dn].get(c)
            b = st[dn].get(c)
            if not a or not b:
                continue
            ок = (a["n"] == b["n"] and a["дни"] == b["дни"]
                  and abs(a["net"] - b["net"]) <= 0.002 and abs(a["win"] - b["win"]) <= 0.15)
            зле += 0 if ок else 1
            print("   %-6s %-6s мое n=%-5d дни=%-4d нето=%+.3f win=%.1f | файл n=%-5d дни=%-4d нето=%+.3f win=%.1f  %s"
                  % (dn, c, a["n"], a["дни"], a["net"], a["win"],
                     b["n"], b["дни"], b["net"], b["win"], "OK" if ок else "🔴 РАЗМИНАВА"),
                  flush=True)
    лог("С4 · разминавания: %d" % зле)

    # ---------------- ДВАТА РЕЖИМА ----------------------------------------
    E = np.load(TUK / "r2_vhodove.npz")
    N = np.load(TUK / "r3_neta.npz")
    изход = {"С4_доставени": к0}
    for етикет in ("ОБЩИ", "СВОИ", "СМЕС"):
        d = E[етикет + "_dir"]
        c = кофи(d, E[етикет + "_stl"], E[етикет + "_sts"])
        к = таблица(d, c, N[етикет + "_net"], E[етикет + "_dord"],
                    E[етикет + "_dd20"], E[етикет + "_stl"], E[етикет + "_sts"],
                    "КЛЕТКИ · режим %s (n=%s)" % (етикет, format(len(d), ",")))
        изход[етикет] = к
    io.open(TUK / "r4_kletki.json", "w", encoding="utf-8").write(
        json.dumps(изход, ensure_ascii=False, indent=1))
    лог("записано r4_kletki.json")


if __name__ == "__main__":
    main()
