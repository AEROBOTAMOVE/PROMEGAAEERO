# -*- coding: utf-8 -*-
"""
F21 · СТЪПКА 4 · СЪЩАТА ПОПУЛАЦИЯ КАТО БОТА, после пак шестте деления

Предишната стъпка мереше ВСЕКИ кръгъл час в двете посоки. Ботът не прави така:
той избира ЕДНА посока по дъската и влиза само ако класът не е «weak».
Затова числата ми не бяха сравними с официалната клетка.

Тук възпроизвеждам точно това:
    refs   : sma50/sma20/ago5/ago20/low20/high20 от ДНЕВНАТА крива, до ВЧЕРА
    _scores: петте ценови теста + макро-краката, cN = цената в момента на пробата
    _resolve/_tier: буквално както в бота
    вход   : само ако tier != weak

МИНЬОРИТЕ (GDX) ГИ НЯМАМ локално. Но в разбъркано макро доларът и лихвите
задължително са в противоположни посоки → точно ЕДИН от двата крака е бичи.
Значи score = P + 1 (миньорите мечи) или P + 2 (бичи), където P са ценовите
тестове. Прагът за «не-weak» е 4. Тоест:
    P >= 3 → влиза И В ДВАТА случая
    P == 2 → зависи от миньорите
    P <= 1 → не влиза в никой случай
Затова меря ДВЕТЕ граници и гледам дали изводът е един и същ. Това е
проверка на чувствителността, не измисляне на данни.
"""
import warnings, time, json, io
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)

T = pd.read_parquet("f21_trades.parquet")
дни = pd.read_parquet("f21_dni.parquet").copy()
T["date"] = pd.to_datetime(T["date"])
лог(f"сделки {len(T):,} · дни {len(дни):,}")

# ── refs от ДНЕВНАТА крива, изместени с 1 ден (без надничане) ────────────
c = дни["close"]
дни["r_sma50"] = c.rolling(50).mean().shift(1)
дни["r_sma20"] = c.rolling(20).mean().shift(1)
дни["r_ago5"] = c.shift(5 + 1)
дни["r_ago20"] = c.shift(20 + 1)
# low20/high20 искат High/Low — възстановявам ги от atr20 приблизително НЕ;
# вместо това ползвам close-базирани екстремуми, което е по-строго
дни["r_low20"] = c.rolling(20).min().shift(1)
дни["r_high20"] = c.rolling(20).max().shift(1)

T = T.merge(дни[["r_sma50", "r_sma20", "r_ago5", "r_ago20", "r_low20", "r_high20",
                 "d20", "r20", "close", "sma50", "atr20"]],
            left_on="date", right_index=True, how="left").dropna(subset=["r_sma50", "r_ago20"])
лог(f"с пълни refs: {len(T):,}")

# ── петте ценови теста, точно като `_scores` ─────────────────────────────
cN = T["entry"].to_numpy()
lp = np.column_stack([
    cN > T["r_sma50"], cN > T["r_sma20"], cN > T["r_ago20"],
    (cN / T["r_ago5"] - 1 < 0) & (cN / T["r_ago20"] - 1 > 0),
    cN <= T["r_low20"] * 1.015,
]).sum(axis=1)
sp = np.column_stack([
    cN < T["r_sma50"], cN < T["r_sma20"], cN < T["r_ago20"],
    (cN / T["r_ago5"] - 1 > 0) & (cN / T["r_ago20"] - 1 < 0),
    cN >= T["r_high20"] * 0.985,
]).sum(axis=1)
T["P_long"], T["P_short"] = lp, sp

# в mixed: доларът е бичи ⟺ d20 < 0; лихвите са бичи ⟺ r20 < 0; точно едното
дол_бичи = (T["d20"] < 0).to_numpy()
лих_бичи = (T["r20"] < 0).to_numpy()
мл_без = дол_бичи.astype(int) + лих_бичи.astype(int)      # 0..2 без миньорите
мс_без = 2 - мл_без


def популация(миньори_бичи):
    """връща маска: влиза ли ботът, и в коя посока"""
    ml = мл_без + (1 if миньори_бичи else 0)
    ms = мс_без + (0 if миньори_бичи else 1)
    ls = ml + T["P_long"].to_numpy()
    ss = ms + T["P_short"].to_numpy()
    посока = np.where(ls > ss, "long", np.where(ss > ls, "short", "wait"))
    score = np.where(ls > ss, ls, np.where(ss > ls, ss, np.maximum(ls, ss)))
    # в mixed доларът и лихвите СА в противоположни посоки → и трите никога
    tier_ok = (score >= 4) & (посока != "wait")
    return посока, score, tier_ok


ДЕЛЕНИЯ = lambda T: {
    "1 кой крак е бичи": {"долар↓лихви↑": (T["d20"] < 0) & (T["r20"] > 0),
                          "долар↑лихви↓": (T["d20"] > 0) & (T["r20"] < 0)},
    "2 сила на несъгл.": {"слабо": (T["d20"].abs() < T["d20"].abs().median())
                                   & (T["r20"].abs() < T["r20"].abs().median()),
                          "силно": (T["d20"].abs() >= T["d20"].abs().median())
                                   & (T["r20"].abs() >= T["r20"].abs().median())},
    "3 режим на златото": {"над SMA50": T["close"] > T["sma50"],
                           "под SMA50": T["close"] <= T["sma50"]},
    "4 волатилност": {"висока": T["atr20"] > T["atr20"].median(),
                      "ниска": T["atr20"] <= T["atr20"].median()},
    "5 сесия": {"азия": T["hour"] < 8, "европа": (T["hour"] >= 8) & (T["hour"] < 13),
                "америка": T["hour"] >= 13},
    "6 посока": {"ЛОНГ": T["dir"] == "long", "ШОРТ": T["dir"] == "short"},
}

RNG = np.random.default_rng(21)


def бут(g, n=3000, дов=99.17):
    if len(g) < 50: return None
    d = g.groupby("date")["net"].agg(["sum", "count"])
    S, C = d["sum"].to_numpy(), d["count"].to_numpy(); k = len(S)
    из = RNG.integers(0, k, size=(n, k))
    ср = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    a = (100 - дов) / 2
    return g["net"].mean(), np.percentile(ср, a), np.percentile(ср, 100 - a), len(g)


оф = json.load(io.open("backtest_stats.json", encoding="utf-8"))["fresh"]["long"]["mixed"]
for миньори in (True, False):
    пос, score, ок = популация(миньори)
    # ботът влиза само в посоката на дъската
    съвп = (T["dir"].to_numpy() == пос) & ок
    G = T[съвп]
    print()
    print("=" * 84)
    print(f"ПОПУЛАЦИЯТА НА БОТА · миньорите {'БИЧИ' if миньори else 'МЕЧИ'}")
    print("=" * 84)
    гл = G[G["dir"] == "long"]
    r = бут(гл)
    print(f"  лонг в mixed: n={len(гл):,} · нето {гл['net'].mean():+.3f}$"
          + (f" · [{r[1]:+.3f} .. {r[2]:+.3f}]" if r else ""))
    print(f"  ОФИЦИАЛНО   : n={оф.get('n'):,} · нето {оф.get('net'):+.2f}$")
    print(f"  → {'СЪВПАДА по знак ✅' if (гл['net'].mean() < 0) == (оф.get('net',0) < 0) else '🔴 РАЗЛИЧЕН ЗНАК'}")
    if миньори:
        continue
    print()
    print("  ШЕСТТЕ ДЕЛЕНИЯ ВЪРХУ ПОПУЛАЦИЯТА НА БОТА")
    print(f"  {'подмножество':22s} {'n':>7s} {'нето':>9s} {'99.17%':>20s}  присъда")
    оцел = []
    for име, части in ДЕЛЕНИЯ(G).items():
        print(f"  ─ {име}")
        for под, m in части.items():
            g = G[m]; r = бут(g)
            if not r:
                print(f"    {под:20s} малко"); continue
            ср, lo, hi, n = r
            ок2 = (lo > 0) and (n >= 2000) and (ср >= 0.30)
            пр = "✅ ОЦЕЛЯВА" if ок2 else ("нулата вътре" if lo <= 0 else
                                          ("n малко" if n < 2000 else "под +0.30$"))
            print(f"    {под:20s} {n:7,d} {ср:+8.3f}$ [{lo:+7.3f}..{hi:+7.3f}] {пр}")
            if ок2: оцел.append((под, m, ср, n))
    print()
    print(f"  ОЦЕЛЕЛИ: {len(оцел)}")
    if оцел:
        гр = pd.Timestamp("2014-01-01")
        for под, m, ср, n in оцел:
            g = G[m]; a, b = g[g["date"] < гр], g[g["date"] >= гр]
            ra, rb = бут(a), бут(b)
            ok = ra and rb and ra[0] > 0 and rb[0] > 0
            print(f"    {под:20s} 2006-13 {ra[0]:+.3f}$ · 2014-26 {rb[0]:+.3f}$  "
                  f"{'✅ ДВЕТЕ' if ok else '🔴 само едната'}" if ra and rb else f"    {под}: празна епоха")
    else:
        print("    НИТО ЕДНО → F21 THREAD_ENDS")
лог("готово")
