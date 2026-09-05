# -*- coding: utf-8 -*-
"""vrati.py — ПРЕЗ КОЯ ВРАТА влиза всяка сделка на ЖИВИЯ уред.

Отговаря на въпроса «колко от живите входове са РЕ-ОФЕР» върху 22 години,
не върху 46 дни дневник. Числата от дневника са в README-то до тези.
"""
from __future__ import annotations
import collections, sys
from pathlib import Path
import numpy as np
ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import jiv, potok, mer                                            # noqa: E402


def main():
    B = jiv.лента(); G = jiv.решетка(); D = potok.подготви(G)
    assert potok.сверка_с1(D, G)
    брой_дни = int(B["dord"][-1]) + 1
    години = int(B["tsmin"][-1] - B["tsmin"][0]) / (60 * 24 * 365.25)
    Ж = potok.жива_настройка()
    cfg = dict(potok.СТАР, cap=Ж["cap"], guard=True, guard_h=Ж["guard_h"],
               guard_stops=Ж["guard_stops"], cool_min=Ж["cool_min"],
               cool_flip=Ж["cool_flip"], reoffer=True, reoffer_h=Ж["reoffer_h"],
               reoffer_h_fresh=Ж["reoffer_h_fresh"], max_age=Ж["max_age"],
               max_age_fresh=Ж["max_age_fresh"], reoffer_lo=Ж["reoffer_lo"],
               reoffer_hi=Ж["reoffer_hi"], reoffer_tier=Ж["reoffer_tier"])
    r = potok.пробег(D, B, cfg, mer.геом_жива)
    с = r["сделки"]
    print("")
    print("ЖИВИЯТ УРЕД · %d сделки · %d карти (%.2f години)" % (len(с), r["карти"], години))
    бр = collections.Counter(x[9] for x in с)
    for k, v in бр.most_common():
        net = np.array([x[4] for x in с if x[9] == k])
        dord = np.array([x[6] for x in с if x[9] == k])
        m, lo, hi, дни = jiv.бутстрап_по_ден(net, dord, mer.REPS, mer.SEED)
        print("  %-10s %6d сделки = %5.1f%%  ·  $/сделка %+7.3f [%+7.3f..%+7.3f] %s · дни=%d · общо %+9.1f$"
              % (k, v, 100.0 * v / len(с), m, lo, hi, jiv.присъда(lo, hi, дни), дни, net.sum()))
    print("  ---")
    print("  СТАРИЯТ уред вижда САМО «нов ключ» и «TIER_UP» и то при пауза 45/15:")
    print("  6846 сделки. Тоест %d от %d живи сделки (%.1f%%) НЕ СЪЩЕСТВУВАТ за него."
          % (len(с) - 6846, len(с), 100.0 * (len(с) - 6846) / len(с)))


if __name__ == "__main__":
    main()
