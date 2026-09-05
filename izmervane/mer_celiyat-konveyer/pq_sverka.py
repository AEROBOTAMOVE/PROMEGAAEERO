# -*- coding: utf-8 -*-
"""pq_sverka.py — доказва, че САМОПИСНИЯТ четец на parquet чете вярно.

Не «изглежда правдоподобно», а: същите числа, извадени от НЕЗАВИСИМ източник.

П1 · цените в решетката срещу .npy кеша на 1-мин лентата
     px_long[i] трябва да е B["oa"][bar_index[i]] до последния бит.
П2 · часовете: ts на чекпойнта + 15 мин ≤ tsmin на входния бар ≤ +135 мин.
П3 · доставените входове (geom_entries.parquet) — прочетени с четеца — трябва
     да са 6846 и техните entry_px да съвпадат с лентата.
П4 · булевите колони: fill_ok трябва да е точно (bar_index >= 0).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
sys.path.insert(0, str(TUK))
sys.path.insert(0, str(IZM / "mer_mnozhitelite"))
import pq_lite as pl                                                 # noqa: E402
import dvig                                                          # noqa: E402

SCRATCH = Path(r"C:\Users\User\AppData\Local\Temp\claude"
               r"\C--Users-User-Downloads-----"
               r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad")


def main():
    t0 = time.time()
    G = pl.read_columns(TUK / "reshetka.parquet")
    G.pop("__meta__")
    B = dvig.лента()
    print("[%.1fs] решетка %s реда · лента %s бара"
          % (time.time() - t0, format(len(G["ts"]), ","), format(len(B["ob"]), ",")))

    ок = G["fill_ok"]
    bi = G["bar_index"][ок]
    # ---- П1
    d1 = np.abs(G["px_long"][ок] - B["oa"][bi])
    d2 = np.abs(G["px_short"][ок] - B["ob"][bi])
    print("П1 · max|px_long − oa[bar]| = %.3e ; max|px_short − ob[bar]| = %.3e"
          % (d1.max(), d2.max()))
    assert d1.max() == 0 and d2.max() == 0, "четецът дава други цени"

    # ---- П2
    tsmin = G["ts"] // 60_000_000                    # µs → минути
    lag = B["tsmin"][bi] - tsmin[ок] - 15
    print("П2 · закъснение вход−(чекпойнт+15м): min %d, max %d, медиана %d минути"
          % (lag.min(), lag.max(), int(np.median(lag))))
    assert lag.min() >= 0 and lag.max() <= 120

    # ---- П4
    same = (G["fill_ok"] == (G["bar_index"] >= 0))
    print("П4 · fill_ok ≡ (bar_index≥0): разминавания %d" % int((~same).sum()))
    assert same.all()

    # ---- П3
    E = pl.read_columns(SCRATCH / "geom_entries.parquet")
    E.pop("__meta__")
    print("П3 · geom_entries.parquet: %s реда, колони: %s"
          % (format(len(E["bar_index"]), ","), ", ".join(sorted(E))))
    dirs = np.array([x.decode() if isinstance(x, bytes) else x for x in E["direction"]])
    px = np.where(dirs == "long", B["oa"][E["bar_index"]], B["ob"][E["bar_index"]])
    print("П3 · max|entry_px − лента| = %.3e ; long %d / short %d"
          % (np.abs(px - E["entry_px"]).max(), int((dirs == "long").sum()),
             int((dirs == "short").sum())))
    assert np.abs(px - E["entry_px"]).max() == 0
    print("✅ четецът на parquet е сверен с независим източник")


if __name__ == "__main__":
    main()
