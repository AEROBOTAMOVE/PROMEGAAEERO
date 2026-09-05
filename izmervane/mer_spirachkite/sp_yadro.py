# -*- coding: utf-8 -*-
"""sp_yadro.py — ЯДРОТО за «коя спирачка колко струва».

Стъпва ИЗЦЯЛО върху `mer_jiviyat` (jiv/potok), който е сверен в тази сесия:
  · jiv.едно  == geom_harness._one_trade        → 0 разминавания
  · jiv.бързо == jiv.едно                       → 0 разминавания
  · potok.сверка_с1: СТАРАТА настройка ⇒ доставените 6846 входа → 0

ДОБАВЯ три неща, които potok.пробег няма и които са НУЖНИ за въпроса:
  1. ТАВАН_ВХОД_ДЕН   (live_bot.py:1732) — таван на ВХОДОВЕТЕ за календарен ден
  2. ГЕЙТ_МИН_ТОЧКИ   (live_bot.py:8078) — праг по точки ПРЕД гейта
  3. ПАЗАЧ_ПРОЗОРЕЦ_Ч=0 = «до края на деня» (live_bot._пазач_n връща n),
     а не «изключен», както го тълкува potok.пробег

Нищо в repo/ извън izmervane/ не се пише. live_bot се ЧЕТЕ и ИЗПЪЛНЯВА.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ТУК = Path(__file__).resolve().parent
MJ = ТУК.parent / "mer_jiviyat"
sys.path.insert(0, str(MJ))
import jiv                                                        # noqa: E402
import potok                                                      # noqa: E402
import mer                                                        # noqa: E402

REPS = 5000
SEED = 20260905


# ─────────────────────────────────────────────────────────── гейтът (жив)
def направи_гейт(G, *, us_щит=True, мин_дни=None, min_n=None,
                 лонг_недоказано=None, шорт_недоказано=None):
    """Вика ЖИВАТА `live_bot._advice_entry`. Ръчките се менят САМО в паметта
    на този процес (setattr върху модула), файлът не се пипа."""
    sys.path.insert(0, str(jiv.REPO))
    import live_bot as lb
    if мин_дни is not None:
        lb.МИН_ДНИ = int(мин_дни)
    if min_n is not None:
        lb.MIN_N = int(min_n)
    if лонг_недоказано is not None:
        lb.ГЕЙТ_ЛОНГ_НЕДОКАЗАНО = bool(лонг_недоказано)
    if шорт_недоказано is not None:
        lb.ГЕЙТ_ШОРТ_НЕДОКАЗАНО = bool(шорт_недоказано)
    stats = json.loads((jiv.REPO / "backtest_stats.json").read_text(encoding="utf-8"))
    dd20 = G["dd20"]; ush = G["us_shield"]
    памет = {}

    def гейт(dr, streak, i):
        близо = bool(np.isfinite(dd20[i]) and dd20[i] < lb.NEAR_HIGH_DD20)
        щит = bool(us_щит) and bool(ush[i]) and dr == "short"
        k = (dr, int(streak), близо, щит)
        r = памет.get(k)
        if r is None:
            _t, ok = lb._advice_entry(dr, int(streak), stats, None, щит, 0,
                                      sym="XAUUSD", stale_price=False,
                                      dd20=(float(dd20[i]) if np.isfinite(dd20[i])
                                            else None))
            r = bool(ok)
            памет[k] = r
        return r
    return гейт, lb


# ─────────────────────────────────────────────────────── пробегът (разширен)
def пробег(D, B, cfg, геом_fn):
    """Копие на potok.пробег + дневен таван входове + праг по точки +
    честното «прозорец 0 = до края на деня»."""
    n = D["n"]
    tsmin = D["tsmin"]; act = D["act"]
    dname = D["dname"]; tname = D["tname"]; tier = D["tier"]
    fill_ok = D["fill_ok"]; bidx = D["bar_index"]
    pxl = D["px_long"]; pxs = D["px_short"]; sof = D["sofia_h"]
    stl = D["streak_long"]; sts = D["streak_short"]; dord = D["dord"]
    score = D["score"]

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
    guard_ден = {"long": -1, "short": -1}      # деня, в който броячът е пълнен
    ден_брой = {}

    карти = 0; сп_таван = 0; сп_пазач = 0; сп_гейт = 0; сп_fill = 0
    сп_точки = 0; сп_ден = 0
    карти_reoffer = 0
    сделки = []

    for i in range(n):
        t = tsmin[i]
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
            reoffer = (слот and tr >= cfg["reoffer_tier"]
                       and mins is not None
                       and mins >= potok._праг_ч(cfg, dr, streak) * 60
                       and key_age_h is not None
                       and key_age_h <= potok._таван_ч(cfg, dr, streak)
                       and cfg["reoffer_lo"] <= int(sof[i]) <= cfg["reoffer_hi"])

        should = (last_key != k or tier_up or reoffer) and cool_ok
        if not should:
            continue
        карти += 1
        if reoffer and last_key == k:
            карти_reoffer += 1
        key_since = key_since if (last_key == k and key_since is not None) else t
        last_key, last_dir, last_tier, last_sent = k, dr, tr, t

        # ── вратите пред СДЕЛКАТА, в реда на живия бот ──
        if guard_on:
            gt = guard_t[dr]
            if gt is None:
                n_g = 0
            elif guard_h > 0:
                n_g = guard_n[dr] if 0 <= (t - gt) / 60.0 < guard_h else 0
            else:
                # ПАЗАЧ_ПРОЗОРЕЦ_Ч<=0 → live_bot._пазач_n връща брояча както е,
                # а той се нулира на СМЯНА НА ДЕНЯ (guard.json е дневен)
                n_g = guard_n[dr] if guard_ден[dr] == int(dord[i]) else 0
            if n_g >= guard_st:
                сп_пазач += 1
                continue
        if мин_точки and int(score[i]) < мин_точки:
            сп_точки += 1
            continue
        if гейт is not None and not гейт(dr, streak, i):
            сп_гейт += 1
            continue
        d0 = int(dord[i])
        if ден_брой.get(d0, 0) >= ден_таван:
            сп_ден += 1
            continue
        if not слот:
            сп_таван += 1
            continue
        if not fill_ok[i]:
            сп_fill += 1
            continue

        i0 = int(bidx[i])
        px = float(pxl[i] if dr == "long" else pxs[i])
        r = jiv.бързо(i0, dr, px, геом_fn(dr), B)
        if r is None:
            сп_fill += 1
            continue
        ист = (r["kind"] == "stop" and abs(r["gross"]) > 0.05)
        отворени.append((int(B["tsmin"][r["exit_index"]]), dr, ист, d0))
        guard_ден[dr] = d0
        ден_брой[d0] = ден_брой.get(d0, 0) + 1
        сделки.append((i, i0, dr, px, r["net"], r["kind"], d0,
                       r["n_fills"], r["net_per_fill"], "", streak))

    return dict(карти=карти, карти_reoffer=карти_reoffer,
                сп_таван=сп_таван, сп_пазач=сп_пазач, сп_гейт=сп_гейт,
                сп_fill=сп_fill, сп_точки=сп_точки, сп_ден=сп_ден,
                сделки=сделки, карти_нов_ключ=0, карти_tier_up=0)


# ─────────────────────────────────────────────────────────── статистика
def по_дни(сделки, брой_дни):
    v = np.zeros(брой_дни)
    for x in сделки:
        v[x[6]] += x[4]
    return v


def сдвоено(a, b, брой_дни):
    """Б МИНУС А по ТЪРГОВСКИ ДЕН. Положително = вариантът Б носи повече."""
    va = по_дни(a["сделки"], брой_дни)
    vb = по_дни(b["сделки"], брой_дни)
    d = vb - va
    жив = np.nonzero(np.abs(va) + np.abs(vb) > 0)[0]
    return jiv.бутстрап_по_ден(d[жив], жив, REPS, SEED)


def сам(r, брой_дни):
    """$/сделка на самия вариант."""
    с = r["сделки"]
    if not с:
        return (float("nan"),) * 3 + (0,)
    net = np.array([x[4] for x in с]); dor = np.array([x[6] for x in с])
    return jiv.бутстрап_по_ден(net, dor, REPS, SEED)


def зареди():
    B = jiv.лента(); G = jiv.решетка(); D = potok.подготви(G)
    assert potok.сверка_с1(D, G), "С1 падна — нищо оттук не важи"
    брой_дни = int(B["dord"][-1]) + 1
    години = int(B["tsmin"][-1] - B["tsmin"][0]) / (60 * 24 * 365.25)
    return B, G, D, брой_дни, години


def жива_база(G, **гейт_кв):
    """Точната жива настройка + ЖИВИЯТ гейт (без него ботът не отваря нищо)."""
    Ж = potok.жива_настройка()
    гейт, lb = направи_гейт(G, **гейт_кв)
    cfg = dict(potok.СТАР,
               име="ЖИВ",
               cool_min=Ж["cool_min"], cool_flip=Ж["cool_flip"],
               reoffer=True, reoffer_h=Ж["reoffer_h"],
               reoffer_h_fresh=Ж["reoffer_h_fresh"],
               max_age=Ж["max_age"], max_age_fresh=Ж["max_age_fresh"],
               reoffer_lo=Ж["reoffer_lo"], reoffer_hi=Ж["reoffer_hi"],
               reoffer_tier=Ж["reoffer_tier"],
               cap=Ж["cap"], guard=Ж["guard"], guard_h=Ж["guard_h"],
               guard_stops=Ж["guard_stops"],
               _гейт=гейт, ден_таван=lb.ТАВАН_ВХОД_ДЕН or None,
               мин_точки=lb.ГЕЙТ_МИН_ТОЧКИ)
    return cfg, Ж, lb
