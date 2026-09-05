# -*- coding: utf-8 -*-
"""sp4_pazachyt_chestno.py — ПАЗАЧЪТ, ПРЕМЕРЕН ЧЕСТНО.

НАМЕРЕН ДЕФЕКТ В УРЕДА (не в бота), доказан от собствения ми пробег:
`mer_jiviyat/potok.пробег` увеличава `guard_n` и НИКОГА не го нулира. Живият
бот нулира по ДЕН — `live_bot.py:7452`:

    guard = _load_state(out / "guard.json", {})
    if guard.get("date") != ден_карти:
        guard = {"date": ден_карти, "long": 0, "short": 0, ...}

Следствие: в стария уред след втория стоп ЗА 22 ГОДИНИ броячът е ≥2 завинаги,
затова `ПАЗАЧ_СТОПОВЕ=1/2/3` дават ТОЧНО еднакъв резултат (проверено в sp1:
n=+0 и Δ=+0.000 и за двете). Тоест ръчката «колко стопа» изобщо не беше мерена
— мереше се само ПРОЗОРЕЦЪТ.

Тук броячът се нулира на смяна на ТЪРГОВСКИЯ ДЕН (dord), както го прави
guard.json, и `ПАЗАЧ_СТОПОВЕ` става истинска ръчка.
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

ЕПОХИ = ((2004, 2010), (2011, 2015), (2016, 2020), (2021, 2026))


def пробег(D, B, cfg, геом_fn):
    """Копие на sp_yadro.пробег с ЕДНА поправка: guard_n се нулира по ДЕН."""
    n = D["n"]; tsmin = D["tsmin"]; act = D["act"]
    dname = D["dname"]; tname = D["tname"]; tier = D["tier"]
    fill_ok = D["fill_ok"]; bidx = D["bar_index"]
    pxl = D["px_long"]; pxs = D["px_short"]; sof = D["sofia_h"]
    stl = D["streak_long"]; sts = D["streak_short"]; dord = D["dord"]
    score = D["score"]
    import potok

    cool_min = cfg["cool_min"]; cool_flip = cfg["cool_flip"]
    cap = cfg["cap"] if cfg["cap"] else 10 ** 9
    guard_on = cfg["guard"]; guard_h = cfg["guard_h"]; guard_st = cfg["guard_stops"]
    гейт = cfg.get("_гейт")
    ден_таван = cfg.get("ден_таван") or 10 ** 9
    мин_точки = cfg.get("мин_точки") or 0

    last_key = ""; last_dir = ""; last_tier = 0
    last_sent = None; key_since = None
    отворени = []
    guard_t = {"long": None, "short": None}
    guard_n = {"long": 0, "short": 0}
    guard_ден = None
    ден_брой = {}
    карти = 0; сп_пазач = 0; сп_гейт = 0; сп_таван = 0; сп_fill = 0
    сделки = []

    for i in range(n):
        t = tsmin[i]
        d0 = int(dord[i])
        # ── НУЛИРАНЕ ПО ДЕН, както guard.json (live_bot.py:7452) ──
        if guard_ден != d0:
            guard_ден = d0
            guard_n["long"] = 0; guard_n["short"] = 0

        if отворени:
            ост = []
            for ex_t, dr_, ист, _d in отворени:
                if ex_t <= t:
                    if ист:
                        guard_n[dr_] += 1
                        guard_t[dr_] = ex_t
                else:
                    ост.append((ex_t, dr_, ист, _d))
            отворени = ост

        if not act[i]:
            last_key = ""
            continue
        dr = dname[i]; tr = int(tier[i]); k = dr + ":" + tname[i]
        mins = None if last_sent is None else (t - last_sent)
        tier_up = (tr > last_tier) and (dr == last_dir)
        cool_ok = (mins is None or mins >= cool_min
                   or (dr != last_dir and mins >= cool_flip) or tier_up)
        слот = len(отворени) < cap
        streak = int(stl[i] if dr == "long" else sts[i])
        reoffer = False
        if cfg["reoffer"]:
            key_age_h = ((t - key_since) / 60.0
                         if (last_key == k and key_since is not None) else None)
            reoffer = (слот and tr >= cfg["reoffer_tier"] and mins is not None
                       and mins >= potok._праг_ч(cfg, dr, streak) * 60
                       and key_age_h is not None
                       and key_age_h <= potok._таван_ч(cfg, dr, streak)
                       and cfg["reoffer_lo"] <= int(sof[i]) <= cfg["reoffer_hi"])
        should = (last_key != k or tier_up or reoffer) and cool_ok
        if not should:
            continue
        карти += 1
        key_since = key_since if (last_key == k and key_since is not None) else t
        last_key, last_dir, last_tier, last_sent = k, dr, tr, t

        if guard_on:
            gt = guard_t[dr]
            if gt is None:
                n_g = 0
            elif guard_h > 0:
                n_g = guard_n[dr] if 0 <= (t - gt) / 60.0 < guard_h else 0
            else:
                n_g = guard_n[dr]          # «до края на деня» — броячът е дневен
            if n_g >= guard_st:
                сп_пазач += 1
                continue
        if мин_точки and int(score[i]) < мин_точки:
            continue
        if гейт is not None and not гейт(dr, streak, i):
            сп_гейт += 1
            continue
        if ден_брой.get(d0, 0) >= ден_таван:
            continue
        if not слот:
            сп_таван += 1
            continue
        if not fill_ok[i]:
            сп_fill += 1
            continue
        r = jiv.бързо(int(bidx[i]), dr, float(pxl[i] if dr == "long" else pxs[i]),
                      геом_fn(dr), B)
        if r is None:
            сп_fill += 1
            continue
        ист = (r["kind"] == "stop" and abs(r["gross"]) > 0.05)
        отворени.append((int(B["tsmin"][r["exit_index"]]), dr, ист, d0))
        ден_брой[d0] = ден_брой.get(d0, 0) + 1
        сделки.append((i, int(bidx[i]), dr, 0.0, r["net"], r["kind"], d0,
                       r["n_fills"], r["net_per_fill"], "", streak))
    return dict(карти=карти, сп_пазач=сп_пазач, сп_гейт=сп_гейт,
                сп_таван=сп_таван, сп_fill=сп_fill, сделки=сделки)


def main():
    import sp3_makro_i_opashka as sp3
    import sp2_geyt_i_epohi as sp2
    B, G, D, брой_дни, години = S.зареди()
    год = sp2.година_на_ден(B, брой_дни)
    БАЗА_CFG, Ж, lb = S.жива_база(G)

    print("\n" + "=" * 126)
    print("ПАЗАЧЪТ С ДНЕВНО НУЛИРАН БРОЯЧ (както guard.json) · Δ = ВАРИАНТ минус ЖИВАТА база")
    print("=" * 126)
    БАЗА = пробег(D, B, БАЗА_CFG, mer.геом_жива)
    s0 = sum(x[4] for x in БАЗА["сделки"])
    m, lo, hi, дни = S.сам(БАЗА, брой_дни)
    print("  БАЗА (пазач 1 стоп / 4ч): n=%d дни=%d $/сделка %+0.3f [%+0.3f..%+0.3f] %s "
          "общо %+0.1f$ · спрени от пазача %d"
          % (len(БАЗА["сделки"]), дни, m, lo, hi, jiv.присъда(lo, hi, дни), s0,
             БАЗА["сп_пазач"]), flush=True)

    ВАР = [
        ("ПАЗАЧ_ВКЛ=не", dict(БАЗА_CFG, guard=False)),
        ("ПАЗАЧ_СТОПОВЕ=2", dict(БАЗА_CFG, guard_stops=2)),
        ("ПАЗАЧ_СТОПОВЕ=3", dict(БАЗА_CFG, guard_stops=3)),
        ("ПАЗАЧ_ПРОЗОРЕЦ_Ч=1", dict(БАЗА_CFG, guard_h=1.0)),
        ("ПАЗАЧ_ПРОЗОРЕЦ_Ч=2", dict(БАЗА_CFG, guard_h=2.0)),
        ("ПАЗАЧ_ПРОЗОРЕЦ_Ч=8", dict(БАЗА_CFG, guard_h=8.0)),
        ("ПАЗАЧ_ПРОЗОРЕЦ_Ч=24", dict(БАЗА_CFG, guard_h=24.0)),
        ("ПАЗАЧ_ПРОЗОРЕЦ_Ч=0 (до края на деня)", dict(БАЗА_CFG, guard_h=0.0)),
        ("ПАЗАЧ 2 стопа / до края на деня (старото)",
         dict(БАЗА_CFG, guard_h=0.0, guard_stops=2)),
    ]
    редове = []
    без = None
    for име, cfg in ВАР:
        r = пробег(D, B, cfg, mer.геом_жива)
        if име == "ПАЗАЧ_ВКЛ=не":
            без = r
        dm, dlo, dhi, dд = S.сдвоено(БАЗА, r, брой_дни)
        s1 = sum(x[4] for x in r["сделки"])
        v = S.по_дни(r["сделки"], брой_дни)
        редове.append(dict(име=име, n=len(r["сделки"]),
                           dn=len(r["сделки"]) - len(БАЗА["сделки"]),
                           д_ден=dm, lo=dlo, hi=dhi, дни=dд,
                           на_година=(s1 - s0) / години,
                           най_лош_ден=float(v.min()),
                           присъда=jiv.присъда(dlo, dhi, dд)))
        print("  %-42s n=%6d (%+6d)  Δ$/ден %+7.3f [%+7.3f..%+7.3f] %-16s "
              "Δ$/год %+8.2f · най-лош ден %+8.2f$"
              % (име, len(r["сделки"]), len(r["сделки"]) - len(БАЗА["сделки"]),
                 dm, dlo, dhi, jiv.присъда(dlo, dhi, dд), (s1 - s0) / години,
                 float(v.min())), flush=True)

    print("\n  ЕПОХИ · Δ = БЕЗ ПАЗАЧ минус С ПАЗАЧ (отрицателно = пазачът печели)")
    va = S.по_дни(БАЗА["сделки"], брой_дни)
    vb = S.по_дни(без["сделки"], брой_дни)
    d = vb - va
    еп = []
    for a, b in ЕПОХИ + (("ВСИЧКИ", None),):
        if b is None:
            m_ = np.ones(брой_дни, bool); име = "2004-2026"
        else:
            m_ = (год >= a) & (год <= b); име = "%d-%d" % (a, b)
        жив = np.nonzero(m_ & (np.abs(va) + np.abs(vb) > 0))[0]
        dm, dlo, dhi, dд = jiv.бутстрап_по_ден(d[жив], жив, S.REPS, S.SEED)
        еп.append(dict(епоха=име, дни=dд, д_ден=dm, lo=dlo, hi=dhi,
                       присъда=jiv.присъда(dlo, dhi, dд)))
        print("    %-12s дни=%5d  Δ$/ден %+8.3f [%+8.3f..%+8.3f]  %s"
              % (име, dд, dm, dlo, dhi, jiv.присъда(dlo, dhi, dд)), flush=True)

    (ТУК / "rez_sp4.json").write_text(
        json.dumps({"редове": редове, "епохи": еп, "години": години},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    jiv.лог("записано rez_sp4.json")


if __name__ == "__main__":
    main()
