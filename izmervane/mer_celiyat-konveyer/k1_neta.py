# -*- coding: utf-8 -*-
"""k1_neta.py — нетото на ВСЕКИ възможен вход (не само на пуснатите).

Без това никое звено не може да бъде съдено: за «спрените» трябва да се знае
какво БИХА донесли. Пресмята се доставената геометрия за всеки чекпойнт с
посока и изпълним бар — 461 291 хипотетични сделки.

Двигателят е izmervane/mer_mnozhitelite/dvig.py, сверен РЕД ПО РЕД срещу
gh._one_trade. Сверката се пуска ОТНОВО тук, на 400 случайни входа от ТАЗИ
решетка (не на чужда извадка), преди да се повярва на който и да е нет.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
sys.path.insert(0, str(IZM / "mer_mnozhitelite"))
sys.path.insert(0, str(IZM))
sys.path.insert(0, str(REPO))
import dvig                                                          # noqa: E402
import geom_harness as gh                                            # noqa: E402

T0 = time.time()
OUT = TUK / "neta.npz"


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


def сверка(G, B, k=400, seed=7):
    """Моят двигател срещу gh._one_trade на входове ОТ ТАЗИ решетка."""
    ок = G.fill_ok.values & (G["dir"].values != 0)
    idx = np.flatnonzero(ок)
    rng = np.random.default_rng(seed)
    proba = rng.choice(idx, size=min(k, len(idx)), replace=False)
    лош = 0
    for p in proba:
        d = "long" if G["dir"].values[p] == 1 else "short"
        px = float(G.px_long.values[p] if d == "long" else G.px_short.values[p])
        i0 = int(G.bar_index.values[p])
        a = dvig.една(i0, d, px, dvig.GEOM, B)
        b = gh._one_trade(i0, d, px, gh.GEOM_SHIPPED, B)
        if (a is None) != (b is None):
            лош += 1; continue
        if a is None:
            continue
        if (abs(a["net"] - b["net"]) > 1e-9 or a["kind"] != b["kind"]
                or a["exit_index"] != b["exit_index"]):
            лош += 1
            if лош <= 3:
                лог("   РАЗМИНАВАНЕ", i0, d, a, b)
    лог("С2 · двигател срещу gh._one_trade на %d входа: %d разминавания" % (len(proba), лош))
    assert лош == 0, "двигателят се разминава с gh._one_trade"


def main():
    G = pd.read_parquet(TUK / "reshetka.parquet")
    B = dvig.лента()
    сверка(G, B)

    ок = G.fill_ok.values & (G["dir"].values != 0) & G.ok_hist.values
    idx = np.flatnonzero(ок)
    лог("сделки за смятане: %s" % format(len(idx), ","))
    dirs = G["dir"].values
    pxl = G.px_long.values
    pxs = G.px_short.values
    bidx = G.bar_index.values

    net = np.full(len(G), np.nan)
    exi = np.full(len(G), -1, dtype=np.int64)
    kind = np.zeros(len(G), dtype=np.int8)      # 0 нищо·1 stop·2 be/stop-after·3 tp3·4 time
    KMAP = {"stop": 1, "tp3": 3, "time": 4}
    t = time.time()
    for c, p in enumerate(idx):
        d = "long" if dirs[p] == 1 else "short"
        r = dvig.една(int(bidx[p]), d, float(pxl[p] if d == "long" else pxs[p]),
                      dvig.GEOM, B)
        if r is None:
            continue
        net[p] = r["net"]
        exi[p] = r["exit_index"]
        k = r["kind"]
        kind[p] = KMAP.get(k, 2 if k.startswith(("be-stop", "stop-after")) else 4)
        if c % 50000 == 0 and c:
            лог("   %s / %s  (%.0fs)" % (format(c, ","), format(len(idx), ","),
                                         time.time() - t))
    лог("готово · с нето: %s" % format(int(np.isfinite(net).sum()), ","))
    np.savez_compressed(OUT, net=net, exit_index=exi, kind=kind)
    лог("записано %s" % OUT)


if __name__ == "__main__":
    main()
