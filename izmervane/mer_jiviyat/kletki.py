# -*- coding: utf-8 -*-
"""kletki.py — ЧЕТИРИТЕ КЛЕТКИ НА ГЕЙТА, ПРЕИЗМЕРЕНИ НА ЖИВИЯ БОТ.

ЗАЩО. `backtest_stats.json` → `fresh` е смятан върху ДОСТАВЕНИТЕ 6846 входа
(проверено с аритметика: сборът на n по четирите клетки е ТОЧНО 3525 лонг и
3321 шорт). Но 80.5% от сделките на живия бот идват през ВРАТА, която този
набор няма — повторното предлагане. Тоест гейтът съди всеки жив вход по числа,
мерени върху бот, в който 4 от всеки 5 такива входа НЕ СЪЩЕСТВУВАТ.

Тук същите четири клетки се смятат върху ЖИВИЯ поток.
"""
from __future__ import annotations
import collections, json, sys
from pathlib import Path
import numpy as np
ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import jiv, potok, mer                                            # noqa: E402


def кофа(s):
    return potok._клетка(int(s))


def таблица(име, с):
    print("\n  " + име)
    print("    %-8s %-7s %7s %6s %9s %9s %9s  %s"
          % ("посока", "кофа", "n", "дни", "$/сделка", "lo", "hi", "присъда"))
    for d in ("long", "short"):
        for c in ("day1", "fresh", "mixed", "stale"):
            v = [x for x in с if x[2] == d and кофа(x[10]) == c]
            if not v:
                continue
            net = np.array([x[4] for x in v]); dor = np.array([x[6] for x in v])
            m, lo, hi, дни = jiv.бутстрап_по_ден(net, dor, mer.REPS, mer.SEED)
            print("    %-8s %-7s %7d %6d %+9.3f %+9.3f %+9.3f  %s"
                  % (d, c, len(v), дни, m, lo, hi, jiv.присъда(lo, hi, дни)))


def main():
    B = jiv.лента(); G = jiv.решетка(); D = potok.подготви(G)
    assert potok.сверка_с1(D, G)
    Ж = potok.жива_настройка()
    ст = potok.пробег(D, B, dict(potok.СТАР), mer.геом_жива)
    cfg = dict(potok.СТАР, cap=Ж["cap"], guard=True, guard_h=Ж["guard_h"],
               guard_stops=Ж["guard_stops"], cool_min=Ж["cool_min"],
               cool_flip=Ж["cool_flip"], reoffer=True, reoffer_h=Ж["reoffer_h"],
               reoffer_h_fresh=Ж["reoffer_h_fresh"], max_age=Ж["max_age"],
               max_age_fresh=Ж["max_age_fresh"], reoffer_lo=Ж["reoffer_lo"],
               reoffer_hi=Ж["reoffer_hi"], reoffer_tier=Ж["reoffer_tier"])
    жв = potok.пробег(D, B, cfg, mer.геом_жива)
    print("\n" + "=" * 100)
    print("Т5 · КЛЕТКИТЕ НА ГЕЙТА · СТАРИЯТ набор входове срещу ЖИВИЯ (жива геометрия, 21д)")
    print("=" * 100)
    таблица("СТАР набор (6846 входа — това, което стои в backtest_stats.json)", ст["сделки"])
    таблица("ЖИВ набор (%d входа, с ре-офер/таван/пазач)" % len(жв["сделки"]), жв["сделки"])
    st = json.loads((jiv.REPO / "backtest_stats.json").read_text(encoding="utf-8"))["fresh"]
    print("\n  ЗАПИСАНОТО в backtest_stats.json (за сверка на СТАРИЯ ред):")
    for d in ("long", "short"):
        for c in ("day1", "fresh", "mixed", "stale"):
            g = st[d][c]
            print("    %-8s %-7s %7s %6s %+9.3f %+9.3f %+9.3f"
                  % (d, c, g.get("n"), g.get("дни"), g.get("net"),
                     g.get("lo"), g.get("hi")))


if __name__ == "__main__":
    main()
