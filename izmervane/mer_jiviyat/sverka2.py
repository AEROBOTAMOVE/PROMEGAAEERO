# -*- coding: utf-8 -*-
"""sverka2.py — БЪРЗИЯТ двигател срещу БАВНИЯ (който вече е сверен с gh).

Веригата на доверието:
    gh._one_trade  ==  jiv.едно      (sverka.py, 6846 входа, 0 разминавания)
    jiv.едно       ==  jiv.бързо     (ТУК, 6846 входа × 4 режима)

Мери се при ЧЕТИРИ режима, защото живият уред ги ползва и четирите:
    доставена геометрия ·  5 търговски дни   (режимът на стария уред)
    доставена геометрия · 21 търговски дни   (живият хоризонт)
    жива геометрия      ·  5 търговски дни
    жива геометрия      · 21 търговски дни   (живият бот днес)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import jiv                                                       # noqa: E402

ПОЛЕТА = ("net", "gross", "kind", "n_tp", "n_fills", "exit_index", "hold_min")


def режим(B, E, име, geom_fn):
    idxs = E["bar_index"]; dirs = E["direction"]; pxs = E["entry_px"]
    n = len(idxs)
    лоши = 0; maxd = 0.0; и_None = 0; примери = []
    for p in range(n):
        i0 = int(idxs[p]); d = str(dirs[p]); px = float(pxs[p])
        g = geom_fn(d)
        a = jiv.едно(i0, d, px, g, B)
        b = jiv.бързо(i0, d, px, g, B)
        if a is None or b is None:
            if a is None and b is None:
                и_None += 1
                continue
            лоши += 1
            continue
        for k in ПОЛЕТА:
            va, vb = a[k], b[k]
            if isinstance(va, float):
                dd = abs(va - vb)
                if k == "net":
                    maxd = max(maxd, dd)
                if dd > 0.0:
                    лоши += 1
                    if len(примери) < 3:
                        примери.append((p, k, va, vb, a["kind"], b["kind"]))
                    break
            elif va != vb:
                лоши += 1
                if len(примери) < 3:
                    примери.append((p, k, va, vb, a["kind"], b["kind"]))
                break
    jiv.лог("  %-46s n=%d · None=%d · РАЗМИНАВАНИЯ=%d · max|Δnet|=%.2e"
            % (име, n, и_None, лоши, maxd))
    for пр in примери:
        jiv.лог("      пример %s" % (пр,))
    return лоши == 0 and maxd == 0.0


def main():
    B = jiv.лента()
    E = jiv.доставени_входове()
    jiv.лог("СВЕРКА jiv.бързо СРЕЩУ jiv.едно (която е == gh._one_trade)")
    ok = True
    ok &= режим(B, E, "доставена ·  5 търг. дни",
                lambda d: jiv.ДОСТАВЕНА_5Д)
    ok &= режим(B, E, "доставена · 21 търг. дни",
                lambda d: dict(jiv.ДОСТАВЕНА_5Д, дни=21))
    ok &= режим(B, E, "жива ·  5 търг. дни", lambda d: jiv.жива_геом(d, 5))
    ok &= режим(B, E, "жива · 21 търг. дни", lambda d: jiv.жива_геом(d, 21))
    jiv.лог("ПРИСЪДА: %s" % ("✅ 0 разминавания във ВСИЧКИТЕ четири режима"
                             if ok else "🛑 ИМА РАЗМИНАВАНИЯ"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
