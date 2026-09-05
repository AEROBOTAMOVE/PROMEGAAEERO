# -*- coding: utf-8 -*-
"""r2b_sverka.py - ДВЕ сверки, без които нищо оттук не се брои.

С1 · моята машинария, свита до «една рамка 1ден + СТАРИЯ _resolve/_tier +
     ключ = посока:клас на победителя», трябва да даде ТОЧНО доставените
     6846 входа (geom_entries.parquet).
С2 · КОЛКО ПЪТИ ПАЛИ всеки от петте ценови теста, по рамка, в двата режима -
     за да се види ОТКЪДЕ идват точките, а не само че са повече.
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
import r2_vhodove as r2                                              # noqa: E402

T0 = time.time()
ENTRIES = Path(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----"
               r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad\geom_entries.parquet")


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


def main():
    Z = dict(np.load(TUK / "r1_ramki.npz"))
    G = pl.read_columns(KONV / "reshetka.parquet")
    G.pop("__meta__", None)
    tsmin = G["ts"] // 60_000_000
    ok_hist = np.asarray(G["ok_hist"])
    fill_ok = np.asarray(G["fill_ok"])
    ml = Z["ml"].astype(np.int16)

    # ---------------- С1 -------------------------------------------------
    ls = Z["1ден_ls"].astype(np.int16)
    ss = Z["1ден_ss"].astype(np.int16)
    d, sc, t = r2.resolve_tier(ls, ss, ml, живо=False)
    нес = int((d != np.asarray(G["dir"])).sum()) + int((t != np.asarray(G["tier"])).sum())
    лог("С1а · старият _resolve/_tier срещу решетката: %d разминавания" % нес)
    act = ok_hist & (d != 0) & (t > 0)
    key = ((d + 1) * 4 + t).astype(np.int32)          # само победителя = 1ден
    dname = np.where(d == 1, "long", "short")
    picked = r2.antispam(act, key, dname, t, tsmin)
    picked = picked[fill_ok[picked]]
    лог("С1б · моите входове: %d" % len(picked))
    E = pl.read_columns(ENTRIES)
    E.pop("__meta__", None)
    лог("С1б · доставените geom_entries: %d" % len(E["bar_index"]))
    assert len(picked) == len(E["bar_index"]), "различен БРОЙ входове"
    р1 = int((np.asarray(G["bar_index"])[picked] != np.asarray(E["bar_index"])).sum())
    мойd = np.where(d[picked] == 1, "long", "short")
    р2 = int((мойd != np.asarray(E["direction"]).astype(str)).sum())
    р3 = int((sc[picked] != np.asarray(E["score"])).sum())
    лог("С1в · bar_index %d · direction %d · score %d разминавания" % (р1, р2, р3))
    assert р1 == 0 and р2 == 0 and р3 == 0
    лог("С1 ✅ машинарията възпроизвежда доставените 6846 входа ТОЧНО")

    # ---------------- С2 -------------------------------------------------
    Rd = {k: Z["дневна_" + k] for k in ("sma50", "sma20", "ago5", "ago20", "low20", "high20")}
    лог("С2 · дял на ПАЛЕНЕ на всеки тест (само ok_hist), лонг|шорт")
    print("   %-6s %-6s %-12s %-12s %-12s %-12s %-12s" %
          ("рамка", "режим", "cN>sma50", "cN>sma20", "cN>ago20", "5/20 обрат", "край20"),
          flush=True)
    for име in r2.ИМЕНА:
        if име == "1ден":
            continue
        cN, hN, lN = Z[име + "_cN"], Z[име + "_hN"], Z[име + "_lN"]
        ок = Z[име + "_свои_ок"]
        for етикет, R in (("ОБЩИ", Rd),
                          ("СВОИ", {k: np.where(ок, Z[име + "_" + k], Rd[k]) for k in Rd})):
            def nn(a):
                return ~np.isnan(a)
            with np.errstate(invalid="ignore", divide="ignore"):
                t1 = nn(R["sma50"]) & (cN > R["sma50"])
                t2 = nn(R["sma20"]) & (cN > R["sma20"])
                t3 = nn(R["ago20"]) & (cN > R["ago20"])
                t4 = (nn(R["ago5"]) & nn(R["ago20"]) & (cN / R["ago5"] - 1 < 0)
                      & (cN / R["ago20"] - 1 > 0))
                t5 = nn(R["low20"]) & (lN <= R["low20"] * 1.015)
                s1 = nn(R["sma50"]) & (cN < R["sma50"])
                s2 = nn(R["sma20"]) & (cN < R["sma20"])
                s3 = nn(R["ago20"]) & (cN < R["ago20"])
                s4 = (nn(R["ago5"]) & nn(R["ago20"]) & (cN / R["ago5"] - 1 > 0)
                      & (cN / R["ago20"] - 1 < 0))
                s5 = nn(R["high20"]) & (hN >= R["high20"] * 0.985)
            m = ok_hist
            print("   %-6s %-6s %5.1f|%-5.1f %5.1f|%-5.1f %5.1f|%-5.1f %5.1f|%-5.1f %5.1f|%-5.1f"
                  % (име, етикет, 100 * t1[m].mean(), 100 * s1[m].mean(),
                     100 * t2[m].mean(), 100 * s2[m].mean(),
                     100 * t3[m].mean(), 100 * s3[m].mean(),
                     100 * t4[m].mean(), 100 * s4[m].mean(),
                     100 * t5[m].mean(), 100 * s5[m].mean()), flush=True)


if __name__ == "__main__":
    main()
