# -*- coding: utf-8 -*-
import sys, io, importlib.util, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd, numpy as np, yfinance as yf, datetime as dt
sys.path.insert(0, "brain")

def _yf(sym, period, interval):
    df = yf.download(sym, period=period, interval=interval, progress=False, auto_adjust=True)
    df.columns = [a if isinstance(a, str) else a[0] for a in df.columns]
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is not None: idx = idx.tz_convert("UTC")
    df.index = idx.tz_localize(None) if idx.tz is not None else idx
    return df.dropna(subset=["Close"])

m1 = _yf("GC=F","7d","1m"); m5 = _yf("GC=F","60d","5m")
src = m5
_bagg = dict(Open=("Open","first"),High=("High","max"),Low=("Low","min"),Close=("Close","last"),Volume=("Volume","sum"))
_bfr = {"1мин": m1, "5м": m5}
for lbl, rule in (("15м","15min"),("1час","60min"),("4час","4h")):
    _bfr[lbl] = src.resample(rule).agg(**_bagg).dropna()

print("СУРОВИ БАРОВЕ:", {k:(len(v) if v is not None else None) for k,v in _bfr.items()})
print("има ли Volume:", {k:("Volume" in v.columns) for k,v in _bfr.items()})

sp = importlib.util.spec_from_file_location("cb","brain/chart_brain.py")
CB = importlib.util.module_from_spec(sp); sp.loader.exec_module(CB)
B6 = CB.B6; SL = CB.SL
now = dt.datetime.utcnow()

setups, diag = CB.сканирай(_bfr, сега=now, състояние={}, работни=("1мин","5м","15м"), праг=14, върни_диагностика=True)
print("\nРАМКИ след чистене:", json.dumps(diag["рамки"], ensure_ascii=False, indent=1))
print("ГРЕШКИ:", diag["грешки"])
print("БЕЛЕЖКИ:", [b for b in diag["бележки"]])

# ── директно: групата ОБЕМИ на всяка работна рамка, БЕЗ изкуствен вход ──
print("\n=== РЕАЛЕН ОБЕМ, БЕЗ ПИПАНЕ ===")
for име in ("1мин","5м","15м","1час"):
    d,_ = CB._подготви(_bfr[име], име)
    d,_ = CB._отрежи_незатворен(d, име, now)
    d = d.iloc[-CB.ПРОЗОРЕЦ:]
    R = B6.f_относителен_обем(d)
    отн = R["отн"]; мета = R["мета"]
    дни = (d.index[-1]-d.index[0]).total_seconds()/86400
    ск = B6.f_обемен_скок(d)
    print(f"{име:5s} барове={len(d)} календ.дни={дни:5.2f} слотове={мета['слотове']:4d} "
          f"готови_отн={мета['готови']:5d} ({мета['дял_готови']*100:5.1f}%) "
          f"отн[-1]={отн[-1] if np.isfinite(отн[-1]) else float('nan'):.3f} скокове={len(ск['скокове'])}")

# ── какво вижда СЛИВАНЕТО: групата Ж по рамки ──
print("\n=== ГРУПА Ж (ОБЕМИ) ПРЕЗ РЕАЛНИЯ ПЪТ НА КОДА ===")
for име in ("1мин","5м","15м"):
    d,_ = CB._подготви(_bfr[име], име)
    d,_ = CB._отрежи_незатворен(d, име, now)
    d = d.iloc[-CB.ПРОЗОРЕЦ:]
    R,вр,гр = CB._прочети(d, име)
    V = R["обем"]
    карти = SL.f_сливане(d, R, праг_карта=0)
    ж = {k:v for k,v in (карти[0]["всички_условия"].items() if карти else {}.items())
         if k.startswith(("J1","J1b","J2"))}
    print(f"{име:5s} отн_сега={V['отн_сега']}  последен_скок={'има' if V['последен_скок'] else 'НЯМА'}  Ж={ж}")

# ── КОЛКО ЧЕСТО Ж ИЗОБЩО ДАВА ТОЧКИ НА 15м (историческа честота) ──
print("\n=== ЧЕСТОТА НА Ж НА 15м (1200 бара, всеки бар) ===")
d15,_ = CB._подготви(_bfr["15м"], "15м"); d15 = d15.iloc[-CB.ПРОЗОРЕЦ:]
R = B6.f_относителен_обем(d15); отн = R["отн"]
ск = B6.f_обемен_скок(d15)
барове_скок = set(e["бар"] for e in ск["скокове"])
ok = np.isfinite(отн)
j1 = (ok & (отн>=1.5)).sum(); j1b = (ok & (отн>=2.5)).sum()
print(f"барове с готова база: {ok.sum()}/{len(отн)}")
print(f"J1 (>=1.5x) верен на {j1} бара = {j1/len(отн)*100:.1f}%")
print(f"J1b(>=2.5x) верен на {j1b} бара = {j1b/len(отн)*100:.1f}%")
print(f"J2 скок-барове: {len(барове_скок)} = {len(барове_скок)/len(отн)*100:.1f}%")
среден_ж = sum(min(3,(1 if (ok[i] and отн[i]>=1.5) else 0)+(1 if (ok[i] and отн[i]>=2.5) else 0)+(1 if i in барове_скок else 0)) for i in range(len(отн)))/len(отн)
print(f"СРЕДЕН ПРИНОС на Ж за произволен бар на 15м: {среден_ж:.3f} точки от таван 3")
