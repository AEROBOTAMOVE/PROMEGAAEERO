# -*- coding: utf-8 -*-
"""k2_funiya.py — ФУНИЯТА: от N възможни сигнала колко минават всяко звено.

Пуска конвейера с ЖИВАТА настройка и отпечатва стъпалата.
Преди това — СВЕРКА С3: конвейерът с ИЗКЛЮЧЕНИ всички звена след анти-спама и
с паузите на geom_harness (45/15) трябва да даде ТОЧНО доставените 6846 входа —
не «толкова на брой», а СЪЩИТЕ барове, един по един.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

TUK = Path(__file__).resolve().parent
sys.path.insert(0, str(TUK))
import konv                                                          # noqa: E402
import pq_lite as pl                                                 # noqa: E402

SCRATCH = Path(r"C:\Users\User\AppData\Local\Temp\claude"
               r"\C--Users-User-Downloads-----"
               r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad")
T0 = time.time()


def лог(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)


def сверка_с3(D, B, гейт):
    cfg = dict(konv.ЖИВА)
    cfg.update(antispam=True, reoffer=False, mute=False, cool_min=45, cool_flip=15,
               us_shield=False, guard=False, opposite=False, flip=False,
               cap=10 ** 9, gate=False, size=False)
    сд, ф, карти, _ = konv.бягай(D, cfg, гейт, B)
    лог("С3 · конвейер само с анти-спам 45/15 → карти %d" % ф["КАРТА"])
    мои = np.array([D["bar_index"][i] for i, *_ in карти if D["fill_ok"][i]])
    E = pl.read_columns(SCRATCH / "geom_entries.parquet", ["bar_index", "direction"])
    тех = E["bar_index"]
    лог("С3 · с изпълним бар: %d · доставени входове: %d" % (len(мои), len(тех)))
    assert len(мои) == len(тех), "различен БРОЙ входове"
    нес = int((np.sort(мои) != np.sort(тех)).sum())
    лог("С3 · разминаващи се БАРОВЕ: %d" % нес)
    assert нес == 0
    моиd = [d for i, d, *_ in карти if D["fill_ok"][i]]
    техd = [x.decode() if isinstance(x, bytes) else x for x in E["direction"]]
    assert моиd == list(техd), "различни ПОСОКИ"
    лог("С3 ✅ конвейерът възпроизвежда доставените 6846 входа ред по ред")


def main():
    G, D, B = konv.данни()
    stats = json.load(open(konv.REPO / "backtest_stats.json", encoding="utf-8"))
    гейт = konv.Гейт(stats)
    сверка_с3(D, B, гейт)

    сд, ф, карти, убит = konv.бягай(D, konv.ЖИВА, гейт, B, записвай=True)
    лог("ЖИВАТА настройка: сделки %d · карти %d" % (len(сд), ф["КАРТА"]))
    np.save(TUK / "ubit_zhiva.npy", убит)
    with open(TUK / "sdelki_zhiva.json", "w", encoding="utf-8") as f:
        json.dump(сд, f)
    with open(TUK / "funiya_zhiva.json", "w", encoding="utf-8") as f:
        json.dump(ф, f, ensure_ascii=False)

    n0 = ф["чекпойнти"]
    print()
    print("ФУНИЯ · ЖИВАТА НАСТРОЙКА (01.09.2026) · 15-мин решетка 2004-06-30 .. 2026-07-07")
    print("%-34s %12s %10s %10s" % ("стъпало", "остават", "% от вход", "% от преди"))
    ред = [("всички чекпойнти", "чекпойнти"),
           ("има история и макро", "ok_hist"),
           ("дъска · има ПОСОКА", "посока"),
           ("дъска · СТЕПЕН > weak", "степен"),
           ("АНТИ-СПАМ (ключ/пауза/повторно)", "антиспам"),
           ("US-щит", "US-щит"),
           ("СТОП-ПАЗАЧ", "пазач"),
           ("насрещна отворена сделка", "насрещна"),
           ("заглушена «НЕ»-карта", "заглушена"),
           ("→ ИЗЛЯЗЛА КАРТА", "КАРТА"),
           ("ГЕЙТ (клетка + MIN_N + шум)", "гейт"),
           ("ТАВАН на сделките", "таван"),
           ("изпълним бар (дупка в лентата)", "изпълним"),
           ("→ ОТВОРЕНА СДЕЛКА", "СДЕЛКА")]
    пред = None
    for име, k in ред:
        v = ф[k]
        print("%-34s %12s %9.3f%% %9.1f%%"
              % (име, format(v, ","), 100.0 * v / n0,
                 100.0 if пред is None else 100.0 * v / max(пред, 1)))
        пред = v
    print()
    print("КОЛКО РЕЖЕ ВСЯКО ЗВЕНО (от пристигналите при него)")
    print("%-34s %12s %12s %10s" % ("звено", "пристигат", "реже", "% реже"))
    пред = None
    for име, k in ред:
        v = ф[k]
        if пред is not None:
            print("%-34s %12s %12s %9.1f%%"
                  % (име, format(пред, ","), format(пред - v, ","),
                     100.0 * (пред - v) / max(пред, 1)))
        пред = v


if __name__ == "__main__":
    main()
