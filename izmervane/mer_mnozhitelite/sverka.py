# -*- coding: utf-8 -*-
"""sverka.py — dvig.една СРЕЩУ gh._one_trade, ред по ред.

Условие: 0 разминавания по net, kind и exit_index върху
  · всичките 6846 реални входа (двете посоки)
  · 8000 слепи входа (случаен момент в същия ден)
преди което и да е число от тази папка да се вярва.

+ С3в · зоната зависи ли ИЗОБЩО от причинния прозорец: разваляме ПОСЛЕДНИТЕ
  50 часови бара ПРЕДИ решението — ако класът не мръдне, мерим константа.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
sys.path.insert(0, str(TUK))
sys.path.insert(0, str(IZM))
sys.path.insert(0, str(REPO))
import geom_harness as gh                                            # noqa: E402
import dvig                                                          # noqa: E402

T0 = time.time()


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


def main():
    E = pd.read_parquet(TUK / "mnozh_6846.parquet")
    B = dvig.лента()

    idxs = E.bar_index.values.astype(np.int64)
    dirs = E.direction.values
    pxs = E.entry_px.values.astype(float)

    # ---------- реалните -------------------------------------------------
    лог("сверка върху %d реални входа ..." % len(idxs))
    лоши = 0
    for p in range(len(idxs)):
        r1 = gh._one_trade(int(idxs[p]), dirs[p], float(pxs[p]), gh.GEOM_SHIPPED, B)
        r2 = dvig.една(int(idxs[p]), dirs[p], float(pxs[p]), dvig.GEOM, B)
        if (r1 is None) != (r2 is None):
            лоши += 1; continue
        if r1 is None:
            continue
        if (abs(r1["net"] - r2["net"]) > 1e-9 or r1["kind"] != r2["kind"]
                or r1["exit_index"] != r2["exit_index"] or r1["n_fills"] != r2["n_fills"]):
            лоши += 1
            if лоши <= 5:
                лог("  РАЗМИНАВАНЕ p=%d %s  gh=%s  моят=%s" % (p, dirs[p], r1, r2))
    лог("реални: разминавания %d от %d" % (лоши, len(idxs)))

    # ---------- слепите --------------------------------------------------
    bidx = dvig.слепи_индекси(idxs, B, ndraw=2, seed=777)
    bi = bidx.reshape(-1)[:8000]
    bd = np.tile(dirs, 2)[:8000]
    лог("сверка върху %d слепи входа ..." % len(bi))
    лоши2 = 0
    for p in range(len(bi)):
        i0 = int(bi[p]); dr = bd[p]
        px = float(B["oa"][i0] if dr == "long" else B["ob"][i0])
        r1 = gh._one_trade(i0, dr, px, gh.GEOM_SHIPPED, B)
        r2 = dvig.една(i0, dr, px, dvig.GEOM, B)
        if (r1 is None) != (r2 is None):
            лоши2 += 1; continue
        if r1 is None:
            continue
        if (abs(r1["net"] - r2["net"]) > 1e-9 or r1["kind"] != r2["kind"]
                or r1["exit_index"] != r2["exit_index"]):
            лоши2 += 1
            if лоши2 <= 5:
                лог("  РАЗМИНАВАНЕ слеп p=%d %s  gh=%s  моят=%s" % (p, dr, r1, r2))
    лог("слепи: разминавания %d от %d" % (лоши2, len(bi)))

    # ---------- сверка и срещу записаните нета в kletki_6846 -------------
    K = Path(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----"
             r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad\kletki\kletki_6846.parquet")
    if K.exists():
        KK = pd.read_parquet(K)
        мои = dvig.мнозина(idxs, dirs, pxs, B)["net"]
        d = np.abs(KK["net"].values - мои)
        лог("срещу kletki_6846.net: макс |Δ| = %.2e   разминавания>1e-9: %d"
            % (np.nanmax(d), int((d > 1e-9).sum())))
        np.save(TUK / "net_6846.npy", мои)
        лог("записано net_6846.npy  средно %.4f$" % np.nanmean(мои))

    assert лоши == 0 and лоши2 == 0, "ДВИГАТЕЛЯТ НЕ СЪВПАДА — нищо оттук не важи"
    print("\nСВЕРКА МИНА: 0 разминавания на %d реални + %d слепи сделки"
          % (len(idxs), len(bi)))


if __name__ == "__main__":
    main()
