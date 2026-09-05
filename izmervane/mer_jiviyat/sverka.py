# -*- coding: utf-8 -*-
"""sverka.py — 0 РАЗМИНАВАНИЯ ПРЕДИ КОЕТО И ДА Е ЧИСЛО.

Пуска `jiv.едно` СРЕЩУ ДОСТАВЕНАТА `geom_harness._one_trade` (не преписана —
ИМПОРТИРАНА) на ВСИЧКИТЕ 6846 входа, при доставената геометрия и хоризонт 5
търговски дни, тоест точно режима, за който старият уред е писан.

Сравняват се: net, gross, kind, n_tp, n_fills, exit_index, hold_min.

`geom_harness` внася pyarrow на ниво модул, а arrow DLL-ите са блокирани от
Windows App Control на тази машина. `_one_trade` НЕ ползва pyarrow — само
numpy върху подадения B. Затова pyarrow се подменя с празен модул САМО за
внасянето; функцията, която се сверява, е дословно живата.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
sys.path.insert(0, str(ТУК.parent))
import jiv                                                       # noqa: E402


def _внеси_gh():
    import pandas  # noqa: F401 — pandas сам пипа pyarrow; внася се ПРЕДИ подмяната
    if "pyarrow" not in sys.modules:
        pa = types.ModuleType("pyarrow")
        pq = types.ModuleType("pyarrow.parquet")

        def _мъртво(*a, **k):
            raise RuntimeError("pyarrow не е наличен — сверката не чете parquet "
                               "през gh, само _one_trade")
        pq.read_table = _мъртво
        pa.parquet = pq
        sys.modules["pyarrow"] = pa
        sys.modules["pyarrow.parquet"] = pq
    import geom_harness as gh
    return gh


def main():
    gh = _внеси_gh()
    assert gh.SLIP_PER_TRADE == jiv.SLIP_PER_TRADE, "различен слип"
    assert gh.TIME_EXIT_DAYS == jiv.ДОСТАВЕНА_5Д["дни"], (
        "gh.TIME_EXIT_DAYS=%s, а сверката е писана за %s"
        % (gh.TIME_EXIT_DAYS, jiv.ДОСТАВЕНА_5Д["дни"]))

    B = jiv.лента()
    E = jiv.доставени_входове()
    idxs = E["bar_index"]; dirs = E["direction"]; pxs = E["entry_px"]
    n = len(idxs)
    jiv.лог("входове %d (лонг %d · шорт %d)"
            % (n, int((dirs == "long").sum()), int((dirs == "short").sum())))

    geom_gh = dict(gh.GEOM_SHIPPED)
    geom_jv = jiv.ДОСТАВЕНА_5Д
    assert geom_gh["tps"] == geom_jv["tps"] and geom_gh["sl"] == geom_jv["sl"] \
        and geom_gh["be_after_tp1"] == geom_jv["be_after_tp1"], "различна геометрия"

    ПОЛЕТА = ("net", "gross", "kind", "n_tp", "n_fills", "exit_index", "hold_min")
    разминавания = 0
    max_dnet = 0.0
    и_двете_None = 0
    примери = []
    for p in range(n):
        i0 = int(idxs[p]); d = str(dirs[p]); px = float(pxs[p])
        a = gh._one_trade(i0, d, px, geom_gh, B)
        b = jiv.едно(i0, d, px, geom_jv, B)
        if a is None or b is None:
            if a is None and b is None:
                и_двете_None += 1
                continue
            разминавания += 1
            примери.append((p, "едното е None", a, b))
            continue
        лошо = False
        for k in ПОЛЕТА:
            va, vb = a[k], b[k]
            if isinstance(va, float):
                d_ = abs(va - vb)
                if k == "net":
                    max_dnet = max(max_dnet, d_)
                if d_ > 0.0:
                    лошо = True
            elif va != vb:
                лошо = True
        if лошо:
            разминавания += 1
            if len(примери) < 5:
                примери.append((p, {k: (a[k], b[k]) for k in ПОЛЕТА}))
        if (p + 1) % 2000 == 0:
            jiv.лог("  ... %d/%d, разминавания %d" % (p + 1, n, разминавания))

    jiv.лог("=" * 70)
    jiv.лог("СВЕРКА jiv.едно  СРЕЩУ  geom_harness._one_trade")
    jiv.лог("  входове               %d" % n)
    jiv.лог("  и двете None          %d  (прозорецът е празен)" % и_двете_None)
    jiv.лог("  РАЗМИНАВАНИЯ          %d" % разминавания)
    jiv.лог("  max|Δnet|             %.2e" % max_dnet)
    for пр in примери:
        jiv.лог("  пример: %s" % (пр,))
    ok = (разминавания == 0 and max_dnet == 0.0)
    jiv.лог("ПРИСЪДА: %s" % ("✅ 0 разминавания — може да се вярва на числата"
                             if ok else "🛑 ИМА РАЗМИНАВАНИЯ — числата НЕ важат"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
