# -*- coding: utf-8 -*-
import sys, io, json
sys.argv = ["x"]
import live_bot as lb
import pandas as pd
S = json.load(io.open("backtest_stats.json", encoding="utf-8"))
PIP = lb.PIP; ДНИ_МАКС = 30
ВЪЗРАСТ_ВХОД = ((6, 0.231), (12, 0.052), (24, -1.590), (48, -0.681), (10**9, -1.219))
def _въз(h):
    for п,н in ВЪЗРАСТ_ВХОД:
        if h < п: return н
    return ВЪЗРАСТ_ВХОД[-1][1]
def _бр(n): return f"{n:,}".replace(",", " ")

# ---------- 5 · СТОП ----------
def карта_стоп(tr, price_hit, when, gap, guard_n, взети, стълба, sym="XAUUSD", dec=2):
    метал = "злато" if sym=="XAUUSD" else "сребро"
    пос = "покупка" if tr["direction"]=="long" else "продажба"
    e = tr["entry"]
    L = [f"🛑 СТОПЪТ СЕ ИЗПЪЛНИ · {метал} {пос} · {lb._sofia(when)}",
         f"💵 влязохме на {lb._fmt(e,dec)} · излязохме на {lb._fmt(price_hit,dec)}",
         f"💰 сделката свърши на {lb._пари(стълба,sym)} на унция · това ѝ е целият резултат"]
    if gap:
        L.append("⚠️ цената прескочи стопа, вместо да го докосне · при твоя брокер загубата може да е малко по-голяма")
    L.append("👉 ти не правиш нищо · брокерът вече те е извадил")
    if guard_n >= 2:
        L.append(f"⛔ това е {guard_n}-ият стоп днес в тази посока · до утре не пращам нови карти натам")
    elif guard_n == 1:
        L.append("📌 това е първият стоп днес в тази посока · при втори спирам картите до утре")
    L.append("👁 сделката е затворена · чакам следващия ясен сигнал")
    return "\n".join(L)

tr = {"direction":"long","entry":4358.00,"levels":lb._levels(4358.00,"long"),"hit":{},"sym":"XAUUSD"}
print(карта_стоп(tr, 4338.00, "2026-08-21T10:00:00", True, 2, 0, -20.0))
print("\n"+"="*60+"\n")

# ---------- 6 · СТОИ ----------
def карта_стои(direction, price_user, lv, age_h, за, общо, macro, мъртви):
    пос = "покупка" if direction=="long" else "продажба"
    нето = _въз(age_h)
    L = [f"⏸ САМО ЗА СВЕДЕНИЕ · нагласата за {пос} още стои · {lb._sofia()}"]
    реш = [k for k in ("долар","лихви") if k in (macro or {}) and k not in (мъртви or [])]
    зад = sum(1 for k in реш if (macro[k] if direction=="long" else not macro[k]))
    if реш and зад == len(реш):
        L.append(f"📌 {' и '.join(реш)}те още сочат натам · нищо не се е развалило")
    elif реш and зад == 0:
        L.append(f"⚠️ {' и '.join(реш)}те вече сочат СРЕЩУ тази посока")
    elif реш:
        L.append("⚠️ доларът и лихвите вече не са единодушни")
    if мъртви:
        L.append(f"⚠️ за {', '.join(мъртви)} нямам число в момента · източникът мълчи и не го броя")
    L.append(f"⌛ нагласата е отпреди {age_h:.0f} часа · пресният вход по нея мина")
    L.append(f"📊 мерено: вход, взет толкова късно, дава средно {lb._пари(нето)} на сделка")
    L.append("👉 затова НЕ давам вход · ти също не влизай по тази карта")
    L.append(f"🔎 нивата, ако някога стане вход: {lb._fmt(price_user,2)} · стоп {lb._fmt(lv['sl'],2)} · {lb._разст(price_user,lv['sl'])}")
    L.append("👁 пиша ти веднага, щом се появи нов и пресен сигнал")
    return "\n".join(L)

lvv = lb._levels(4365.20,"long")
print(карта_стои("long", 4365.20, lvv, 14.0, 2, 2, {"долар":True,"лихви":True}, []))
print()
print(карта_стои("long", 4365.20, lvv, 3.0, 2, 2, {"долар":True,"лихви":True}, ["лихви"]))
