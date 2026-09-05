# -*- coding: utf-8 -*-
"""adv4_epohi.py — +158.17$/ГОД Е СРЕДНО ПРЕЗ 22 ГОДИНИ. КЪДЕ ЖИВЕЕ БОТЪТ?

Геометрията е в ДОЛАРИ (стоп 13$). Златото е било 400$ (стоп = 3.2%) и е
3400$ (стоп = 0.38%). Тук същите два уреда се мерят ПО ЕПОХИ, за да се види
дали +158$/год е число за ДНЕС или средно през девет различни пазара.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import jiv                                                        # noqa: E402
import potok                                                      # noqa: E402
import mer                                                        # noqa: E402
from adv3_tavan_den import пробег_с_дневен_таван                  # noqa: E402

REPS = 5000
SEED = 20260905


def main():
    B = jiv.лента(); G = jiv.решетка(); D = potok.подготви(G)
    брой_дни = int(B["dord"][-1]) + 1
    # ден -> година (от tsmin на първия бар в деня)
    d_first = np.zeros(брой_дни, dtype=np.int64)
    dord = B["dord"]; ts = B["tsmin"]
    _, idx = np.unique(dord, return_index=True)
    d_first[dord[idx]] = ts[idx]
    # tsmin е минути от епохата на лентата; вадим годината през datetime
    import datetime as dt
    t0 = dt.datetime(1970, 1, 1)
    год_на_ден = np.array([(t0 + dt.timedelta(minutes=int(x))).year if x else 0
                           for x in d_first])

    ЖИВ = potok.жива_настройка()
    С0 = dict(potok.СТАР)
    С6 = dict(С0, cap=ЖИВ["cap"], guard=True, guard_h=ЖИВ["guard_h"],
              guard_stops=ЖИВ["guard_stops"], cool_min=ЖИВ["cool_min"],
              cool_flip=ЖИВ["cool_flip"], reoffer=True,
              reoffer_h=ЖИВ["reoffer_h"], reoffer_h_fresh=ЖИВ["reoffer_h_fresh"],
              max_age=ЖИВ["max_age"], max_age_fresh=ЖИВ["max_age_fresh"],
              reoffer_lo=ЖИВ["reoffer_lo"], reoffer_hi=ЖИВ["reoffer_hi"],
              reoffer_tier=ЖИВ["reoffer_tier"])

    r0 = пробег_с_дневен_таван(D, B, С0, mer.геом_доставена, 0)
    r6 = пробег_с_дневен_таван(D, B, С6, mer.геом_жива, 0)
    print("СВЕРКА: %d и %d сделки (mer.py: 6846 и 22099)"
          % (len(r0["сделки"]), len(r6["сделки"])))

    v0 = mer.по_дни(r0["сделки"], брой_дни)
    v6 = mer.по_дни(r6["сделки"], брой_дни)
    d = v6 - v0

    епохи = [("2004-2011", 2004, 2011), ("2012-2015", 2012, 2015),
             ("2016-2020", 2016, 2020), ("2021-2026", 2021, 2026),
             ("2024-2026", 2024, 2026)]
    print("\n" + "=" * 126)
    print("ПО ЕПОХИ | СТАР срещу ЖИВ, сдвоено по ден, блоков бутстрап по ден, 5000 реплики")
    print("=" * 126)
    for име, a, b in епохи:
        m_дни = (год_на_ден >= a) & (год_на_ден <= b)
        год = m_дни.sum() / 252.0
        n0 = sum(1 for x in r0["сделки"] if m_дни[x[6]])
        n6 = sum(1 for x in r6["сделки"] if m_дни[x[6]])
        s0 = v0[m_дни].sum(); s6 = v6[m_дни].sum()
        жив = np.nonzero(m_дни & (np.abs(v0) + np.abs(v6) > 0))[0]
        dm, dlo, dhi, dд = jiv.бутстрап_по_ден(d[жив], жив, REPS, SEED)
        print("  %-10s ~%5.1f год | СТАР n=%5d %+8.1f$ (/год %+7.2f) | ЖИВ n=%6d %+8.1f$ (/год %+7.2f)"
              "  Δ%+.3f$/ден [%+.3f..%+.3f] %s  Δ/год %+8.2f$"
              % (име, год, n0, s0, s0 / год, n6, s6, s6 / год,
                 dm, dlo, dhi, jiv.присъда(dlo, dhi, dд), (s6 - s0) / год))

    # същото, но САМО ЖИВИЯТ уред — печели ли изобщо пари в последната епоха
    print("\n" + "=" * 126)
    print("САМО ЖИВИЯТ УРЕД по епохи | доказва ли ПОЛОЖИТЕЛНИ пари")
    print("=" * 126)
    net6 = np.array([x[4] for x in r6["сделки"]])
    day6 = np.array([x[6] for x in r6["сделки"]])
    for име, a, b in епохи:
        m_дни = (год_на_ден >= a) & (год_на_ден <= b)
        м = m_дни[day6]
        год = m_дни.sum() / 252.0
        mm, lo, hi, дни = jiv.бутстрап_по_ден(net6[м], day6[м], REPS, SEED)
        print("  %-10s n=%6d  $/сделка %+.3f [%+.3f..%+.3f] %-16s  общо %+8.1f$  /год %+8.2f$  дни=%d"
              % (име, int(м.sum()), mm, lo, hi, jiv.присъда(lo, hi, дни),
                 net6[м].sum(), net6[м].sum() / год, дни))


if __name__ == "__main__":
    main()
