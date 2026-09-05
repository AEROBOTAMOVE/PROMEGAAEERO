# -*- coding: utf-8 -*-
"""k4_zvena.py — ЦЕНАТА НА ВСЯКА СПИРАЧКА.

Т0 · какво остава НАКРАЯ, срещу базата.
Т2 · за всяко звено: средното на ПУСНАТИТЕ срещу СПРЕНИТЕ, СРЕЩУ БАЗАТА,
     сдвоено по ден. Звено, чиито спрени са по-добри, работи наопаки.
Т2б· ПЛАЦЕБО за единствената доказана находка: случаен «гейт», който пуска
     точно толкова карти — колко от 500 разбърквания бият истинския?
Т4 · махаме звено X → колко пари се менят, сдвоено ПО ДЕН, с интервал.
Т6 · припокриване: звената съдят ЕДНИ И СЪЩИ чекпойнти — колко съвпадат.

СВЕРКИ ПРЕДИ ЧИСЛАТА:
  С4 · базата по ден срещу базата вход-по-вход (mer_mnozhitelite/slepi_15.npy).
  С5 · парите на живата настройка по два начина (по сделки и по дни).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
sys.path.insert(0, str(TUK))
sys.path.insert(0, str(IZM / "mer_mnozhitelite"))
import konv                                                          # noqa: E402
import pq_lite as pl                                                 # noqa: E402
import dvig                                                          # noqa: E402

SCRATCH = Path(r"C:\Users\User\AppData\Local\Temp\claude"
               r"\C--Users-User-Downloads-----"
               r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad")
REPS = 4000
SEED = 777
ПЛАЦЕБА = 500
T0 = time.time()


def лог(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)


class Бут:
    """ЕДИН набор преизбрани търговски дни за ВСИЧКИ сравнения (сдвояването се
    пази само така). Блок = един търговски ден, по ВХОДА."""

    def __init__(self, nd, reps=REPS, seed=SEED):
        rng = np.random.default_rng(seed)
        self.nd = nd
        self.iz = rng.integers(0, nd, size=(reps, nd), dtype=np.int32)
        self.reps = reps

    def ср_разпр(self, S, C):
        return S[self.iz].sum(1) / np.maximum(C[self.iz].sum(1), 1e-12)

    def средно(self, S, C):
        b = self.ср_разпр(S, C)
        tot = C.sum()
        return ((S.sum() / tot) if tot else np.nan,
                np.nanpercentile(b, 2.5), np.nanpercentile(b, 97.5), int(tot))

    def сума(self, S, дел=1.0):
        b = S[self.iz].sum(1) / дел
        return S.sum() / дел, np.percentile(b, 2.5), np.percentile(b, 97.5)


def побн(v, day, nd):
    ok = np.isfinite(v)
    S = np.bincount(day[ok], weights=v[ok], minlength=nd)
    C = np.bincount(day[ok], minlength=nd).astype(float)
    return S, C


def зв(lo, hi):
    if not np.isfinite(lo) or not np.isfinite(hi):
        return "—"
    return "ДОКАЗАНО+" if lo > 0 else ("ДОКАЗАНО−" if hi < 0 else "недоказано")


def main():
    G, D, B = konv.данни()
    stats = json.load(open(konv.REPO / "backtest_stats.json", encoding="utf-8"))
    гейт = konv.Гейт(stats)
    Z = np.load(TUK / "baza_po_den.npz")
    BL, BS = Z["long"], Z["short"]
    nd = len(BL)
    n = len(D["dir"])
    day = np.where(D["dord_entry"] >= 0, D["dord_entry"], 0).astype(np.int64)
    посока = D["dir"]
    base = np.where(посока == 1, BL[day], np.where(посока == -1, BS[day], np.nan))
    base = np.where(D["dord_entry"] >= 0, base, np.nan)
    net = D["net"]
    прев = net - base

    # ---------------------------------------------------------------- С4
    E = pl.read_columns(SCRATCH / "geom_entries.parquet", ["bar_index", "direction"])
    sl = np.load(IZM / "mer_mnozhitelite" / "slepi_15.npy")
    dirs = np.array([x.decode() if isinstance(x, bytes) else x for x in E["direction"]])
    ред = {int(b): k for k, b in enumerate(E["bar_index"])}
    маска = np.array([int(b) in ред for b in D["bar_index"]]) & D["fill_ok"]
    idx = np.flatnonzero(маска)
    assert len(idx) == len(E["bar_index"])
    idx = idx[np.argsort([ред[int(D["bar_index"][i])] for i in idx])]
    ml = dirs == "long"
    b6 = base[idx]
    лог("С4 · база ВХОД ПО ВХОД : лонг %+.3f · шорт %+.3f · всичко %+.3f"
        % (np.nanmean(sl[:, ml]), np.nanmean(sl[:, ~ml]), np.nanmean(sl)))
    лог("С4 · база ПО ДЕН       : лонг %+.3f · шорт %+.3f · всичко %+.3f"
        % (np.nanmean(b6[ml]), np.nanmean(b6[~ml]), np.nanmean(b6)))
    d1 = abs(np.nanmean(sl[:, ml]) - np.nanmean(b6[ml]))
    d2 = abs(np.nanmean(sl[:, ~ml]) - np.nanmean(b6[~ml]))
    лог("С4 · разлика лонг %.3f$ · шорт %.3f$ — две РАЗЛИЧНИ тегления от същия ден"
        % (d1, d2))
    assert d1 < 0.35 and d2 < 0.35

    # ---------------------------------------------------------------- живата
    П = {k: np.zeros(n, dtype=bool) for k in
         ("стигнал", "антиспам", "US-щит", "пазач", "насрещна", "заглушена",
          "гейт", "таван")}
    сд, ф, карти, убит = konv.бягай(D, konv.ЖИВА, гейт, B, записвай=True, присъди=П)
    лог("живата: сделки %d · карти %d" % (len(сд), ф["КАРТА"]))
    бут = Бут(nd)
    години = nd / 252.0

    def пари_по_ден(сделки):
        M = np.zeros(nd)
        for t in сделки:
            M[t["den"]] += t["w"] * t["net"]
        return M

    M0 = пари_по_ден(сд)
    s1 = sum(t["w"] * t["net"] for t in сд)
    лог("С5 · пари по сделки %.4f · по дни %.4f · разлика %.2e"
        % (s1, M0.sum(), abs(s1 - M0.sum())))
    assert abs(s1 - M0.sum()) < 1e-6

    # ================================================================ Т0
    ii = np.array([t["i"] for t in сд])
    print()
    print("Т0 · КАКВО ОСТАВА НАКРАЯ  (1917 сделки, $/унция на 1 унция; ×100 за лот)")
    print("%-34s %8s %10s %10s %-24s %s"
          % ("мярка", "n", "стойност", "база", "95% интервал", "присъда"))
    for име, v, msk in (("нето на сделката", net[ii], None),
                        ("нето МИНУС базата", прев[ii], None),
                        ("· само ЛОНГ", прев[ii], посока[ii] == 1),
                        ("· само ШОРТ", прев[ii], посока[ii] == -1)):
        vv = v if msk is None else v[msk]
        dd = day[ii] if msk is None else day[ii][msk]
        S = np.bincount(dd[np.isfinite(vv)], weights=vv[np.isfinite(vv)], minlength=nd)
        C = np.bincount(dd[np.isfinite(vv)], minlength=nd).astype(float)
        m, lo, hi, nn = бут.средно(S, C)
        bb = base[ii] if msk is None else base[ii][msk]
        print("%-34s %8s %+10.3f %+10.3f [%+9.3f .. %+9.3f]  %s"
              % (име, format(nn, ","), m, np.nanmean(bb), lo, hi,
                 зв(lo, hi) if "МИНУС" in име or "само" in име else ""))

    # ================================================================ Т2
    РЕД = [("дъска · ПОСОКА", "посока"), ("дъска · СТЕПЕН>weak", "степен"),
           ("АНТИ-СПАМ", "антиспам"), ("US-щит", "US-щит"), ("СТОП-ПАЗАЧ", "пазач"),
           ("насрещна сделка", "насрещна"), ("заглушена «НЕ»", "заглушена"),
           ("ГЕЙТ", "гейт"), ("ТАВАН", "таван"), ("дупка в лентата", "изпълним")]
    print()
    print("Т2 · ПУСНАТИ СРЕЩУ СПРЕНИ · всяко число е НЕТО МИНУС БАЗАТА")
    print("     (същия ден, същата посока, 15 случайни момента; блоков бутстрап "
          "по ден, %d повторения)" % REPS)
    print("%-22s %9s %9s %9s %9s %10s %-22s %-11s" %
          ("звено", "пуснати", "пуснати$", "спрени", "спрени$", "П−С $",
           "95% интервал на П−С", "присъда"))
    for име, k in РЕД:
        p = konv.ЕТ[k]
        стиг = убит >= p
        пус = стиг & (убит > p)
        спр = стиг & (убит == p)
        Sp, Cp = побн(np.where(пус, прев, np.nan), day, nd)
        Ss, Cs = побн(np.where(спр, прев, np.nan), day, nd)
        mp, _, _, np_ = бут.средно(Sp, Cp)
        ms, _, _, ns = бут.средно(Ss, Cs)
        if ns == 0:
            print("%-22s %9s %+9.3f %9s %9s %10s %-22s %-11s"
                  % (име, format(np_, ","), mp, "0", "—", "—", "—", "НЕ РЕЖЕ НИЩО"))
            continue
        d = бут.ср_разпр(Sp, Cp) - бут.ср_разпр(Ss, Cs)
        lo, hi = np.nanpercentile(d, 2.5), np.nanpercentile(d, 97.5)
        print("%-22s %9s %+9.3f %9s %+9.3f %+10.3f [%+9.3f .. %+9.3f]  %-11s"
              % (име, format(np_, ","), mp, format(ns, ","), ms, mp - ms, lo, hi,
                 зв(lo, hi)))
    print("     «П−С»>0 → звеното реже ПО-ЛОШИТЕ (работи както трябва).")
    print("     «П−С»<0 → спрените са били ПО-ДОБРИ — звеното реже наопаки.")
    print("     ПРОБВАНИ СА 10 ЗВЕНА · при 10 проверки едно «доказано» на 5%% се пада "
          "случайно в 40%% от световете → гледай ПЛАЦЕБОТО отдолу, не звездата.")

    # ================================================================ Т2б
    карти_i = np.array([c[0] for c in карти])
    гейт_ок = np.array([c[3] for c in карти])
    v = прев[карти_i]
    dc = day[карти_i]
    ok = np.isfinite(v)
    v, dc, гейт_ок = v[ok], dc[ok], гейт_ок[ok]
    npass = int(гейт_ок.sum())
    ист = v[гейт_ок].mean() - v[~гейт_ок].mean()
    rng = np.random.default_rng(20260902)
    бият = 0
    for _ in range(ПЛАЦЕБА):
        m = np.zeros(len(v), dtype=bool)
        m[rng.choice(len(v), npass, replace=False)] = True
        if (v[m].mean() - v[~m].mean()) >= ист:
            бият += 1
    print()
    print("Т2б · ПЛАЦЕБО за ГЕЙТА: случаен «гейт», който пуска същите %s от %s карти"
          % (format(npass, ","), format(len(v), ",")))
    print("      истинският дава П−С = %+.3f$ · %d от %d разбърквания го бият (%.1f%%)"
          % (ист, бият, ПЛАЦЕБА, 100.0 * бият / ПЛАЦЕБА))

    # ================================================================ Т4
    ВАРИАНТИ = [
        ("степен>weak", dict(tier_filter=False)),
        ("АНТИ-СПАМ (целият)", dict(antispam=False)),
        ("· само повторното предлагане", dict(reoffer=False)),
        ("US-щит", dict(us_shield=False)),
        ("СТОП-ПАЗАЧ (жив: ИЗКЛ)", dict(guard=False)),
        ("СТОП-ПАЗАЧ ВКЛючен (обратно)", dict(guard=True)),
        ("насрещна сделка", dict(opposite=False)),
        ("премиум флип", dict(flip=False)),
        ("заглушаване на «НЕ»", dict(mute=False)),
        ("ГЕЙТ", dict(gate=False)),
        ("ТАВАН (12 → без)", dict(cap=10 ** 9)),
        ("РАЗМЕР (4-те множителя)", dict(size=False)),
    ]
    print()
    print("Т4 · МАХАМЕ ЗВЕНОТО — какво става с ПАРИТЕ ($/унция/година; ×100 за лот)")
    print("     сдвоено ПО ТЪРГОВСКИ ДЕН срещу живата настройка, %d повторения" % REPS)
    print("%-30s %7s %8s %9s %9s %-22s %-11s %-30s"
          % ("махнато звено", "сделки", "карти", "пари/год", "Δ/год",
             "95% интервал на Δ/год", "присъда", "Δ на СДЕЛКА над базата + инт."))
    ж_год = M0.sum() / години
    S0, C0 = побн(np.where(np.isin(np.arange(n), ii), прев, np.nan), day, nd)
    print("%-30s %7s %8s %9.1f %9s %-22s %-11s %-30s"
          % ("(нищо — ЖИВАТА)", format(len(сд), ","), format(ф["КАРТА"], ","),
             ж_год, "—", "—", "—", "—"))
    OFF = {}
    for име, промени in ВАРИАНТИ:
        cfg = dict(konv.ЖИВА)
        cfg.update(промени)
        П2 = {k: np.zeros(n, dtype=bool) for k in П}
        сд2, ф2, карти2, убит2 = konv.бягай(D, cfg, гейт, B, записвай=True, присъди=П2)
        M = пари_по_ден(сд2)
        Δ = M - M0
        _, lo, hi = бут.сума(Δ, дел=години)
        ii2 = np.array([t["i"] for t in сд2])
        m2 = np.zeros(n, dtype=bool); m2[ii2] = True
        S2, C2 = побн(np.where(m2, прев, np.nan), day, nd)
        dd = бут.ср_разпр(S2, C2) - бут.ср_разпр(S0, C0)
        дс = (S2.sum() / max(C2.sum(), 1)) - (S0.sum() / max(C0.sum(), 1))
        dlo, dhi = np.nanpercentile(dd, 2.5), np.nanpercentile(dd, 97.5)
        print("%-30s %7s %8s %9.1f %+9.1f [%+9.1f .. %+9.1f]  %-11s %+7.3f [%+6.3f..%+6.3f] %s"
              % (име, format(len(сд2), ","), format(ф2["КАРТА"], ","),
                 M.sum() / години, Δ.sum() / години, lo, hi, зв(lo, hi),
                 дс, dlo, dhi, зв(dlo, dhi)))
        OFF[име] = (убит2, len(сд2), ф2["КАРТА"])
    print("     Δ>0 → БЕЗ звеното парите РАСТАТ, тоест спирачката е ПЛАТЕНА (вреди).")
    print("     Δ<0 → звеното НОСИ пари.  «недоказано» = нулата е в интервала.")
    print("     «Δ/сделка» е разликата в средните пари на сделка — казва дали "
          "печалбата идва от РЪБ или само от БРОЙ.")

    # ================================================================ Т3
    print()
    print("Т3 · ЧЕСТОТА на живата настройка (22.6 години)")
    дни_карти = len({int(day[c[0]]) for c in карти})
    дни_сделки = len({t["den"] for t in сд})
    print("  карти       %8s = %7.1f/година   ·  карти-ДНИ   %5s = %5.1f дни/год (от 252)"
          % (format(ф["КАРТА"], ","), ф["КАРТА"] / години,
             format(дни_карти, ","), дни_карти / години))
    print("  сделки      %8s = %7.1f/година   ·  сделки-ДНИ  %5s = %5.1f дни/год"
          % (format(len(сд), ","), len(сд) / години,
             format(дни_сделки, ","), дни_сделки / години))
    print("  пари        %8.0f$/унция общо = %.1f$/год = %.0f$/год на 1 стандартен лот"
          % (M0.sum(), ж_год, ж_год * 100))

    # ================================================================ Т6
    ЗВ = ["антиспам", "US-щит", "пазач", "насрещна", "заглушена", "гейт", "таван"]
    стиг = П["стигнал"]
    N = int(стиг.sum())
    print()
    print("Т6 · ПРИПОКРИВАНЕ · всички звена съдят ЕДНИТЕ И СЪЩИ %s чекпойнта"
          % format(N, ","))
    print("     (присъдите се смятат ВСИЧКИ, без спиране — иначе второто звено "
          "никога не бива питано)")
    print("%-12s %9s   %s" % ("звено", "спира", "  ".join("%9s" % z for z in ЗВ)))
    for a in ЗВ:
        A = П[a] & стиг
        ред_ = []
        for b in ЗВ:
            Bb = П[b] & стиг
            ред_.append("%8.1f%%" % (100.0 * (A & Bb).sum() / max(A.sum(), 1)))
        print("%-12s %9s   %s" % (a, format(int(A.sum()), ","), "   ".join(ред_)))
    print("     ЧЕТЕ СЕ: «от спрените от РЕДА, колко % ги спира и КОЛОНАТА».")
    print("     100%% в клетка (ред≠колона) значи, че редът е ИЗЛИШЕН — колоната "
          "го върши цялата.")

    # ================================================================ Т5
    print()
    print("Т5 · ЗАЩО «СТЕПЕН>weak» НЕ МОЖЕ ДА СПРЕ НИЩО (не късмет — аритметика)")
    има = D["ok_hist"] & (посока != 0)
    победител = np.maximum(D["ls"], D["ss"])[има]
    сбор = (D["ls"] + D["ss"])[има]
    print("     ls+ss = 3 + (ценови точки за лонг) + (ценови точки за шорт);")
    print("     трите средни (sma50, sma20, отпреди 20д) дават точка на ТОЧНО една")
    print("     страна → ls+ss ≥ 6 винаги; а щом ls≠ss, победителят е ≥ 4 = «medium».")
    print("     ИЗМЕРЕНО на %s чекпойнта с посока: min(ls+ss) = %d · min(победител) = %d"
          % (format(int(има.sum()), ","), int(сбор.min()), int(победител.min())))
    print("     степен==0 при налична посока: %d случая → прагът е МЪРТЪВ КОД."
          % int((D["tier"][има] <= 0).sum()))

    np.save(TUK / "ubit_zhiva.npy", убит)
    np.savez_compressed(TUK / "prisadi_zhiva.npz", **П)
    with open(TUK / "sdelki_zhiva.json", "w", encoding="utf-8") as f:
        json.dump(сд, f)
    лог("записано")


if __name__ == "__main__":
    main()
