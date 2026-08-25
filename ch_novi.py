# -*- coding: utf-8 -*-
import sys, io, json
sys.argv = ["x"]
import live_bot as lb
import pandas as pd

STATS = json.load(io.open("backtest_stats.json", encoding="utf-8"))
PIP = lb.PIP

# ---- помощни, каквито предлагам да влязат в кода ----
ВЪЗРАСТ_ВХОД = ((6, 0.231), (12, 0.052), (24, -1.590), (48, -0.681), (10**9, -1.219))
ДНИ_МАКС = 30

def _възраст_нето(age_h):
    for праг, нето in ВЪЗРАСТ_ВХОД:
        if age_h < праг:
            return нето
    return ВЪЗРАСТ_ВХОД[-1][1]

def _от_10(win):
    return round(float(win) / 10.0)

def _ден_от(opened, now_utc):
    try:
        return (pd.Timestamp(now_utc) - pd.Timestamp(opened)).days + 1
    except Exception:
        return None

def _мерено_редове(t):
    """t = _gate_trace['мерено'] = {кофа,win,net,n,lo,hi}"""
    L = []
    if not t or not t.get("n"):
        return L
    L.append(f"📊 такава нагласа се е случвала {t['n']:,} пъти · "
             f"{t['win']:.1f}% от тях са свършили на плюс".replace(",", " "))
    L.append(f"📈 средно {lb._пари(t['net'])} на сделка")
    if t.get("lo") is not None and t.get("hi") is not None:
        L.append(f"📐 честната граница на това средно е "
                 f"{t['lo']/PIP:+,.0f} до {t['hi']/PIP:+,.0f} пипса"
                 .replace("+", "+").replace(",", " "))
    L.append("⚠️ това е средно от много сделки · ТАЗИ може да удари стопа")
    return L

t = STATS["fresh"]["long"]["day1"]
tr = {"кофа": "пресен ден-1", "win": t["win"], "net": t["net"], "n": t["n"],
      "lo": t["lo"], "hi": t["hi"]}
for r in _мерено_редове(tr):
    print(r)
print("---")
for a in (3, 8, 14, 30, 70):
    print(a, "ч →", lb._пари(_възраст_нето(a)))
