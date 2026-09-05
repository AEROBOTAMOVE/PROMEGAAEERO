# -*- coding: utf-8 -*-
"""s4 · ПОДРЕДЕНО ЛИ Е МЕРЕНОТО В ПОСОКАТА, КОЯТО ТЕГЛОТО ПРЕДПОЛАГА?

ZONE_W падна на плоско на 01.09, защото преизмерването ОБЪРНА реда (C излезе
най-добра, а получаваше най-малко). Тук същият въпрос се задава на другите три.

Всяко тегло е ТВЪРДЕНИЕ: «тази половина печели по-малко, затова ѝ давам по-малко».
Проверява се ПРЯКО: средното нето на всяка кофа, с интервал (блоков бутстрап по
ден), и РАЗЛИКАТА между кофите — сдвоена по ден.

Плюс базата: нето МИНУС слепия ден (същия ден, случаен момент, 15 тегления).
Ако разликата между кофите изчезне, след като се извади денят, теглото съди
ДЕНЯ, а не сетъпа.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

TUK = Path(__file__).resolve().parent
sys.path.insert(0, str(TUK))
import tegla                                                         # noqa: E402
from s2_parite import Б2, дв                                         # noqa: E402


def кофи(name, E, net, net_b, dayid, m, групи, тегла):
    """групи: dict име -> булева маска (върху пълния масив). тегла: dict име -> w"""
    print("\n" + "-" * 78)
    print("%s   (n=%d)" % (name, int(m.sum())))
    print("  %-26s %6s %6s  %-34s %-34s"
          % ("кофа (тегло)", "n", "дни", "нето, БЕЗ базата", "нето МИНУС слепия ден"))
    редове = []
    for gname, gm in групи.items():
        mm = m & gm
        if mm.sum() < 30:
            print("  %-26s %6d   — под 30 входа, не се съди" % (gname, int(mm.sum())))
            continue
        b = Б2(dayid[mm])
        a = b.средно(net[mm])
        c = b.средно(net[mm] - net_b[mm])
        print("  %-26s %6d %6d  %-34s %-34s"
              % ("%s (×%.2f)" % (gname, тегла[gname]), int(mm.sum()), b.k, дв(*a), дв(*c)))
        редове.append((gname, тегла[gname], a[0], c[0], mm))
    # сдвоената разлика между двете крайни кофи
    if len(редове) >= 2:
        по_тегло = sorted(редове, key=lambda r: r[1])
        ниско, високо = по_тегло[0], по_тегло[-1]
        mm = m & (ниско[4] | високо[4])
        b = Б2(dayid[mm])
        зн = np.where(високо[4][mm], 1.0, -1.0)

        def разлика(vals):
            v_hi = np.where(зн > 0, vals[mm], np.nan)
            v_lo = np.where(зн < 0, vals[mm], np.nan)
            okh = np.isfinite(v_hi); okl = np.isfinite(v_lo)
            Sh = np.bincount(b.inv[okh], weights=v_hi[okh], minlength=b.k)
            Ch = np.bincount(b.inv[okh], minlength=b.k).astype(float)
            Sl = np.bincount(b.inv[okl], weights=v_lo[okl], minlength=b.k)
            Cl = np.bincount(b.inv[okl], minlength=b.k).astype(float)
            dd = (Sh[b.iz].sum(1) / np.maximum(Ch[b.iz].sum(1), 1e-9)
                  - Sl[b.iz].sum(1) / np.maximum(Cl[b.iz].sum(1), 1e-9))
            return (float(np.nanmean(v_hi) - np.nanmean(v_lo)),
                    float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5)))

        r1 = разлика(net)
        r2 = разлика(net - net_b)
        print("  РАЗЛИКА «%s(×%.2f)» − «%s(×%.2f)»  БЕЗ базата:      %s"
              % (високо[0], високо[1], ниско[0], ниско[1], дв(*r1)))
        print("  РАЗЛИКА «%s(×%.2f)» − «%s(×%.2f)»  МИНУС слепия ден: %s"
              % (високо[0], високо[1], ниско[0], ниско[1], дв(*r2)))
        print("  ПОСОКАТА, която теглото предполага (по-голямо тегло = повече пари):"
              "  БЕЗ базата %s · СЛЕД базата %s"
              % ("ПОТВЪРДЕНА" if r1[0] > 0 else "🔴 ОБЪРНАТА",
                 "ПОТВЪРДЕНА" if r2[0] > 0 else "🔴 ОБЪРНАТА"))


def main():
    E = tegla.данни()
    net = np.load(TUK / "net_6846.npy")
    BL = np.load(TUK / "slepi_15.npy")
    net_b = np.nanmean(BL, axis=0)
    гейт, _ = tegla.гейт_маска(E)
    dayid = tegla.ден_ид(E)
    d = E.direction.values
    под = (E.cN.values < E.sma200.values)
    прев = np.abs(E.ls.values.astype(int) - E.ss.values.astype(int))
    кл = E["клетка"].values
    зона = E["зона"].values

    print("=" * 78)
    print("s4 · ПОДРЕДЕНО ЛИ Е МЕРЕНОТО В ПОСОКАТА НА ТЕГЛОТО")
    print("=" * 78)

    for име_поп, m in (("ВСИЧКИ 6846", np.ones(len(E), bool)),
                       ("ГЕЙТ-ПУСНАТИТЕ", гейт)):
        print("\n" + "=" * 78)
        print(име_поп)
        print("=" * 78)
        кофи("ЗОНА (_zw) · днес ПЛОСКО; мерените бяха A1.00/B0.85/C0.50", E, net, net_b,
             dayid, m,
             {"A": зона == "A", "B": зона == "B", "C": зона == "C"},
             {"A": 1.00, "B": 0.85, "C": 0.50})
        кофи("МАЛЪК (_мw) · mixed/stale получават 0.50", E, net, net_b, dayid, m,
             {"day1/fresh": np.isin(кл, ("day1", "fresh")),
              "mixed/stale": np.isin(кл, ("mixed", "stale"))},
             {"day1/fresh": 1.00, "mixed/stale": 0.50})
        кофи("РЕЖИМ (_рw) · САМО ЛОНГ · под SMA200 получава 0.50", E, net, net_b, dayid,
             m & (d == "long"),
             {"над SMA200": ~под, "под SMA200": под},
             {"над SMA200": 1.00, "под SMA200": 0.50})
        кофи("РЕЖИМ · ШОРТЪТ (теглото НЕ се прилага — проверка дали е трябвало)",
             E, net, net_b, dayid, m & (d == "short"),
             {"над SMA200": ~под, "под SMA200": под},
             {"над SMA200": 1.00, "под SMA200": 0.50})
        кофи("ПРЕВЕС (_пw) · |ls−ss| ≤2 получава 0.50", E, net, net_b, dayid, m,
             {"широк ≥3": прев >= 3, "тесен ≤2": прев <= 2},
             {"широк ≥3": 1.00, "тесен ≤2": 0.50})
        кофи("ПРЕВЕС · само ЛОНГ", E, net, net_b, dayid, m & (d == "long"),
             {"широк ≥3": прев >= 3, "тесен ≤2": прев <= 2},
             {"широк ≥3": 1.00, "тесен ≤2": 0.50})
        кофи("ПРЕВЕС · само ШОРТ", E, net, net_b, dayid, m & (d == "short"),
             {"широк ≥3": прев >= 3, "тесен ≤2": прев <= 2},
             {"широк ≥3": 1.00, "тесен ≤2": 0.50})


if __name__ == "__main__":
    main()
