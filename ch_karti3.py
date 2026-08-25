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

# ---------- 3 · СДЕЛКАТА ТЕЧЕ ----------
def карта_тече(tr, spot, now_utc, нов_сигнал, sym="XAUUSD", dec=2):
    ст = PIP if sym=="XAUUSD" else 0.001
    метал = "злато" if sym=="XAUUSD" else "сребро"
    пос = "покупка" if tr["direction"]=="long" else "продажба"
    hit = tr.get("hit", {}); lv = tr["levels"]; e = tr["entry"]
    пл, взети = lb._отворена_стълба(tr, spot)
    ден = (pd.Timestamp(now_utc) - pd.Timestamp(tr["opened"])).days + 1
    без_риск = abs(float(lv["sl"]) - float(e)) < 0.01
    L = [f"📌 СДЕЛКАТА ТЕЧЕ · {метал} {пос} · {lb._sofia()}"]
    if пл is not None:
        L.append(f"💰 в момента носи {lb._пари(пл, sym)} на унция")
    L.append(f"💵 влязохме на {lb._fmt(e,dec)}" + (f" · сега {lb._fmt(spot['mid'],dec)}" if spot else ""))
    прибр = [n for n,k in (("1️⃣","tp1"),("2️⃣","tp2")) if hit.get(k)]
    if прибр:
        L.append(f"✅ прибрани вече: {' и '.join(прибр)} · остава {'последната трета' if len(прибр)==2 else 'две трети'}")
    if без_риск:
        L.append(f"🔒 стопът е на входа {lb._fmt(lv['sl'],dec)} · оттук нататък не можеш да излезеш на минус")
    else:
        L.append(f"🛑 стопът е на {lb._fmt(lv['sl'],dec)} · "
                 + (f"{abs(float(spot['mid'])-float(lv['sl']))/ст:,.0f} пипса от сегашната цена" if spot else lb._разст(e,lv['sl'],sym,dec)))
    for n,k in (("1️⃣","tp1"),("2️⃣","tp2"),("3️⃣","tp3")):
        if not hit.get(k):
            ост = (abs(lv[k]-float(spot['mid']))/ст) if spot else abs(lv[k]-e)/ст
            L.append(f"{n} {lb._fmt(lv[k],dec)} · още {ост:,.0f} пипса дотам")
    L.append(f"⏳ ден {ден} от най-много {ДНИ_МАКС} · на {ДНИ_МАКС}-ия излизам по цената, каквато е")
    if нов_сигнал:
        L.append("📣 сега се появи НОВ сигнал в същата посока · втора сделка не отварям")
    L.append("👉 ти не правиш нищо · дръж тази · не отваряй нова")
    return "\n".join(L)

tr = {"direction":"long","entry":4358.00,"opened":"2026-08-19T09:00:00",
      "levels":lb._levels(4358.00,"long"),"hit":{"tp1":True,"tp2":True},"status":"open","sym":"XAUUSD"}
tr["levels"]["sl"] = 4358.00
spot = {"mid":4365.20,"src":"swq"}
print(карта_тече(tr, spot, "2026-08-21T09:39:00", True))
print("\n"+"="*60+"\n")

# ---------- 4 · ЦЕЛ 1 ----------
def карта_цел1(tr, price_hit, when, sym="XAUUSD", dec=2):
    ст = PIP if sym=="XAUUSD" else 0.001
    метал = "злато" if sym=="XAUUSD" else "сребро"
    пос = "покупка" if tr["direction"]=="long" else "продажба"
    e = tr["entry"]; lv = tr["levels"]; зн = 1 if tr["direction"]=="long" else -1
    дол = (price_hit-e)*зн
    трета = дол/3.0
    return "\n".join([
      f"✅ ПЪРВАТА ЦЕЛ Е ВЗЕТА · {метал} {пос} · {lb._sofia(when)}",
      f"💵 цената мина {lb._пари(дол,sym)}: {lb._fmt(e,dec)} → {lb._fmt(price_hit,dec)}",
      f"👉 затвори ЕДНА ТРЕТА от позицията сега",
      f"💰 тази трета добавя {lb._пари(трета,sym)} към сметката на цялата сделка",
      f"🛑 и премести стопа на входа {lb._fmt(e,dec)}",
      f"🔒 оттук нататък сделката не може да излезе на минус · най-лошото ѝ е {lb._пари(трета,sym)}",
      f"2️⃣ {lb._fmt(lv['tp2'],dec)} · още {abs(lv['tp2']-price_hit)/ст:,.0f} пипса · там прибираш втората трета",
      f"3️⃣ {lb._fmt(lv['tp3'],dec)} · още {abs(lv['tp3']-price_hit)/ст:,.0f} пипса · там затваряш последната",
      f"⏳ ако не стигне до тях, излизам най-късно на {ДНИ_МАКС}-ия ден от влизането"])
tr2 = {"direction":"long","entry":4358.00,"levels":lb._levels(4358.00,"long"),"hit":{},"sym":"XAUUSD"}
print(карта_цел1(tr2, 4365.50, "2026-08-21T10:00:00"))
