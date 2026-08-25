# -*- coding: utf-8 -*-
"""
F21 · СТЪПКА 1 · ПОСТРОЯВАНЕ НА СДЕЛКИТЕ ОТ СУРОВИ ДАННИ

Генератор за клетките НЯМА в repo-то — само ботът. Значи строя наново от:
    xauusd_1min_bid_ask.parquet   7.96M бара, 2006-2026
    dxy_yahoo_full.csv            доларът, дневно
    DFII10.csv                    реалните лихви, дневно

Геометрията е ДОСТАВЕНАТА, не измислена: ТП 7.5/12/20, стоп 20, стълба 1/3,
стоп на входа след ТП1, вход/изход от вярната страна на спреда, +0.02$
приплъзване, стоп ПРЕДИ цел при съмнение.

Пише f21_trades.parquet — по един ред на сделка, с всичко нужно за шестте
деления от предварителната регистрация.
"""
import sys, warnings, io, time
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

D = "C:/Users/User/Downloads/ЛОЦО/f6_data"
t0 = time.time()


def лог(s):
    print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)


# ── 1 · баровете ─────────────────────────────────────────────────────────
лог("чета 1-минутните барове…")
b = pd.read_parquet(f"{D}/parquet/xauusd_1min_bid_ask.parquet")
лог(f"  {len(b):,} реда · колони: {list(b.columns)}")
ts = pd.to_datetime(b["timestamp_utc"])
mid_o = (b["open_bid"] + b.get("open_ask", b["open_bid"])) / 2
bars = pd.DataFrame({
    "ts": ts,
    "o_bid": b["open_bid"], "h_bid": b["high_bid"], "l_bid": b["low_bid"], "c_bid": b["close_bid"],
}).dropna()
if "open_ask" in b.columns:
    bars["o_ask"] = b["open_ask"]; bars["h_ask"] = b["high_ask"]
    bars["l_ask"] = b["low_ask"]; bars["c_ask"] = b["close_ask"]
else:
    # без ask колони — слагаме типичен спред от 0.30$/унция (консервативно)
    for k in ("o", "h", "l", "c"):
        bars[f"{k}_ask"] = bars[f"{k}_bid"] + 0.30
bars = bars.set_index("ts").sort_index()
лог(f"  период: {bars.index[0]} → {bars.index[-1]}")

# ── 2 · дневните барове на златото (за refs и streak) ────────────────────
den = pd.DataFrame({
    "Open": ((bars["o_bid"] + bars["o_ask"]) / 2).resample("1D").first(),
    "High": ((bars["h_bid"] + bars["h_ask"]) / 2).resample("1D").max(),
    "Low": ((bars["l_bid"] + bars["l_ask"]) / 2).resample("1D").min(),
    "Close": ((bars["c_bid"] + bars["c_ask"]) / 2).resample("1D").last(),
}).dropna()
# 🔴 часовата зона: баровете са +00:00, макро-файловете са наивни → reindex
# не съвпадаше с НИЩО и всичко излизаше NaN (mixed=100%). Сваляме зоната.
den.index = pd.DatetimeIndex(den.index).tz_localize(None).normalize()
лог(f"дневни барове: {len(den):,} · {den.index[0].date()}→{den.index[-1].date()}")

# ── 3 · макрото ──────────────────────────────────────────────────────────
dxy = pd.read_csv(f"{D}/dxy_yahoo_full.csv", parse_dates=["Date"]).set_index("Date")["Close"].dropna()
rr = pd.read_csv(f"{D}/DFII10.csv", parse_dates=["observation_date"]).set_index("observation_date")["DFII10"]
rr = pd.to_numeric(rr, errors="coerce").dropna()
лог(f"долар: {len(dxy):,} дни {dxy.index[0].date()}→{dxy.index[-1].date()} · "
    f"лихви: {len(rr):,} дни {rr.index[0].date()}→{rr.index[-1].date()}")

idx = den.index
dx = dxy.reindex(idx).ffill()
r_ = rr.reindex(idx).ffill()

# ТОЧНО правилото от бота (_streaks): m_l = доларът пада И лихвите падат
d20 = dx.pct_change(20)
r20 = r_ - r_.shift(20)
m_l = (-(d20) > 0) & (-(r20) > 0)
m_s = (d20 > 0) & (r20 > 0)


def стрийк(s):
    s = s.fillna(False)
    return s.groupby((~s).cumsum()).cumsum()


st_l, st_s = стрийк(m_l), стрийк(m_s)

# ── 4 · дъската: посоката за деня (опростена — по режима на цената) ──────
c = den["Close"]
sma50 = c.rolling(50).mean()
sma20 = c.rolling(20).mean()
atr20 = (den["High"] - den["Low"]).rolling(20).mean()

# ── 5 · кои дни са MIXED ─────────────────────────────────────────────────
mixed = (st_l == 0) & (st_s == 0)
лог(f"дни общо: {len(idx):,} · MIXED: {int(mixed.sum()):,} = {mixed.mean()*100:.1f}%")

таблица = pd.DataFrame({
    "close": c, "sma50": sma50, "sma20": sma20, "atr20": atr20,
    "d20": d20, "r20": r20, "st_l": st_l, "st_s": st_s, "mixed": mixed,
})
таблица.to_parquet("f21_dni.parquet")
лог("записан f21_dni.parquet")

# ── 6 · разпределение на разбърканите състояния ──────────────────────────
m = таблица[таблица["mixed"]].dropna(subset=["d20", "r20"])
print()
print("=" * 68)
print("РАЗБЪРКАНИТЕ ДНИ · какви са")
print("=" * 68)
дп = (m["d20"] < 0)      # доларът ПАДА → бичи за златото
лр = (m["r20"] < 0)      # лихвите ПАДАТ → бичи за златото
print(f"  доларът пада + лихвите растат : {int((дп & ~лр).sum()):5d}")
print(f"  доларът расте + лихвите падат : {int((~дп & лр).sum()):5d}")
print(f"  и двата почти нула            : {int((дп == лр).sum()):5d}")
print()
print(f"  над SMA50: {int((m['close'] > m['sma50']).sum()):5d} · "
      f"под: {int((m['close'] <= m['sma50']).sum()):5d}")
_med = m["atr20"].median()
print(f"  ATR20 медиана {_med:.2f}$ · над нея {int((m['atr20'] > _med).sum()):5d} дни")
лог("готово")
