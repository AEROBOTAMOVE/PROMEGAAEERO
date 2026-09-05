# -*- coding: utf-8 -*-
"""potok.py — ПОТОКЪТ НА ВХОДОВЕТЕ + ПОРТФЕЙЛЪТ, както ги прави ЖИВИЯТ бот.

Един последователен пробег по 530 659-те 15-минутни чекпойнта. На всеки
чекпойнт се пита точно каквото пита `live_bot.main()`, в СЪЩИЯ РЕД:

  анти-спам ключ         live_bot.py:7699-7700   (тук: само рамката «1ден»)
  ключът се нулира       live_bot.py:7682
  пауза cool_ok          live_bot.py:7708-7710   (COOL_MIN / COOL_FLIP_MIN)
  свободен слот          live_bot.py:7728        (`_слот_за_напомняне`)
  ПОВТОРНО ПРЕДЛАГАНЕ    live_bot.py:7729-7741
  should_sig             live_bot.py:7762
  стоп-пазач             live_bot.py:7938  +  `_advice_entry` (гейтът)
  свободен слот за ВХОД  live_bot.py:8504-8508
  сделката се пише СЛЕД потвърдено пращане  live_bot.py:9081-9099

⚠️ Редовете са четени на 05.09.2026 при HEAD=6e8e9ee07 (v18.58); файлът се
пише в същия ден и номерата мърдат. Изразите — не.

Всяко звено е ПРЕВКЛЮЧВАЕМО, за да може да се махне и да се види цената му.
`СТАР` е точно това, което `geom_harness.build_entries` прави: пауза 45/15,
БЕЗ повторно предлагане, БЕЗ таван, БЕЗ пазач.

СВЕРКА С1 (условие преди което и да е число): `СТАР` върху решетката трябва
да даде БАЙТ ЗА БАЙТ доставените 6846 входа.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import jiv                                                        # noqa: E402

ИМЕ_ПОСОКА = np.array(["short", "wait", "long"])
ИМЕ_СТЕПЕН = np.array(["weak", "medium", "strong", "premium"])

# ── живата настройка, ПРОЧЕТЕНА от live_bot, не преписана ────────────────
СТАР = dict(
    име="СТАР (geom_harness)",
    cool_min=45, cool_flip=15,        # geom_harness.py:64-65
    reoffer=False, cap=None, guard=False, gate=False,
    reoffer_h=None, reoffer_h_fresh=None, max_age=None, max_age_fresh=None,
    reoffer_lo=0, reoffer_hi=23, reoffer_tier=1,
    guard_h=4.0, guard_stops=1,
)


def жива_настройка():
    """Не преписвам числа — чета ги от живия файл в тази сесия."""
    sys.path.insert(0, str(jiv.REPO))
    import live_bot as lb
    return dict(
        име="ЖИВ (live_bot към тази сесия)",
        cool_min=lb.COOL_MIN, cool_flip=lb.COOL_FLIP_MIN,
        reoffer=True, cap=lb.ТАВАН_СДЕЛКИ, guard=lb.ПАЗАЧ_ВКЛ, gate=False,
        reoffer_h=lb.REOFFER_H, reoffer_h_fresh=lb.REOFFER_H_ПРЕСЕН,
        max_age=lb.REOFFER_MAX_AGE_H, max_age_fresh=lb.MAX_AGE_ПРЕСЕН,
        reoffer_lo=lb.REOFFER_LO, reoffer_hi=lb.REOFFER_HI,
        reoffer_tier={"weak": 0, "medium": 1, "strong": 2,
                      "premium": 3}[lb.РЕОФЕР_КЛАС],
        guard_h=lb.ПАЗАЧ_ПРОЗОРЕЦ_Ч, guard_stops=lb.ПАЗАЧ_СТОПОВЕ,
    )


def _клетка(streak_n):
    """live_bot._cell_name — дословно."""
    if streak_n == 1:
        return "day1"
    if 2 <= streak_n <= 3:
        return "fresh"
    if streak_n == 0:
        return "mixed"
    return "stale"


def _праг_ч(cfg, посока, streak_n):
    """live_bot._reoffer_h"""
    if посока == "long" and _клетка(streak_n) in ("day1", "fresh"):
        return cfg["reoffer_h_fresh"]
    return cfg["reoffer_h"]


def _таван_ч(cfg, посока, streak_n):
    """live_bot._max_age_h · <=0 значи БЕЗ таван (live_bot.py:2965-2973)."""
    т = (cfg["max_age_fresh"] if (посока == "long"
                                  and _клетка(streak_n) in ("day1", "fresh"))
         else cfg["max_age"])
    return float("inf") if т is None or т <= 0 else float(т)


def подготви(G):
    """Всичко, което пробегът чете, като плоски numpy масиви."""
    n = len(G["ts"])
    tsmin = (G["ts"] // 60_000_000).astype(np.int64)
    act = G["ok_hist"] & (G["dir"] != 0) & (G["tier"] > 0)
    return dict(
        n=n, tsmin=tsmin, act=act,
        dirn=G["dir"], tier=G["tier"],
        dname=ИМЕ_ПОСОКА[G["dir"] + 1], tname=ИМЕ_СТЕПЕН[G["tier"]],
        fill_ok=G["fill_ok"], bar_index=G["bar_index"],
        px_long=G["px_long"], px_short=G["px_short"],
        sofia_h=G["sofia_h"], score=G["score"],
        streak_long=G["streak_long"], streak_short=G["streak_short"],
        dord=G["dord_entry"],
    )


def пробег(D, B, cfg, геом_fn, само_карти=False):
    """Един пълен пробег. Връща dict със сделките и броячите."""
    n = D["n"]
    tsmin = D["tsmin"]; act = D["act"]
    dname = D["dname"]; tname = D["tname"]; tier = D["tier"]
    fill_ok = D["fill_ok"]; bidx = D["bar_index"]
    pxl = D["px_long"]; pxs = D["px_short"]; sof = D["sofia_h"]
    stl = D["streak_long"]; sts = D["streak_short"]; dord = D["dord"]

    cool_min = cfg["cool_min"]; cool_flip = cfg["cool_flip"]
    cap = cfg["cap"] if cfg["cap"] else 10 ** 9
    guard_on = cfg["guard"]; guard_h = cfg["guard_h"]; guard_st = cfg["guard_stops"]
    гейт = cfg.get("_гейт")

    last_key = ""; last_dir = ""; last_tier = 0
    last_sent = None; key_since = None

    # отворени сделки: списък (exit_tsmin, посока, истински_стоп)
    отворени = []
    guard_t = {"long": None, "short": None}
    guard_n = {"long": 0, "short": 0}

    карти = 0; карти_reoffer = 0; карти_tier_up = 0; карти_нов_ключ = 0
    сп_таван = 0; сп_пазач = 0; сп_гейт = 0; сп_fill = 0
    сделки = []

    for i in range(n):
        t = tsmin[i]
        # --- затваряне на приключилите (освобождава слот, храни пазача) ---
        if отворени:
            ост = []
            for ex_t, dr, ист in отворени:
                if ex_t <= t:
                    if ист:
                        guard_n[dr] += 1
                        guard_t[dr] = ex_t
                else:
                    ост.append((ex_t, dr, ист))
            отворени = ост

        if not act[i]:
            last_key = ""                     # live_bot.py:7567
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
                       and mins >= _праг_ч(cfg, dr, streak) * 60
                       and key_age_h is not None
                       and key_age_h <= _таван_ч(cfg, dr, streak)
                       and cfg["reoffer_lo"] <= int(sof[i]) <= cfg["reoffer_hi"])

        should = (last_key != k or tier_up or reoffer) and cool_ok
        if not should:
            continue

        # --- картата е ПРАТЕНА: часовниците се навиват (live_bot.py:8951-8957)
        карти += 1
        if reoffer and last_key == k:
            карти_reoffer += 1
            врата = "РЕ-ОФЕР"
        elif tier_up and last_key == k:
            карти_tier_up += 1
            врата = "TIER_UP"
        else:
            карти_нов_ключ += 1
            врата = "нов ключ"
        key_since = key_since if (last_key == k and key_since is not None) else t
        last_key, last_dir, last_tier, last_sent = k, dr, tr, t

        if само_карти:
            continue

        # --- вратите пред СДЕЛКАТА ---
        if guard_on:
            gt = guard_t[dr]
            n_g = guard_n[dr] if (gt is not None and 0 <= (t - gt) / 60.0 < guard_h) else 0
            if n_g >= guard_st:
                сп_пазач += 1
                continue
        if гейт is not None and not гейт(dr, streak, i):
            сп_гейт += 1
            continue
        if not слот:
            сп_таван += 1
            continue
        if not fill_ok[i]:
            сп_fill += 1
            continue

        i0 = int(bidx[i])
        px = float(pxl[i] if dr == "long" else pxs[i])
        g = геом_fn(dr)
        r = jiv.бързо(i0, dr, px, g, B)
        if r is None:
            сп_fill += 1
            continue
        ист_стоп = (r["kind"] == "stop" and abs(r["gross"]) > 0.05)
        отворени.append((int(B["tsmin"][r["exit_index"]]), dr, ист_стоп))
        сделки.append((i, i0, dr, px, r["net"], r["kind"], int(dord[i]),
                       r["n_fills"], r["net_per_fill"], врата, streak))

    return dict(карти=карти, карти_нов_ключ=карти_нов_ключ,
                карти_reoffer=карти_reoffer, карти_tier_up=карти_tier_up,
                сп_таван=сп_таван, сп_пазач=сп_пазач, сп_гейт=сп_гейт,
                сп_fill=сп_fill, сделки=сделки)


# --------------------------------------------------------------------- С1
def сверка_с1(D, G):
    """СТАРАТА настройка върху решетката ⇒ ТОЧНО доставените 6846 входа."""
    cfg = dict(СТАР)
    избрани = []
    n = D["n"]; tsmin = D["tsmin"]; act = D["act"]
    dname = D["dname"]; tname = D["tname"]; tier = D["tier"]
    last_key = ""; last_dir = ""; last_tier = 0; last_sent = None
    for i in range(n):
        if not act[i]:
            last_key = ""
            continue
        dr = dname[i]; tr = int(tier[i]); k = dr + ":" + tname[i]
        mins = None if last_sent is None else (tsmin[i] - last_sent)
        tier_up = (tr > last_tier) and (dr == last_dir)
        cool_ok = (mins is None or mins >= cfg["cool_min"]
                   or (dr != last_dir and mins >= cfg["cool_flip"]) or tier_up)
        if (k != last_key or tier_up) and cool_ok:
            избрани.append(i)
            last_key, last_dir, last_tier, last_sent = k, dr, tr, tsmin[i]
    избрани = np.array(избрани)
    избрани = избрани[D["fill_ok"][избрани]]

    E = jiv.доставени_входове()
    jiv.лог("С1 · мои входове %d · доставени %d" % (len(избрани), len(E["bar_index"])))
    assert len(избрани) == len(E["bar_index"]), "различен БРОЙ входове"
    мой_dir = dname[избрани]
    мой_px = np.where(мой_dir == "long", D["px_long"][избрани], D["px_short"][избрани])
    двойки = (("bar_index", D["bar_index"][избрани], E["bar_index"]),
              ("direction", мой_dir, E["direction"]),
              ("tier", tname[избрани], E["tier"]),
              ("score", D["score"][избрани], E["score"]),
              ("entry_px", мой_px, E["entry_px"]))
    ok = True
    for име, мое, тяхно in двойки:
        if мое.dtype.kind == "f":
            нес = int((np.abs(мое - тяхно) > 1e-12).sum())
        else:
            нес = int((мое != тяхно).sum())
        jiv.лог("   С1 %-11s разминавания: %d" % (име, нес))
        ok &= (нес == 0)
    jiv.лог("С1 %s" % ("✅ решетката възпроизвежда доставените 6846 ТОЧНО" if ok
                       else "🛑 НЕ ги възпроизвежда — нищо оттук не важи"))
    return ok
