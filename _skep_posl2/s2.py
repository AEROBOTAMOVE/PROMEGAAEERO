# -*- coding: utf-8 -*-
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE); os.chdir(BASE)
import live_bot as lb
import pandas as pd

БАР = 4647.2; СПОТ = 4591.465
СТАР = 25.515; ИСТИНА = БАР - СПОТ

idx = pd.date_range("2026-08-21T10:00", periods=12, freq="5min")
bars = pd.DataFrame({"Open":[БАР]*12,"High":[4648.0]*12,"Low":[4646.4]*12,"Close":[БАР]*12}, index=idx)

# ЖИВИЯТ спот е ЕДИН И СЪЩ в двата свята — _spot_sane връща суровия фийд или None,
# никога бар−базис. Значи при ре-анкер спотът НЕ мърда.
SPOT = {"mid": СПОТ, "bid": СПОТ-0.2, "ask": СПОТ+0.2}

# КАК ЖИВИЯТ КОД ОТВАРЯ СДЕЛКА (ред 3894): entry = _entry_side(spot_g, dir) — ЖИВИЯТ СПОТ
вход = lb._entry_side(SPOT, "long")
lv = lb._levels(round(вход,2), "long")
t = {"direction":"long","entry":round(вход,2),"opened":"2026-08-21T09:55",
     "checked":"2026-08-21T09:59","ledger":"spot","v2":True,"levels":lv,
     "hit":{},"status":"open","tier":"premium","date":"2026-08-21"}
print("вход (жив спот, ask) =", t["entry"], " нива:", lv)
print("бар минус ЗАМРАЗЕН базис  =", round(БАР-СТАР,2), " → разминава с", round((БАР-СТАР)-вход,2), "$")
print("бар минус ИСТИНСКИ базис  =", round(БАР-ИСТИНА,2), " → разминава с", round((БАР-ИСТИНА)-вход,2), "$")
print()
def пусни(t, basis, скок):
    _, ev = lb.track_trade(dict(t), bars, basis, SPOT["mid"], "2026-08-21T11:00", spot=SPOT, скок_базис=скок)
    return [(e[0], e[1], e[3]) for e in ev] or "НЯМА"
print("A· ЗАМРАЗЕН грешен базис 25.515, скок_базис=False :", пусни(t, СТАР, False))
print("B· РЕ-АНКЕРВАН верен базис 55.735, скок_базис=True  :", пусни(t, ИСТИНА, True))
print("C· РЕ-АНКЕРВАН верен базис 55.735, скок_базис=False :", пусни(t, ИСТИНА, False))
ts = dict(t); ts["direction"]="short"; ts["entry"]=round(lb._entry_side(SPOT,"short"),2)
ts["levels"]=lb._levels(ts["entry"],"short")
print()
print("шорт вход", ts["entry"], ts["levels"])
print("A· замразен, скок_базис=False :", пусни(ts, СТАР, False))
print("B· ре-анкерван, скок_базис=True :", пусни(ts, ИСТИНА, True))
