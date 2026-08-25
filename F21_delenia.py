# -*- coding: utf-8 -*-
"""
F21 · СТЪПКА 3 · ШЕСТТЕ РЕГИСТРИРАНИ ДЕЛЕНИЯ

Критериите са ЗАКОВАНИ в F21_ПРЕДВАРИТЕЛНО.md, преди първото измерване:
  · Bonferroni за 6 теста → иска се 99.17% интервал, не 95%
  · n ≥ 2000 сделки
  · нето ≥ +0.30$/сделка
  · оцелява и в двете епохи (2006-2013 срещу 2014-2026)

Блоков бутстрап ПО ДЕН — сделките в един ден са зависими.
"""
import warnings, json, io
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

T = pd.read_parquet("f21_trades.parquet")
дни = pd.read_parquet("f21_dni.parquet")
T["date"] = pd.to_datetime(T["date"])
T = T.merge(дни[["d20", "r20", "close", "sma50", "atr20"]],
            left_on="date", right_index=True, how="left").dropna(subset=["d20", "r20"])
print(f"сделки: {len(T):,} · дни: {T['date'].nunique():,}")

RNG = np.random.default_rng(21)
_med_atr = T["atr20"].median()


def бутстрап(g, n=4000, дов=99.17):
    """блоков бутстрап ПО ДЕН"""
    if len(g) < 50:
        return None
    по_ден = g.groupby("date")["net"].agg(["sum", "count"])
    S, C = по_ден["sum"].to_numpy(), по_ден["count"].to_numpy()
    k = len(S)
    из = RNG.integers(0, k, size=(n, k))
    ср = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    a = (100 - дов) / 2
    return g["net"].mean(), np.percentile(ср, a), np.percentile(ср, 100 - a), len(g)


ДЕЛЕНИЯ = {
    "1 · кой крак е бичи": {
        "долар↓ лихви↑": (T["d20"] < 0) & (T["r20"] > 0),
        "долар↑ лихви↓": (T["d20"] > 0) & (T["r20"] < 0),
    },
    "2 · сила на несъгласието": {
        "слабо (двата близо 0)": (T["d20"].abs() < T["d20"].abs().median())
                                 & (T["r20"].abs() < T["r20"].abs().median()),
        "силно разнопосочни": (T["d20"].abs() >= T["d20"].abs().median())
                              & (T["r20"].abs() >= T["r20"].abs().median()),
    },
    "3 · режим на златото": {
        "над SMA50": T["close"] > T["sma50"],
        "под SMA50": T["close"] <= T["sma50"],
    },
    "4 · волатилност": {
        "висока ATR20": T["atr20"] > _med_atr,
        "ниска ATR20": T["atr20"] <= _med_atr,
    },
    "5 · сесия": {
        "азия (0-7 UTC)": T["hour"] < 8,
        "европа (8-12)": (T["hour"] >= 8) & (T["hour"] < 13),
        "америка (13-21)": T["hour"] >= 13,
    },
    "6 · посока": {
        "ЛОНГ": T["dir"] == "long",
        "ШОРТ": T["dir"] == "short",
    },
}

print("\n" + "=" * 86)
print("ШЕСТТЕ ДЕЛЕНИЯ · интервалът е 99.17% (Bonferroni за 6 теста)")
print("=" * 86)
print(f"  {'подмножество':26s} {'n':>8s} {'нето':>9s} {'99.17% интервал':>22s}  присъда")
оцелели = []
for име, части in ДЕЛЕНИЯ.items():
    print(f"\n{име}")
    for под, маска in части.items():
        g = T[маска]
        r = бутстрап(g)
        if r is None:
            print(f"  {под:26s} {'малко':>8s}")
            continue
        ср, lo, hi, n = r
        ок = (lo > 0) and (n >= 2000) and (ср >= 0.30)
        пр = "✅ ОЦЕЛЯВА" if ок else ("нулата е вътре" if lo <= 0
                                     else ("n малко" if n < 2000 else "под +0.30$"))
        print(f"  {под:26s} {n:8,d} {ср:+8.3f}$  [{lo:+7.3f} .. {hi:+7.3f}]  {пр}")
        if ок:
            оцелели.append((име, под, маска, ср, lo, n))

print("\n" + "=" * 86)
print(f"ОЦЕЛЕЛИ СЛЕД ПЪРВИТЕ ТРИ КРИТЕРИЯ: {len(оцелели)}")
print("=" * 86)
if not оцелели:
    print("  НИТО ЕДНО → хипотезата е УБИТА, THREAD_ENDS")
else:
    print("\nЧЕТВЪРТИЯТ КРИТЕРИЙ · оцелява ли в ДВЕТЕ епохи?")
    гр = pd.Timestamp("2014-01-01")
    for име, под, маска, ср, lo, n in оцелели:
        g = T[маска]
        a, b = g[g["date"] < гр], g[g["date"] >= гр]
        ra, rb = бутстрап(a), бутстрап(b)
        if not ra or not rb:
            print(f"  {под:26s} една от епохите е празна → пада"); continue
        ok = ra[0] > 0 and rb[0] > 0
        print(f"  {под:26s} 2006-13: {ra[0]:+.3f}$ (n={ra[3]:,})  ·  "
              f"2014-26: {rb[0]:+.3f}$ (n={rb[3]:,})  {'✅ ДВЕТЕ' if ok else '🔴 само едната'}")
