# -*- coding: utf-8 -*-
"""adv · ПОПРАВЕНА версия на теста «живо срещу потвърдено».

ПЪРВИЯТ МИ ОПИТ БЕШЕ ГРЕШЕН и го казвам на глас: мапнах 15-мин проба с етикет T
към 1-мин бар в момент T и влизах на неговото ЗАТВАРЯНЕ. Но 15-мин бар с етикет T
ЗАТВАРЯ в T+15м (geom_harness.py:247-249) — значи условието се знае едва тогава.
Тоест изтичах 14 минути от самия прозорец, който ражда сигнала. Оттам и абсурдните
+6.10$. Тук пълненето е първият 1-мин бар В ИЛИ СЛЕД T+15м, на ОТВАРЯНЕТО му, от
вярната страна на спреда — точно както прави обученият harness.
"""
import sys, warnings, time
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

SP = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad"
sys.path.insert(0, SP)
import geom_harness as GH
import pyarrow.parquet as pq

t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)
B = GH.load_tape(); n = len(B["dord"])
ГЕОМ = {"name": "доставената", "sl": 20.0,
        "tps": [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], "be_after_tp1": True}
GH.TIME_EXIT_DAYS = 21          # живото правило: 30 календарни дни ≈ 21 търговски

cols = ["timestamp_utc", "high_bid", "low_bid", "close_bid", "high_ask", "low_ask", "close_ask"]
q = pq.read_table(GH.P15MIN, columns=cols).to_pandas().sort_values("timestamp_utc").reset_index(drop=True)
q["h"] = (q.high_bid + q.high_ask) / 2; q["l"] = (q.low_bid + q.low_ask) / 2
q["c"] = (q.close_bid + q.close_ask) / 2
ny = q.timestamp_utc.dt.tz_convert("America/New_York")
q["day"] = (ny + pd.Timedelta(hours=7)).dt.normalize().dt.tz_localize(None)
q["run_h"] = q.groupby("day")["h"].cummax()
q["run_l"] = q.groupby("day")["l"].cummin()
daily = q.groupby("day").agg(close=("c", "last"))
daily["sma50"] = daily["close"].rolling(50).mean().shift(1)     # live `_hist`: завършени дни
daily["sma200"] = daily["close"].rolling(200).mean().shift(1)
X = q.join(daily[["sma50", "sma200"]], on="day")

# ── ПРАВИЛНО пълнене: първият 1-мин бар в или след T+15м ──────────────────────
want = (X.timestamp_utc.values.astype("datetime64[m]") + np.timedelta64(15, "m")).astype(np.int64)
j = np.searchsorted(B["tsmin"], want, side="left")
ok = j < n
gap = np.where(ok, B["tsmin"][np.clip(j, 0, n - 1)] - want, 10**9)
X["fill_i"] = np.where(ok & (gap <= 120), j, -1)
лог(f"проби {len(X):,} · без изпълнимо пълнене {(X['fill_i']<0).sum():,}")


def сделки(idx, посока):
    out = []
    for i0 in idx:
        i0 = int(i0)
        if i0 < 0 or i0 + 1 >= n: continue
        вх = B["oa"][i0] if посока == "long" else B["ob"][i0]   # ОТВАРЯНЕ, вярна страна
        r = GH._one_trade(i0, посока, float(вх), ГЕОМ, B)
        if r is not None: out.append(r["net"])
    return np.array(out)


def ки(x, L, Bn=4000, seed=11):
    m = len(x)
    if m < 8: return (np.nan, np.nan)
    L = min(L, max(2, m // 4)); rng = np.random.default_rng(seed)
    nb = int(np.ceil(m / L))
    st = rng.integers(0, max(m - L + 1, 1), size=(Bn, nb))
    из = (st[:, :, None] + np.arange(L)[None, None, :]).reshape(Bn, -1)[:, :m]
    v = x[np.minimum(из, m - 1)].mean(axis=1)
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


print()
print("=" * 104)
print("ЖИВАТА ВЕРСИЯ (пали по НЕЗАВЪРШЕН дневен бар, както прави ботът) срещу ПОТВЪРДЕНАТА")
print("=" * 104)
print("  Твърдението, което проверявам: «живата е по-лоша, не по-добра» (F25, некерено там).")
print("  Пълнене: първи 1-мин бар след затварянето на 15-мин пробата, на отваряне, лонг=ask.")
print("  Време-изход 21 търговски дни (живото правило). Блоков бутстрап L=21 сделки")
print("  (сделките се застъпват до 21 дни → по-къс блок лъже).")
print()
print(f"  {'събитие':13s} {'вид':14s} {'n':>5s} {'нето':>9s} {'95% (L=21)':>21s} {'95% (L=42)':>21s}  присъда")
рез = {}
for име in ("long_ma50", "short_ma50", "long_ma200", "short_ma200"):
    посока, ma = име.split("_", 1)
    s = X["sma" + ma[2:]]
    ок = s.notna() & (X["fill_i"] >= 0)
    усл = (ок & (X["run_l"] <= s) & (X["c"] > s)) if посока == "long" \
        else (ок & (X["run_h"] >= s) & (X["c"] < s))
    живо = X[усл].groupby("day").first()                  # първото палене за деня
    посл = усл.groupby(X["day"]).last()
    затв = set(посл.index[посл.values])
    групи = (("живо (всички)", живо),
             ("потвърдени", живо[живо.index.isin(затв)]),
             ("отпаднали", живо[~живо.index.isin(затв)]))
    for ет, gg in групи:
        if len(gg) == 0: continue
        x = сделки(gg["fill_i"].to_numpy(), посока)
        if len(x) < 8: continue
        l1, h1 = ки(x, 21); l2, h2 = ки(x, 42)
        пр = "ШУМ" if l2 <= 0 <= h2 else ("ПЕЧЕЛИ" if x.mean() > 0 else "ГУБИ")
        print(f"  {име:13s} {ет:14s} {len(x):5d} {x.mean():+9.3f} [{l1:+9.3f},{h1:+9.3f}] "
              f"[{l2:+9.3f},{h2:+9.3f}]  {пр}")
        рез[(име, ет)] = x
    print()

print("  СВЕРКА с F25 (вход на ЗАТВАРЯНЕ на деня, същата SMA конвенция, 21д):")
print("    long_ma50 -0.047 · short_ma50 -1.976 · long_ma200 -0.087 · short_ma200 -1.913")
лог("готово")
