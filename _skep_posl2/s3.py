# -*- coding: utf-8 -*-
import sys, io, os, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE); os.chdir(BASE)
import live_bot as lb
import pandas as pd

БАР = 4647.2; СПОТ = 4591.465
СТАР = 25.515; ИСТИНА = БАР - СПОТ
idx = pd.date_range("2026-08-21T10:00", periods=12, freq="5min")
bars = pd.DataFrame({"Open":[БАР]*12,"High":[4648.0]*12,"Low":[4646.4]*12,"Close":[БАР]*12}, index=idx)
SPOT = {"mid": СПОТ, "bid": СПОТ-0.2, "ask": СПОТ+0.2}

def прясна(посока):
    вход = round(lb._entry_side(SPOT, посока), 2)
    return {"direction":посока,"entry":вход,"opened":"2026-08-21T09:55",
            "checked":"2026-08-21T09:59","ledger":"spot","v2":True,
            "levels":lb._levels(вход, посока),"hit":{},"status":"open",
            "tier":"premium","date":"2026-08-21"}

def пусни(посока, basis, скок):
    t = copy.deepcopy(прясна(посока))          # ЧИСТА сделка всеки път
    _, ev = lb.track_trade(t, bars, basis, SPOT["mid"], "2026-08-21T11:00", spot=SPOT, скок_базис=скок)
    return [(e[0], round(e[1],3), e[3]) for e in ev] or "НЯМА"

for посока in ("long","short"):
    t = прясна(посока)
    print(f"### {посока.upper()} · вход {t['entry']} · нива {t['levels']}")
    print("   A· ЗАМРАЗЕН грешен базис 25.515 (скок_базис=False):", пусни(посока, СТАР, False))
    print("   B· РЕ-АНКЕР верен базис 55.735, ЖИВИЯТ код (скок_базис=True):", пусни(посока, ИСТИНА, True))
    print("   C· РЕ-АНКЕР верен базис 55.735 БЕЗ пазача (скок_базис=False):", пусни(посока, ИСТИНА, False))
    print()
