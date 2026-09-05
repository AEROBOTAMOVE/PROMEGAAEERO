# -*- coding: utf-8 -*-
"""sp5_tavanyt_po_epohi.py — ЕДИНСТВЕНАТА ДОКАЗАНА НАХОДКА, ПРОВЕРЕНА ПО ЕПОХИ.

sp1 намери: махането на ТАВАН_СДЕЛКИ=12 дава +2.846$/ден [+1.011, +4.679] ✅.
Едно доказано число на цялата лента може да е една епоха, качена на гърба на
останалите. Тук се проверява дали знакът се държи във ВСЯКА епоха — същият
тест, който сложи стоп-пазача на пиедестал.

Плюс: ако таванът пада, най-лошият ден и просадката са цената. И те се дават.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import sp_yadro as S                                              # noqa: E402
sys.path.insert(0, str(S.MJ))
import mer                                                        # noqa: E402
import jiv                                                        # noqa: E402
import sp3_makro_i_opashka as sp3                                 # noqa: E402
import sp2_geyt_i_epohi as sp2                                    # noqa: E402
import sp4_pazachyt_chestno as sp4                                # noqa: E402

ЕПОХИ = ((2004, 2010), (2011, 2015), (2016, 2020), (2021, 2026))


def main():
    B, G, D, брой_дни, години = S.зареди()
    год = sp2.година_на_ден(B, брой_дни)
    БАЗА_CFG, Ж, lb = S.жива_база(G)
    БАЗА = sp4.пробег(D, B, БАЗА_CFG, mer.геом_жива)
    va = S.по_дни(БАЗА["сделки"], брой_дни)
    jiv.лог("БАЗА (таван 12) n=%d · общо %+0.1f$" % (len(БАЗА["сделки"]), va.sum()))

    редове = []
    for име, cap in (("БЕЗ ТАВАН (∞)", None), ("таван 24", 24), ("таван 18", 18),
                     ("таван 8", 8), ("таван 5", 5)):
        r = sp4.пробег(D, B, dict(БАЗА_CFG, cap=cap), mer.геом_жива)
        vb = S.по_дни(r["сделки"], брой_дни)
        d = vb - va
        print("\n  %s · n=%d (%+d) · общо %+0.1f$ · най-лош ден %+0.2f$ · просадка %0.2f$"
              % (име, len(r["сделки"]), len(r["сделки"]) - len(БАЗА["сделки"]),
                 vb.sum(), vb.min(), sp3.просадка(vb)), flush=True)
        еп = []
        for a, b in ЕПОХИ + (("ВСИЧКИ", None),):
            if b is None:
                m_ = np.ones(брой_дни, bool); ие = "2004-2026"
            else:
                m_ = (год >= a) & (год <= b); ие = "%d-%d" % (a, b)
            жив = np.nonzero(m_ & (np.abs(va) + np.abs(vb) > 0))[0]
            dm, dlo, dhi, dд = jiv.бутстрап_по_ден(d[жив], жив, S.REPS, S.SEED)
            еп.append(dict(епоха=ие, дни=dд, д_ден=dm, lo=dlo, hi=dhi,
                           присъда=jiv.присъда(dlo, dhi, dд)))
            print("      %-12s дни=%5d  Δ$/ден %+8.3f [%+8.3f..%+8.3f]  %s"
                  % (ие, dд, dm, dlo, dhi, jiv.присъда(dlo, dhi, dд)), flush=True)
        редове.append(dict(име=име, n=len(r["сделки"]), общо=float(vb.sum()),
                           най_лош_ден=float(vb.min()),
                           просадка=sp3.просадка(vb), епохи=еп))

    (ТУК / "rez_sp5.json").write_text(
        json.dumps({"база": dict(n=len(БАЗА["сделки"]), общо=float(va.sum()),
                                 най_лош_ден=float(va.min()),
                                 просадка=sp3.просадка(va)),
                    "редове": редове, "години": години},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    jiv.лог("записано rez_sp5.json")


if __name__ == "__main__":
    main()
