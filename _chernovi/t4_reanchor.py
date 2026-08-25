# -*- coding: utf-8 -*-
"""КАКВО ПРАВИ САМИЯТ ОТКЛЮЧВАЩ ПРЕКЪСВАЧ С ОТВОРЕНА СДЕЛКА.
track_trade съди баровете с ТЕКУЩИЯ базис, а нивата на сделката са замразени
на базиса ОТ ОТВАРЯНЕТО. 🔓 ре-анкерът мести базиса с един скок."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE)
import os; os.chdir(BASE)
import live_bot as lb
import pandas as pd, numpy as np

# ЖИВИ ЧИСЛА от live/meta.json (21.08)
СТАР = 25.515          # замразеният базис
ИСТИНА = 4647.2 - 4591.465   # basis_g_bar - last_spot_g
print(f"замразен базис={СТАР}  ·  истински (бар {4647.2} − спот {4591.465})={ИСТИНА:.3f}"
      f"  ·  скок={ИСТИНА-СТАР:+.2f}$")

# 5-мин барове около живия бар, ПЛОСКИ (пазарът не мърда)
idx = pd.date_range("2026-08-21T10:00", periods=12, freq="5min")
bars = pd.DataFrame({"Open": [4647.2]*12, "High": [4648.0]*12,
                     "Low": [4646.4]*12, "Close": [4647.2]*12}, index=idx)

def нова_сделка(basis):
    вход = round(4647.2 - basis, 2)
    return {"direction": "long", "entry": вход, "opened": "2026-08-21T09:55",
            "checked": "2026-08-21T09:59", "ledger": "spot", "v2": True,
            "levels": {"sl": round(вход - 10, 2), "tp1": round(вход + 5, 2),
                       "tp2": round(вход + 10, 2), "tp3": round(вход + 15, 2)},
            "hit": {}, "status": "open", "tier": "premium", "date": "2026-08-21"}

print()
print("=== A · базисът НЕ мърда (25.515) — сделката е жива ===")
t = нова_сделка(СТАР)
print("   нива:", t["levels"])
t2, ev = lb.track_trade(dict(t), bars, СТАР, 4647.2-СТАР, "2026-08-21T11:00",
                        spot={"mid": 4647.2-СТАР, "bid": 4647.0-СТАР, "ask": 4647.4-СТАР})
print("   събития:", [e[0] for e in ev] or "НЯМА — сделката стои")

print()
print("=== B · СЪЩИЯТ бар, но прекъсвачът току-що ре-анкерва базиса на 55.735 ===")
t3, ev3 = lb.track_trade(dict(t), bars, ИСТИНА, 4647.2-ИСТИНА, "2026-08-21T11:00",
                         spot={"mid": 4647.2-ИСТИНА, "bid": 4647.0-ИСТИНА, "ask": 4647.4-ИСТИНА})
print("   баровете вече се четат като:", round(4648.0-ИСТИНА, 2), "/", round(4646.4-ИСТИНА, 2))
print("   стопът на сделката е:", t["levels"]["sl"])
print("   събития:", [(e[0], e[1]) for e in ev3] or "НЯМА")
print("   -> пазарът НЕ е мръднал НИТО ЦЕНТ; изходът идва от смяната на базиса")

print()
print("=== C · и обратната посока (шорт) ===")
ts = dict(нова_сделка(СТАР)); ts["direction"] = "short"
вход = ts["entry"]
ts["levels"] = {"sl": round(вход+10, 2), "tp1": round(вход-5, 2),
                "tp2": round(вход-10, 2), "tp3": round(вход-15, 2)}
t4, ev4 = lb.track_trade(dict(ts), bars, ИСТИНА, 4647.2-ИСТИНА, "2026-08-21T11:00",
                         spot={"mid": 4647.2-ИСТИНА, "bid": 4647.0-ИСТИНА, "ask": 4647.4-ИСТИНА})
print("   шорт вход", вход, "цели", ts["levels"])
print("   събития:", [(e[0], e[1]) for e in ev4] or "НЯМА")

print()
print("=== D · има ли в кода ре-базиране на нивата при смяна на базиса? ===")
src = open("live_bot.py", encoding="utf-8").read()
блок = src[src.index("def _migrate_trade"):src.index("# ---------- пощенска кутия")]
print("   _migrate_trade се изпълнява само веднъж:", '"ledger") == "spot"' in блок)
print("   пази ли се базисът, с който е отворена сделката?",
      "basis" in json.dumps(list(нова_сделка(СТАР).keys())))
print("   ключове на сделката:", sorted(нова_сделка(СТАР).keys()))
