# -*- coding: utf-8 -*-
"""konv.py — ЦЕЛИЯТ КОНВЕЙЕР, изигран ред по ред върху 530 659 чекпойнта.

Всяко звено е ПРЕВКЛЮЧВАЕМО, за да може да се махне и да се види цената му.
Звената и мястото им са взети от ЖИВИЯ live_bot.py (само се ЧЕТЕ), не от памет:

  ред 5670  ·  сетъпът умира → анти-спам ключът се нулира
  ред 5730  ·  should_sig = actionable И (нов ключ ИЛИ tier_up ИЛИ повторно) И пауза
  ред 5697  ·  повторното предлагане (REOFFER_H / MAX_AGE_H по клетка)
  ред 5645  ·  ПРЕМИУМ насрещен борд ЗАТВАРЯ отворената сделка (flip)
  ред 5879  ·  уикенд
  ред 5885  ·  US-щит (само short, само ако НЯМА отворена сделка)
  ред 5894  ·  стоп-пазач (само ако НЯМА отворена сделка) — ЖИВО ИЗКЛЮЧЕН
  ред 5925  ·  насрещна отворена сделка (непремиум) → без карта
  ред 6012  ·  «НЕ»-карта по бързата лента → заглушена
  ред 6363  ·  сделка се отваря САМО при _adv_ok (ГЕЙТ) И свободен слот (ТАВАН)
  ред 2840  ·  размерът = _zw · малък · _рw · _пw

КАКВО НЕ Е МОДЕЛИРАНО (казано, не премълчано):
  · МОЗЪКЪТ (chart_brain) — ОТДЕЛЕН производител на карти, не звено по пътя на
    дъската; фунията му е броена отделно, от живия дневник.
  · CyberQuant макро-щитът — календарът на събитията не съществува за 22 г.
  · Ключът на анти-спама в живия бот се строи от РАЗЛИЧНИТЕ отчети на 7-те
    рамки; тук е възстановена само рамката «1ден» (както в geom_harness).
  · СТРИЙК_ПАЗАЧ — пази срещу ревизия на данните ВЪТРЕ в деня; при бектест
    стрийкът се смята веднъж на ден и не може да мигне → мъртъв тук.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
sys.path.insert(0, str(IZM / "mer_mnozhitelite"))
sys.path.insert(0, str(IZM))
sys.path.insert(0, str(REPO))
import dvig                                                          # noqa: E402
import live_bot as lb                                                # noqa: E402

TIER_NAME = {1: "medium", 2: "strong", 3: "premium"}
# номерата СА РЕДЪТ по конвейера: «стигнал до звено p» ⇔ убит ≥ p
ЕТ = {"посока": 1, "степен": 2, "антиспам": 3, "US-щит": 4, "пазач": 5,
      "насрещна": 6, "заглушена": 7, "гейт": 8, "таван": 9, "изпълним": 10,
      "СДЕЛКА": 11}
СТЪПАЛА = ("чекпойнти", "ok_hist", "посока", "степен", "антиспам",
           "US-щит", "пазач", "насрещна", "заглушена", "КАРТА", "гейт", "таван",
           "изпълним", "СДЕЛКА")

# ── ЖИВАТА НАСТРОЙКА към 01.09.2026, прочетена от live_bot, не преписана ──
ЖИВА = dict(
    antispam=True, reoffer=True, mute=True,
    cool_min=lb.COOL_MIN, cool_flip=lb.COOL_FLIP_MIN,
    reoffer_h=lb.REOFFER_H, reoffer_h_fresh=lb.REOFFER_H_ПРЕСЕН,
    max_age_h=lb.REOFFER_MAX_AGE_H, max_age_fresh=lb.MAX_AGE_ПРЕСЕН,
    reoffer_lo=lb.REOFFER_LO, reoffer_hi=lb.REOFFER_HI,
    us_shield=True,
    guard=lb.ПАЗАЧ_ВКЛ,                  # ЖИВО False
    guard_stops=lb.ПАЗАЧ_СТОПОВЕ, guard_h=lb.ПАЗАЧ_ПРОЗОРЕЦ_Ч,
    opposite=True, flip=True,
    cap=lb.ТАВАН_СДЕЛКИ,
    gate=True, size=True, tier_filter=True,
)


class Гейт:
    """lb._advice_entry с памет. Викa се ЖИВАТА функция, не преписана логика."""

    def __init__(self, stats):
        self.stats = stats
        self._m = {}

    def __call__(self, посока, streak_n, dd20, shield, guard_n):
        k = (посока, int(streak_n),
             bool(np.isfinite(dd20) and dd20 < lb.NEAR_HIGH_DD20),
             bool(shield), int(guard_n))
        r = self._m.get(k)
        if r is None:
            txt, ok = lb._advice_entry(посока, int(streak_n), self.stats, None,
                                       bool(shield), int(guard_n), sym="XAUUSD",
                                       stale_price=False,
                                       dd20=(float(dd20) if np.isfinite(dd20) else None))
            r = (bool(ok), ("малък размер" in (txt or "")))
            self._m[k] = r
        return r


def тегло(посока, малък, cN, sma200, vol20, volmed, ls, ss):
    """Четирите множителя (live_bot ред 2840-2841).

    _zw идва от lb.ZONE_W, което ЖИВО е ПЛОСКО {A:1,B:1,C:1} → зоната НЕ мени
    размера. Държи се като отделен множител, за да може да се махне и премери
    като всички други."""
    _zw = 1.0                                    # = lb.ZONE_W[зона] при плоски тегла
    reg = {"below_sma200": (bool(cN < sma200) if np.isfinite(sma200) else None),
           "low_vol": (bool(vol20 < volmed) if (np.isfinite(vol20) and np.isfinite(volmed))
                       else None)}
    _рw, _ = lb._режим_тегло(посока, reg)
    _пw, _ = lb._превес_тегло(int(ls) - int(ss))
    _мw = lb.МАЛЪК_РАЗМЕР_W if малък else 1.0
    return _zw, _мw, float(_рw), float(_пw)


def бягай(D, cfg, гейт, B, записвай=False, присъди=None):
    """Един пълен пробег. Връща (сделки, фуния, карти, убит_на_стъпало)."""
    n = len(D["tsmin"])
    tsmin = D["tsmin"]; okh = D["ok_hist"]; dr = D["dir"]; tr = D["tier"]
    fok = D["fill_ok"]; bidx = D["bar_index"]; pxl = D["px_long"]; pxs = D["px_short"]
    ush = D["us_shield"]; sofh = D["sofia_h"]
    stl = D["streak_long"]; sts = D["streak_short"]; dd20 = D["dd20"]
    cN = D["cN"]; s200 = D["sma200"]; v20 = D["vol20"]; vmed = D["volmed"]
    ls = D["ls"]; ss = D["ss"]; net = D["net"]; exb = D["exit_index"]
    exts = D["exit_tsmin"]; kind = D["kind"]; dord = D["dord_entry"]

    антиспам = cfg["antispam"]; повторно = cfg["reoffer"]; заглуши = cfg["mute"]
    cool_min = cfg["cool_min"]; cool_flip = cfg["cool_flip"]
    us_on = cfg["us_shield"]; guard_on = cfg["guard"]
    guard_stops = cfg["guard_stops"]; guard_h = cfg["guard_h"]
    opp_on = cfg["opposite"]; flip_on = cfg["flip"]; cap = cfg["cap"]
    gate_on = cfg["gate"]; size_on = cfg["size"]; tierf = cfg["tier_filter"]

    last_key = ""; last_dir = ""; last_tier = 0; last_ts = None; key_since = None
    отворени = []
    guard_n = {"long": 0, "short": 0}
    guard_t = {"long": None, "short": None}
    сделки = []; карти = []
    ф = {k: 0 for k in СТЪПАЛА}
    убит = np.zeros(n, dtype=np.int8) if записвай else None

    for i in range(n):
        ф["чекпойнти"] += 1
        нч = tsmin[i]
        # ---- затваряне на приключили сделки (то пълни пазача) --------------
        if отворени:
            жив = []
            for t in отворени:
                if t["exit_tsmin"] <= нч:
                    сделки.append(t)
                    if t["kind"] == 1:                      # ИСТИНСКИ стоп, без взета цел
                        guard_n[t["dir"]] += 1
                        guard_t[t["dir"]] = t["exit_tsmin"]
                else:
                    жив.append(t)
            отворени = жив
        if not okh[i]:
            last_key = ""
            continue
        ф["ok_hist"] += 1
        if dr[i] == 0:
            last_key = ""
            if записвай:
                убит[i] = ЕТ["посока"]
            continue
        ф["посока"] += 1
        d = "long" if dr[i] == 1 else "short"
        if tierf and tr[i] <= 0:
            last_key = ""
            if записвай:
                убит[i] = ЕТ["степен"]
            continue
        ф["степен"] += 1
        streak = int(stl[i] if d == "long" else sts[i])

        # ---- ПРЕМИУМ насрещен борд ЗАТВАРЯ първичната сделка ---------------
        if flip_on and отворени and отворени[0]["dir"] != d and tr[i] == 3 and fok[i]:
            t = отворени[0]
            a0 = t["entry_bar"] + 1
            b0 = int(bidx[i])
            if b0 > a0:
                ctx, ab = dvig.ctx_за(t["entry_bar"], t["dir"], B, ab=(a0, b0))
                r = dvig.една(t["entry_bar"], t["dir"], t["entry_px"], dvig.GEOM, B,
                              ctx=ctx, ab=(a0, b0))
                if r is not None:
                    t = dict(t)
                    t["net"] = r["net"]
                    t["kind"] = 1 if r["kind"] == "stop" else 0
                    t["exit_bar"] = r["exit_index"]
                    t["exit_tsmin"] = int(нч)
                    t["flip"] = True
                    сделки.append(t)
                    if t["kind"] == 1:
                        guard_n[t["dir"]] += 1
                        guard_t[t["dir"]] = int(нч)
                    отворени = отворени[1:]

        # ---- АНТИ-СПАМ ------------------------------------------------------
        key = "%s:%s" % (d, TIER_NAME[int(tr[i])])
        mins = None if last_ts is None else (нч - last_ts)
        tier_up = (int(tr[i]) > last_tier) and (d == last_dir)
        if антиспам:
            cool_ok = (mins is None or mins >= cool_min
                       or (d != last_dir and mins >= cool_flip) or tier_up)
            key_age_h = ((нч - key_since) / 60.0
                         if (last_key == key and key_since is not None) else None)
            _мв = (cfg["max_age_fresh"] if (d == "long" and lb._cell_name(streak) == "fresh")
                   else cfg["max_age_h"])
            _мв = float("inf") if _мв <= 0 else float(_мв)
            _рх = (cfg["reoffer_h_fresh"] if (d == "long"
                   and lb._cell_name(streak) in ("day1", "fresh")) else cfg["reoffer_h"])
            reoffer = (повторно and not отворени and mins is not None
                       and mins >= _рх * 60 and key_age_h is not None and key_age_h <= _мв
                       and cfg["reoffer_lo"] <= sofh[i] <= cfg["reoffer_hi"])
            should = (last_key != key or tier_up or reoffer) and cool_ok
        else:
            should = True

        # ---- ВСИЧКИ ПРИСЪДИ СЕ СМЯТАТ ТУК, ПРЕДИ което и да е спиране ------
        # 🔴 02.09 · Без това «припокриване» е неизмеримо: щом първото звено
        # каже НЕ, останалите никога не се питат и не се знае дали биха казали
        # същото. Смятат се ВСИЧКИ, а спирането става по-долу — по РЕДА.
        # Едно и също място, един и същ израз: няма как двете да се разминат.
        gn = 0
        if guard_on and guard_t[d] is not None and guard_n[d] > 0:
            ч = (нч - guard_t[d]) / 60.0
            gn = guard_n[d] if (0 <= ч < guard_h) else 0
        ok_gate, малък = гейт(d, streak, dd20[i], bool(ush[i]), gn)
        if not gate_on:
            ok_gate = True
        бл_анти = not should
        бл_us = bool(us_on and d == "short" and ush[i] and not отворени)
        бл_паз = bool(gn >= guard_stops and not отворени)
        бл_нас = bool(opp_on and отворени and отворени[0]["dir"] != d)
        бл_загл = bool(заглуши and (not ok_gate) and (not tier_up)
                       and not (mins is None or mins >= 45))
        бл_гейт = not ok_gate
        бл_тав = bool(len(отворени) >= cap)
        if присъди is not None:
            присъди["стигнал"][i] = True
            присъди["антиспам"][i] = бл_анти
            присъди["US-щит"][i] = бл_us
            присъди["пазач"][i] = бл_паз
            присъди["насрещна"][i] = бл_нас
            присъди["заглушена"][i] = бл_загл
            присъди["гейт"][i] = бл_гейт
            присъди["таван"][i] = бл_тав

        if бл_анти:
            if записвай:
                убит[i] = ЕТ["антиспам"]
            continue
        ф["антиспам"] += 1

        # 🔴 02.09 · «ИЗПЪЛНИМ ВХОД» НЕ Е ЗВЕНО НА БОТА — това е ДУПКА В ЛЕНТАТА
        # (уикенд/празник). Стоеше ТУК и нулираше анти-спам паметта, което
        # разминаваше конвейера с geom_harness с 1 карта (6845 срещу 6846).
        # Преместено долу, до самата сделка: живият бот не знае за дупки в
        # историята и картата му тръгва независимо от тях.
        if бл_us:
            if записвай:
                убит[i] = ЕТ["US-щит"]
            continue
        ф["US-щит"] += 1

        if бл_паз:
            if записвай:
                убит[i] = ЕТ["пазач"]
            continue
        ф["пазач"] += 1

        if бл_нас:
            if записвай:
                убит[i] = ЕТ["насрещна"]
            continue
        ф["насрещна"] += 1

        if бл_загл:
            if записвай:
                убит[i] = ЕТ["заглушена"]
            continue
        ф["заглушена"] += 1

        # ---- КАРТАТА ТРЪГВА → анти-спам паметта се обновява ------------------
        ф["КАРТА"] += 1
        карти.append((int(i), d, int(tr[i]), bool(ok_gate)))
        key_since = key_since if (last_key == key and key_since is not None) else нч
        last_key, last_dir, last_tier, last_ts = key, d, int(tr[i]), нч

        if бл_гейт:
            if записвай:
                убит[i] = ЕТ["гейт"]
            continue
        ф["гейт"] += 1
        if бл_тав:
            if записвай:
                убит[i] = ЕТ["таван"]
            continue
        ф["таван"] += 1
        if not fok[i] or not np.isfinite(net[i]):
            if записвай:
                убит[i] = ЕТ["изпълним"]
            continue
        ф["изпълним"] += 1

        zw, mw, rw, pw = тегло(d, малък, cN[i], s200[i], v20[i], vmed[i], ls[i], ss[i])
        w = (zw * mw * rw * pw) if size_on else 1.0
        ф["СДЕЛКА"] += 1
        if записвай:
            убит[i] = ЕТ["СДЕЛКА"]
        отворени.append(dict(i=int(i), dir=d, entry_bar=int(bidx[i]),
                             entry_px=float(pxl[i] if d == "long" else pxs[i]),
                             exit_bar=int(exb[i]), exit_tsmin=int(exts[i]),
                             net=float(net[i]), kind=int(kind[i]), w=float(w),
                             zw=zw, mw=mw, rw=rw, pw=pw, den=int(dord[i]),
                             streak=streak, tier=int(tr[i]), flip=False))
    for t in отворени:
        сделки.append(t)
    return сделки, ф, карти, убит


# --------------------------------------------------------------------- данните
def данни():
    """🔴 02.09 · pandas.read_parquet е МЪРТВА врата в тази сесия: Windows App
    Control блокира arrow DLL-ите (WinError 4551, проверено с ctypes). Затова
    решетката се чете със самописния pq_lite, сверен с независим източник
    (pq_sverka.py: max|px − лента| = 0.000e+00 на 530 659 реда)."""
    sys.path.insert(0, str(TUK))
    import pq_lite as pl
    G = pl.read_columns(TUK / "reshetka.parquet")
    G.pop("__meta__", None)
    Z = np.load(TUK / "neta.npz")
    B = dvig.лента()
    exi = Z["exit_index"]
    exts = np.where(exi >= 0, B["tsmin"][np.clip(exi, 0, len(B["tsmin"]) - 1)],
                    np.iinfo(np.int64).max)
    D = {c: v for c, v in G.items() if c not in ("ts", "ден")}
    D["tsmin"] = G["ts"] // 60_000_000                  # µs → минути
    D["ден"] = G["ден"]
    D["net"] = Z["net"]; D["exit_index"] = exi; D["kind"] = Z["kind"]
    D["exit_tsmin"] = exts
    return G, D, B
