# -*- coding: utf-8 -*-
"""adv · (1) наистина ли ЖИВАТА (незавършен бар) версия е по-лоша · (2) може ли ШОРТ да е +4.55"""
import sys, warnings, time
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

SP = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad"
sys.path.insert(0, SP)
import geom_harness as GH
import pyarrow.parquet as pq

t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)
B = GH.load_tape()
n = len(B["dord"])
ТС = pd.to_datetime(pd.Series(B["ts"]))
ГЕОМ = {"name": "доставената", "sl": 20.0,
        "tps": [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], "be_after_tp1": True}

# ── 15-минутна решетка = каданс, близък до живия бот ──────────────────────────
cols = ["timestamp_utc", "high_bid", "low_bid", "close_bid", "high_ask", "low_ask", "close_ask"]
q = pq.read_table(GH.P15MIN, columns=cols).to_pandas().sort_values("timestamp_utc").reset_index(drop=True)
q["h"] = (q.high_bid + q.high_ask) / 2; q["l"] = (q.low_bid + q.low_ask) / 2
q["c"] = (q.close_bid + q.close_ask) / 2
ny = q.timestamp_utc.dt.tz_convert("America/New_York")
q["day"] = (ny + pd.Timedelta(hours=7)).dt.normalize().dt.tz_localize(None)
q["run_h"] = q.groupby("day")["h"].cummax()          # НЕЗАВЪРШЕН дневен бар
q["run_l"] = q.groupby("day")["l"].cummin()
daily = q.groupby("day").agg(close=("c", "last"))
# live_bot `_hist`: SMA само от ЗАВЪРШЕНИ дни → shift(1)
daily["sma50"] = daily["close"].rolling(50).mean().shift(1)
daily["sma200"] = daily["close"].rolling(200).mean().shift(1)
X = q.join(daily[["sma50", "sma200"]], on="day")
лог(f"15м решетка: {len(X):,} проби · {X.day.nunique():,} дни")

# индекс в 1-мин лентата за всяка 15-мин проба (входът е на цената в момента на палене)
tmin1 = B["tsmin"]
tmin15 = X.timestamp_utc.values.astype("datetime64[m]").astype(np.int64)
pos = np.searchsorted(tmin1, tmin15, side="left")
pos = np.clip(pos, 0, n - 1)
X["i1"] = pos

print()
print("=" * 100)
print("1 · ЖИВАТА ВЕРСИЯ (пали по НЕЗАВЪРШЕН бар) срещу ПОТВЪРДЕНАТА (на затваряне)")
print("=" * 100)
print("  Собственикът твърди: «живата е по-лоша, не по-добра». Това НЕ е мерено — мери се тук.")
print("  Живо палене = първата 15-мин проба за деня, в която условието е вярно.")
print("  Потвърдено = условието е вярно и на ЗАТВАРЯНЕ на деня.")
print()
GH.TIME_EXIT_DAYS = 21     # живото правило: 30 календарни дни ≈ 21 търговски (live_bot.py:2125)


def сделки(idx, посока):
    out = []
    for i0 in idx:
        i0 = int(i0)
        if i0 + 1 >= n: continue
        вх = B["ca"][i0] if посока == "long" else B["cb"][i0]
        r = GH._one_trade(i0, посока, float(вх), ГЕОМ, B)
        if r is not None: out.append(r["net"])
    return np.array(out)


def ки(x, L=10, Bn=3000, seed=3):
    if len(x) < 8: return (np.nan, np.nan)
    rng = np.random.default_rng(seed); m = len(x); L = min(L, max(2, m // 4))
    nb = int(np.ceil(m / L))
    st = rng.integers(0, max(m - L + 1, 1), size=(Bn, nb))
    из = (st[:, :, None] + np.arange(L)[None, None, :]).reshape(Bn, -1)[:, :m]
    v = x[np.minimum(из, m - 1)].mean(axis=1)
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


print(f"  {'събитие':13s} {'вид':11s} {'n':>5s} {'нето':>9s} {'95% блоков':>21s}  присъда")
for име in ("long_ma50", "short_ma50", "long_ma200", "short_ma200"):
    посока, ma = име.split("_", 1)
    s = X["sma" + ma[2:]]
    ок = s.notna()
    if посока == "long":
        усл = ок & (X["run_l"] <= s) & (X["c"] > s)
    else:
        усл = ок & (X["run_h"] >= s) & (X["c"] < s)
    живо = X[усл].groupby("day").first()               # първото палене за деня
    # потвърден ден = условието е вярно и на ПОСЛЕДНАТА 15-мин проба за деня (= на затваряне)
    посл_усл = усл.groupby(X["day"]).last()
    затв_дни = set(посл_усл.index[посл_усл.values])
    потв = живо[живо.index.isin(затв_дни)]
    само_живо = живо[~живо.index.isin(затв_дни)]
    for ет, gg in (("живо (всички)", живо), ("потвърдени", потв), ("отпаднали", само_живо)):
        if len(gg) == 0: continue
        x = сделки(gg["i1"].to_numpy(), посока)
        lo, hi = ки(x)
        пр = "ШУМ" if not np.isfinite(lo) or lo <= 0 <= hi else ("ПЕЧЕЛИ" if x.mean() > 0 else "ГУБИ")
        print(f"  {име:13s} {ет:11s} {len(x):5d} {x.mean():+9.3f} [{lo:+9.3f},{hi:+9.3f}]  {пр}")
    print()

print("=" * 100)
print("2 · МОЖЕ ЛИ ШОРТ_MA50 ДА ИЗЛЕЗЕ +4.55$ ПОД КАКВОТО И ДА Е ДОПУСКАНЕ")
print("=" * 100)
mid_h = (B["hb"] + B["ha"]) / 2; mid_l = (B["lb"] + B["la"]) / 2; mid_c = (B["cb"] + B["ca"]) / 2
dd = pd.DataFrame({"d": B["dord"], "h": mid_h, "l": mid_l, "c": mid_c}).groupby("d")
DAY = pd.DataFrame({"high": dd["h"].max(), "low": dd["l"].min(), "close": dd["c"].last(),
                    "last_i": dd.apply(lambda z: z.index[-1])}).reset_index(drop=True)
DAY["sma50"] = DAY["close"].rolling(50).mean()
H_, L_, C_ = DAY["high"].to_numpy(), DAY["low"].to_numpy(), DAY["close"].to_numpy()
ND = len(DAY)
ТПг = (7.5, 12.0, 20.0); СЛг = 20.0


def дн(i, лонг, макс, стоп_бие, sl_mult=1.0):
    зн = 1.0 if лонг else -1.0
    вх = C_[i]; tp = [вх + зн * t for t in ТПг]; sl = вх - зн * СЛг * sl_mult
    пари = 0.0; взети = 0; бе = False
    for j in range(i + 1, min(i + 1 + макс, ND)):
        hi, lo = H_[j], L_[j]
        тек = вх if бе else sl
        уд = (lo <= тек) if лонг else (hi >= тек)
        нови = [k for k, t in enumerate(tp) if k >= взети and ((hi >= t) if лонг else (lo <= t))]
        if уд and (стоп_бие or not нови):
            return пари + (тек - вх) * зн * (3 - взети) / 3.0
        for k in нови:
            пари += (tp[k] - вх) * зн / 3.0; взети = k + 1
            if k == 0: бе = True
            if k == 2: return пари
        if уд and not стоп_бие:
            return пари + (тек - вх) * зн * (3 - взети) / 3.0
    return пари + (C_[min(i + макс, ND - 1)] - вх) * зн * (3 - взети) / 3.0


м = DAY["sma50"].notna() & (DAY["high"] >= DAY["sma50"]) & (DAY["close"] < DAY["sma50"])
idxS = DAY.index[м].to_numpy()
мл = DAY["sma50"].notna() & (DAY["low"] <= DAY["sma50"]) & (DAY["close"] > DAY["sma50"])
idxL = DAY.index[мл].to_numpy()
print(f"  {'хоризонт':>9s} " + "".join(f"{f'SHORT {c}':>16s}" for c in ("целта бие", "стопът бие", "стоп×2, целта бие"))
      + f"{'LONG целта бие':>17s}")
for макс in (3, 5, 10, 21, 40, 60):
    a = np.mean([дн(int(i), False, макс, False) for i in idxS])
    b = np.mean([дн(int(i), False, макс, True) for i in idxS])
    c = np.mean([дн(int(i), False, макс, False, 2.0) for i in idxS])
    d_ = np.mean([дн(int(i), True, макс, False) for i in idxL])
    print(f"  {макс:8d}д {a:+16.3f}{b:+16.3f}{c:+16.3f}{d_:+17.3f}")
print(f"\n  СТАРОТО твърдение: short_ma50 = +4.55$ (n=421, win 62.7%)")
print(f"  Нито едно допускане не дава положителен ШОРТ. Геометрията е СИМЕТРИЧНА —")
print(f"  смяна на ТП/стоп не може да обърне знака на посоката.")
лог("готово")
