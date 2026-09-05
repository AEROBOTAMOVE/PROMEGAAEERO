# -*- coding: utf-8 -*-
"""s1 · РАЗПРЕДЕЛЕНИЕТО НА ПРОИЗВЕДЕНИЕТО върху 6846-те одитирани входа."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

TUK = Path(__file__).resolve().parent
sys.path.insert(0, str(TUK))
import tegla                                                         # noqa: E402
import live_bot as lb                                                # noqa: E402


def таблица(W, име, n_общо):
    v = W["W"].values
    u, c = np.unique(np.round(v, 6), return_counts=True)
    o = np.argsort(-u)
    print("\n  %-38s n=%d" % (име, len(v)))
    print("  %8s %8s %7s %8s   %s" % ("дял", "брой", "%", "кум.%", "дума на картата"))
    кум = 0.0
    for i in o:
        кум += 100.0 * c[i] / len(v)
        _, дума, дял = lb._сила(float(u[i]))
        print("  %7.1f%% %8d %6.1f%% %7.1f%%   %s · %s"
              % (100 * u[i], c[i], 100.0 * c[i] / len(v), кум, дума, дял))
    print("  ── медиана %.1f%% · средно %.1f%% · =100%%: %.1f%% · <25%%: %.1f%% · <50%%: %.1f%%"
          % (100 * np.median(v), 100 * v.mean(),
             100.0 * (v >= 0.999).mean(), 100.0 * (v < 0.25).mean(),
             100.0 * (v < 0.50).mean()))
    return v


def main():
    E = tegla.данни()
    гейт, _ = tegla.гейт_маска(E)
    print("=" * 78)
    print("s1 · РАЗПРЕДЕЛЕНИЕТО НА ПРОИЗВЕДЕНИЕТО  _zw × малък × _рw × _пw")
    print("=" * 78)
    print("входове: %d  (long %d / short %d)   гейтът пуска: %d (%.1f%%)"
          % (len(E), (E.direction == "long").sum(), (E.direction == "short").sum(),
             гейт.sum(), 100.0 * гейт.mean()))

    # какво изобщо се пали
    W = tegla.множители(E)
    print("\nКОЛКО ЧЕСТО ВСЕКИ МНОЖИТЕЛ Е ПОД 1 (всичките 6846):")
    for k, име in (("zw", "зона  _zw"), ("мw", "малък _мw"), ("рw", "режим _рw"),
                   ("пw", "превес _пw")):
        print("   %-12s пали се в %5.1f%% от входовете   стойности: %s"
              % (име, 100.0 * (W[k].values < 0.999).mean(),
                 dict(pd.Series(np.round(W[k].values, 3)).value_counts())))

    for име, zmap in tegla.ZONE_ВАРИАНТИ.items():
        Wz = tegla.множители(E, zone_w=zmap)
        print("\n" + "-" * 78)
        print("ZONE_W = %s   %s" % (име, zmap))
        таблица(Wz, "ВСИЧКИ 6846 входа", len(E))
        таблица(Wz[гейт].reset_index(drop=True), "САМО ГЕЙТ-ПУСНАТИТЕ", int(гейт.sum()))

    # какво носи гейт-пуснатата половина
    print("\n" + "-" * 78)
    print("ГЕЙТ-ПУСНАТИТЕ по клетка и посока:")
    G = E[гейт]
    print(G.groupby(["direction", "клетка"]).size().to_string())


if __name__ == "__main__":
    main()
