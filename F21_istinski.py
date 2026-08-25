# -*- coding: utf-8 -*-
"""
F21 · ФИНАЛ · шестте деления върху ИСТИНСКИТЕ 114 813 сделки

Генераторът се намери: scratchpad/CELLS_NM.py + SPLIT_pnl.parquet (04.08).
Това е СЪЩАТА популация, от която са дошли официалните клетки — с `tier`,
`score`, `actionable`, `streak`, `board`. Моята реконструкция вече не е нужна.

Критериите са от F21_ПРЕДВАРИТЕЛНО.md, непроменени:
  Bonferroni за 6 теста → 99.17% интервал · n ≥ 2000 · нето ≥ +0.30$ ·
  оцелява в двете епохи.
"""
import warnings, json, io
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

SP = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad"
DATA = r"C:\Users\User\Downloads\ЛОЦО\f6_data"

E = pd.read_parquet(SP + r"\SPLIT_pnl.parquet")
print(f"сделки: {len(E):,} · варианти: {E['variant'].unique().tolist()}")
E = E[E["variant"] == "СЕГА"].copy()
E["day"] = pd.to_datetime(E["day"]).dt.tz_localize(None)
print(f"вариант СЕГА: {len(E):,} · {E['day'].min().date()} → {E['day'].max().date()}")

# ── макрото, по СЪЩИЯ начин като в генератора ────────────────────────────
def dc(p):
    d = pd.read_csv(p)
    c = [x for x in d.columns if x.lower() in ("date", "datetime", "time", "observation_date")][0]
    d[c] = pd.to_datetime(d[c], errors="coerce")
    v = [x for x in d.columns if x.lower() in ("close", "adj close", "value", "dfii10", "price")][0]
    d = d[[c, v]].dropna(); d[v] = pd.to_numeric(d[v], errors="coerce")
    return d.dropna().set_index(c)[v].sort_index()

дни_idx = pd.DatetimeIndex(sorted(E["day"].unique()))
dx = dc(DATA + r"\dxy_yahoo_full.csv").reindex(дни_idx, method="ffill")
rr = dc(DATA + r"\DFII10.csv").reindex(дни_idx, method="ffill")
ctx = pd.DataFrame({"d20": dx.pct_change(20), "r20": rr - rr.shift(20)}, index=дни_idx)

# режим и вола на златото — от самите входни цени
пц = E.groupby("day")["close_mid"].last().reindex(дни_idx).ffill()
ctx["close"] = пц
ctx["sma50"] = пц.rolling(50).mean()
ctx["atr20"] = пц.diff().abs().rolling(20).mean()

E = E.merge(ctx, left_on="day", right_index=True, how="left")
E["hour"] = pd.to_datetime(E["entry_utc"]).dt.hour
E = E.dropna(subset=["d20", "r20"])

# КЛЕТКАТА mixed = стрийк 0, точно както `_cell_name`
M = E[E["streak"] == 0].copy()
print(f"\nmixed: {len(M):,} сделки · {M['day'].nunique():,} дни")
for d in ("long", "short"):
    g = M[M["direction"] == d]
    print(f"  {d:5s} n={len(g):6,d} нето {g['pnl'].mean():+.3f}$")

оф = json.load(io.open("backtest_stats.json", encoding="utf-8"))["fresh"]
print(f"\n  ОФИЦИАЛНО long/mixed: n={оф['long']['mixed']['n']:,} "
      f"нето {оф['long']['mixed']['net']:+.2f}$")
_мое = M[M['direction'] == 'long']['pnl'].mean()
print(f"  МОЕТО СЕГА          : n={len(M[M['direction']=='long']):,} нето {_мое:+.2f}$")
print(f"  → {'СЪВПАДА ✅' if abs(_мое - оф['long']['mixed']['net']) < 0.15 else '🔴 РАЗЛИЧНО'}")

RNG = np.random.default_rng(21)


def бут(g, R=4000, дов=99.17):
    if len(g) < 50: return None
    d = g.groupby("day")["pnl"].agg(["sum", "count"])
    S, C = d["sum"].to_numpy(), d["count"].to_numpy(); k = len(S)
    из = RNG.integers(0, k, size=(R, k))
    ср = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    a = (100 - дов) / 2
    return g["pnl"].mean(), np.percentile(ср, a), np.percentile(ср, 100 - a), len(g)


_md, _mr, _ma = M["d20"].abs().median(), M["r20"].abs().median(), M["atr20"].median()
ДЕЛЕНИЯ = {
    "1 кой крак е бичи": {"долар↓ лихви↑": (M["d20"] < 0) & (M["r20"] > 0),
                          "долар↑ лихви↓": (M["d20"] > 0) & (M["r20"] < 0)},
    "2 сила на несъгласието": {"слабо": (M["d20"].abs() < _md) & (M["r20"].abs() < _mr),
                               "силно": (M["d20"].abs() >= _md) & (M["r20"].abs() >= _mr)},
    "3 режим на златото": {"над SMA50": M["close"] > M["sma50"],
                           "под SMA50": M["close"] <= M["sma50"]},
    "4 волатилност": {"висока": M["atr20"] > _ma, "ниска": M["atr20"] <= _ma},
    "5 сесия": {"азия": M["hour"] < 8, "европа": (M["hour"] >= 8) & (M["hour"] < 13),
                "америка": M["hour"] >= 13},
    "6 посока": {"ЛОНГ": M["direction"] == "long", "ШОРТ": M["direction"] == "short"},
}

print("\n" + "=" * 84)
print("ШЕСТТЕ ДЕЛЕНИЯ · ИСТИНСКИТЕ ДАННИ · 99.17% (Bonferroni)")
print("=" * 84)
оцел = []
for име, части in ДЕЛЕНИЯ.items():
    print(f"\n{име}")
    for под, m in части.items():
        g = M[m]; r = бут(g)
        if not r:
            print(f"  {под:16s} малко"); continue
        ср, lo, hi, n = r
        ок = (lo > 0) and (n >= 2000) and (ср >= 0.30)
        пр = "✅ ОЦЕЛЯВА" if ок else ("нулата вътре" if lo <= 0 else
                                     ("n малко" if n < 2000 else "под +0.30$"))
        print(f"  {под:16s} {n:7,d} {ср:+8.3f}$  [{lo:+7.3f} .. {hi:+7.3f}]  {пр}")
        if ок: оцел.append((под, m, ср, n))

print("\n" + "=" * 84)
print(f"ОЦЕЛЕЛИ СЛЕД ТРИТЕ КРИТЕРИЯ: {len(оцел)}")
print("=" * 84)
if not оцел:
    print("  НИТО ЕДНО → F21 THREAD_ENDS · клетката остава затворена")
else:
    гр = pd.Timestamp("2014-01-01")
    for под, m, ср, n in оцел:
        g = M[m]; a, b = g[g["day"] < гр], g[g["day"] >= гр]
        ra, rb = бут(a), бут(b)
        if not (ra and rb):
            print(f"  {под:16s} празна епоха → пада"); continue
        ok = ra[0] > 0 and rb[0] > 0
        print(f"  {под:16s} 2006-13 {ra[0]:+.3f}$ (n={ra[3]:,}) · "
              f"2014-26 {rb[0]:+.3f}$ (n={rb[3]:,})  {'✅ ДВЕТЕ' if ok else '🔴 само едната'}")
