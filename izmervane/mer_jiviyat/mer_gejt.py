# -*- coding: utf-8 -*-
"""mer_gejt.py — същият пробег, но с ВКЛЮЧЕН ГЕЙТ (`live_bot._advice_entry`).

Гейтът е петата врата пред сделката и живият бот не отваря НИТО ЕДНА без
него (live_bot.py:8393 `... and _adv_ok`). Стария уред го няма изобщо —
неговите 6846 входа са ПРЕДИ гейта. Затова тук се мери и двете страни с
гейт, за да е ясно колко от разликата остава след като най-силната жива
врата е сложена и на двете.

Гейтът НЕ се преписва — вика се ЖИВАТА функция от live_bot.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import jiv                                                        # noqa: E402
import potok                                                      # noqa: E402
import mer                                                        # noqa: E402


def направи_гейт(D, G):
    sys.path.insert(0, str(jiv.REPO))
    import live_bot as lb
    stats = json.loads((jiv.REPO / "backtest_stats.json").read_text(encoding="utf-8"))
    dd20 = G["dd20"]; ush = G["us_shield"]
    памет = {}

    def гейт(dr, streak, i):
        близо = bool(np.isfinite(dd20[i]) and dd20[i] < lb.NEAR_HIGH_DD20)
        щит = bool(ush[i]) and dr == "short"
        k = (dr, int(streak), близо, щит)
        r = памет.get(k)
        if r is None:
            _txt, ok = lb._advice_entry(dr, int(streak), stats, None, щит, 0,
                                        sym="XAUUSD", stale_price=False,
                                        dd20=(float(dd20[i]) if np.isfinite(dd20[i])
                                              else None))
            r = bool(ok)
            памет[k] = r
        return r
    return гейт


def main():
    B = jiv.лента()
    G = jiv.решетка()
    D = potok.подготви(G)
    assert potok.сверка_с1(D, G)
    брой_дни = int(B["dord"][-1]) + 1
    години = int(B["tsmin"][-1] - B["tsmin"][0]) / (60 * 24 * 365.25)
    ЖИВ = potok.жива_настройка()
    гейт = направи_гейт(D, G)

    С0 = dict(potok.СТАР, _гейт=гейт)
    С6 = dict(potok.СТАР, cap=ЖИВ["cap"], guard=True,
              guard_h=ЖИВ["guard_h"], guard_stops=ЖИВ["guard_stops"],
              cool_min=ЖИВ["cool_min"], cool_flip=ЖИВ["cool_flip"],
              reoffer=True, reoffer_h=ЖИВ["reoffer_h"],
              reoffer_h_fresh=ЖИВ["reoffer_h_fresh"],
              max_age=ЖИВ["max_age"], max_age_fresh=ЖИВ["max_age_fresh"],
              reoffer_lo=ЖИВ["reoffer_lo"], reoffer_hi=ЖИВ["reoffer_hi"],
              reoffer_tier=ЖИВ["reoffer_tier"], _гейт=гейт)

    print("")
    print("=" * 132)
    print("Т4 · С ВКЛЮЧЕН ГЕЙТ от двете страни")
    print("=" * 132)
    редове = []
    for име, cfg, gf in (("СТАР + гейт (доставена, 5д, ∞)", С0, mer.геом_доставена),
                         ("ЖИВ + гейт (жива, 21д, таван 12, пазач, ре-офер)",
                          С6, mer.геом_жива)):
        r = potok.пробег(D, B, cfg, gf)
        o = mer.отчет(име, r, брой_дни, години)
        редове.append((o, r))
        mer.покажи(o)
        jiv.лог("    спрени от ГЕЙТА: %d · таван %d · пазач %d"
                % (r["сп_гейт"], r["сп_таван"], r["сп_пазач"]))
    print("")
    mer.сдвои("СТАР+гейт → ЖИВ+гейт", редове[0][1], редове[1][1], брой_дни, години)
    a, b = редове[0][0], редове[1][0]
    if a.get("на_година"):
        print("  РАЗЛИКА В ПАРИТЕ НА ГОДИНА: %+0.2f$ = %+0.1f%% от старото число"
              % (b["на_година"] - a["на_година"],
                 100.0 * (b["на_година"] - a["на_година"]) / abs(a["на_година"])))
    print("  РАЗЛИКА В БРОЯ СДЕЛКИ: %+d (%.1f× на стария)"
          % (b["n"] - a["n"], b["n"] / max(a["n"], 1)))
    (ТУК / "rezultat_gejt.json").write_text(
        json.dumps({"редове": [x[0] for x in редове], "години": години},
                   ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
