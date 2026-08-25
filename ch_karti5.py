# -*- coding: utf-8 -*-
import sys, io, json
sys.argv = ["x"]
import live_bot as lb
import pandas as pd
S = json.load(io.open("backtest_stats.json", encoding="utf-8"))
PIP = lb.PIP; ДНИ_МАКС = 30
ВЪЗРАСТ_ВХОД = ((6, 0.231), (12, 0.052), (24, -1.590), (48, -0.681), (10**9, -1.219))
РЪБ_Ч = 12
ИМЕ = {"долар": "доларът", "лихви": "лихвите"}
ИМЕ_МН = {"долар": "доларът", "лихви": "лихвите"}
РЕД = {1:"първият",2:"вторият",3:"третият",4:"четвъртият"}
def _въз(h):
    for п,н in ВЪЗРАСТ_ВХОД:
        if h < п: return н
    return ВЪЗРАСТ_ВХОД[-1][1]

def карта_стои(direction, price_user, lv, age_h, macro, мъртви):
    пос = "покупка" if direction=="long" else "продажба"
    нето = _въз(age_h)
    късно = age_h >= РЪБ_Ч
    L = [f"⏸ САМО ЗА СВЕДЕНИЕ · нагласата за {пос} още стои · {lb._sofia()}"]
    реш = [k for k in ("долар","лихви") if k in (macro or {}) and k not in (мъртви or [])]
    зад = sum(1 for k in реш if (macro[k] if direction=="long" else not macro[k]))
    имена = " и ".join(ИМЕ[k] for k in реш)
    if реш and зад == len(реш):
        L.append(f"📌 {имена} още сочат натам · нищо не се е развалило")
    elif реш and зад == 0:
        L.append(f"⚠️ {имена} вече сочат СРЕЩУ тази посока")
    elif реш:
        L.append("⚠️ доларът и лихвите вече не сочат на една страна")
    for k in (мъртви or []):
        L.append(f"⚠️ за {ИМЕ[k]} нямам число в момента · източникът мълчи и затова не го броя")
    L.append(f"⌛ нагласата е отпреди {age_h:.0f} часа · пресният вход по нея вече мина")
    L.append(f"📊 мерено: вход, взет толкова късно след появата ѝ, дава средно {lb._пари(нето)} на сделка")
    if късно:
        L.append("👉 затова НЕ давам вход · не влизай и ти по тази карта")
    else:
        L.append("👉 картата по тази нагласа вече е пратена · ако си влязъл — дръж · ако не си — не гони цената")
    L.append(f"🔎 нивата ѝ, само за сведение: {lb._fmt(price_user,2)} · стоп {lb._fmt(lv['sl'],2)} · {lb._разст(price_user,lv['sl'])}")
    L.append("👁 пиша ти веднага, щом се появи нов и пресен сигнал")
    return "\n".join(L)

lvv = lb._levels(4365.20,"long")
print(карта_стои("long", 4365.20, lvv, 14.0, {"долар":True,"лихви":True}, []))
print()
print(карта_стои("long", 4365.20, lvv, 5.0, {"долар":True,"лихви":True}, ["лихви"]))
print("\n"+"="*60+"\n")

# ---------- 7 · КЪДЕ СМЕ ----------
def карта_къде(new_dir, за, общо, trade, s_trade, spot_g, spot_s, guard, shield, now_utc):
    L = [f"📌 КЪДЕ СМЕ СЕГА · {lb._sofia()} · снимка по твое искане"]
    if spot_g:
        L.append(f"💵 злато {lb._fmt(spot_g['mid'],2)}"
                 + (f" · сребро {lb._fmt(spot_s['mid'],3)}" if spot_s else ""))
    if new_dir:
        накъде = "НАГОРЕ" if new_dir=="long" else "НАДОЛУ"
        L.append(f"🧭 накъде гледам: {накъде}" + (f" · {за} от {общо} мои измервания сочат натам" if общо>1 else ""))
    else:
        L.append("🧭 накъде гледам: никъде · измерванията ми не сочат на една страна")
    if shield:
        L.append("⚠️ американските данни излизат сега · продажбите чакат края им")
    for нм, име, tr, sp, dec, sym in (("🥇","ЗЛАТО",trade,spot_g,2,"XAUUSD"), ("🥈","СРЕБРО",s_trade,spot_s,3,"XAGUSD")):
        ст = PIP if sym=="XAUUSD" else 0.001
        if tr:
            пос = "покупка" if tr["direction"]=="long" else "продажба"
            ден = (pd.Timestamp(now_utc)-pd.Timestamp(tr["opened"])).days + 1
            L.append(f"{нм} {име} · тече {пос} от {lb._fmt(tr['entry'],dec)} · ден {ден} от {ДНИ_МАКС}")
            пл, _ = lb._отворена_стълба(tr, sp)
            if пл is not None:
                L.append(f"💰 в момента носи {lb._пари(пл, sym)} на унция")
            прибр = [n for n,k in (("1️⃣","tp1"),("2️⃣","tp2"),("3️⃣","tp3")) if tr.get("hit",{}).get(k)]
            if прибр:
                L.append(f"✅ прибрани: {' и '.join(прибр)} · остават {3-len(прибр)} от 3 трети")
            без = abs(float(tr["levels"]["sl"])-float(tr["entry"])) < 0.01
            L.append((f"🔒 стопът е на входа {lb._fmt(tr['levels']['sl'],dec)} · на минус вече не може да излезе"
                      if без else
                      f"🛑 стопът е на {lb._fmt(tr['levels']['sl'],dec)}"
                      + (f" · {abs(float(sp['mid'])-float(tr['levels']['sl']))/ст:,.0f} пипса от сегашната цена" if sp else "")))
            for n,k in (("1️⃣","tp1"),("2️⃣","tp2"),("3️⃣","tp3")):
                if not tr.get("hit",{}).get(k) and sp:
                    L.append(f"{n} {lb._fmt(tr['levels'][k],dec)} · още {abs(tr['levels'][k]-float(sp['mid']))/ст:,.0f} пипса дотам")
        else:
            L.append(f"{нм} {име} · няма отворена сделка")
    бл = [("покупките" if д=="long" else "продажбите", int(н)) for д,н in sorted((guard or {}).items())
          if isinstance(н,(int,float)) and н>=2 and д in ("long","short")]
    for к,н in бл:
        L.append(f"⛔ днес не пращам {к} · {н} стопа в тази посока · пазачът се вдига утре")
    L.append("👉 нищо не се прави по тази карта · тя само показва")
    return "\n".join(L)

tr = {"direction":"long","entry":4358.00,"opened":"2026-08-19T09:00:00",
      "levels":lb._levels(4358.00,"long"),"hit":{"tp1":True,"tp2":True},"sym":"XAUUSD"}
tr["levels"]["sl"]=4358.00
print(карта_къде("long",2,2,tr,None,{"mid":4365.20},{"mid":65.150},{"long":2},False,"2026-08-21T09:39:00"))
