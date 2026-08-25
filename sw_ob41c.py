# -*- coding: utf-8 -*-
"""Базисът в дневника НЕ е чист фючърс−спот: барът на бота е на 10-15 мин назад,
значи basis поглъща и дрейфа. Тук базисът се смята ПО ВРЕМЕ СЪВПАДНАЛИ двойки:
Close на 5м бара, който съдържа рън-а, минус живия спот от същия рън."""
import sys, io, json, os
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd, numpy as np
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, "sw_ob41.py"), encoding="utf-8").read().split("def scal(")[0])

# --- контрол: journal basis наистина ли е bar−spot? ---
chk = [(x["bar"] - x["spot"]) - x["basis"] for x in J
       if x.get("spot") is not None and x.get("bar") is not None and x.get("basis") is not None]
chk = pd.Series(chk)
print("\n(bar−spot) − basis в дневника: медиана %+.2f  |.| p90 %.2f  → базисът НЕ е чист bar−spot"
      % (chk.median(), chk.abs().quantile(.9)))

# --- нов, изравнен по време базис ---
pairs = {}
for ts, r in S.iterrows():
    bt = ts.floor("5min")
    if bt in B.index and not pd.isna(B.loc[bt, "Close"]):
        pairs.setdefault(bt, []).append(float(B.loc[bt, "Close"]) - float(r["pu"]))
pb = pd.Series({k: np.median(v) for k, v in pairs.items()}).sort_index()
pb = pb.rolling(9, center=True, min_periods=1).median()          # изглаждане на трепкането
BAS2 = pb.reindex(B.index).interpolate(limit_direction="both")
print("изравнен базис: медиана %.2f  стд %.2f" % (BAS2.median(), BAS2.std()))

res2 = []
for ts, r in S.iterrows():
    bt = ts.floor("5min")
    if bt in B.index and not pd.isna(B.loc[bt, "Close"]):
        res2.append(float(B.loc[bt, "Close"]) - float(BAS2.loc[bt]) - float(r["pu"]))
res2 = pd.Series(res2)
print("РЕЗИДУАЛ с изравнен базис, %d двойки: |.| медиана %.2f  p90 %.2f  p99 %.2f"
      % (len(res2), res2.abs().median(), res2.abs().quantile(.9), res2.abs().quantile(.99)))
ГРЕШКА = res2.abs().quantile(.9)

def barw(rec, BASX):
    зн = 1 if rec["посока"] == "long" else -1
    t0, t1 = pd.Timestamp(rec["отворен"]), pd.Timestamp(rec["затворен"])
    ц1 = False
    sub = B.loc[(B.index > t0) & (B.index <= t1)]
    дълб = 0.0
    for ts, r in sub.iterrows():
        hi = float(r["High"]) - float(BASX.loc[ts]); lo = float(r["Low"]) - float(BASX.loc[ts])
        if pd.isna(hi) or pd.isna(lo):
            continue
        d = (rec["стоп"] - lo) if зн == 1 else (hi - rec["стоп"])
        if d >= 0:
            return ("стоп", ts, d)
        дълб = max(дълб, d)
        if rec.get("цел2") is not None and ((hi >= rec["цел2"]) if зн == 1 else (lo <= rec["цел2"])):
            return ("цел2", ts, дълб)
        if not ц1 and ((hi >= rec["цел1"]) if зн == 1 else (lo <= rec["цел1"])):
            ц1 = True
    return (None, None, дълб)

print("\n%-3s %-5s %-17s %-6s %8s | %-6s %-17s %8s  присъда" %
      ("№", "пос", "отворен", "запис", "резултат", "по бар", "кога", "дълбочина"))
жив = сив = 0
for i, rec in enumerate(R, 1):
    k, ts, d = barw(rec, BAS2)
    ин = ""
    if k != rec["изход"]:
        if d >= ГРЕШКА:
            ин = "⚠ РАЗЛИКА над грешката"; жив += 1
        else:
            ин = "~ разлика ПОД грешката (%.2f < %.2f)" % (d, ГРЕШКА); сив += 1
    print("%-3d %-5s %-17s %-6s %+8.2f | %-6s %-17s %8.2f  %s"
          % (i, rec["посока"], rec["отворен"], rec["изход"], rec["резултат"],
             str(k), str(ts)[:16], d, ин))
print("\nразлики над шума на измерването: %d/%d   разлики в шума: %d/%d" % (жив, len(R), сив, len(R)))
