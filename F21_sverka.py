# -*- coding: utf-8 -*-
"""
F21 · СТЪПКА 2б · СВЕРКА НА МАШИНАРИЯТА

Моята реконструкция дава лонг/mixed = +0.775$, а официалната клетка казва
−0.47$. Преди каквото и да е твърдение — проверявам себе си.

Методът: пускам СЪЩАТА машинария върху клетките, които ЗНАЯ (fresh, day1,
stale). Възпроизведе ли ги — машинарията е вярна и mixed е аномалията.
Не ги ли възпроизведе — грешката е моя и mixed не значи нищо.

Официалните числа (backtest_stats.json, long):
    day1   n=4019   +2.99$
    fresh  n=5935   +2.01$
    stale  n=21900  +0.94$
    mixed  n=28706  −0.47$
"""
import warnings, time, json, io
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

D = "C:/Users/User/Downloads/ЛОЦО/f6_data"
t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)

ТП = (7.5, 12.0, 20.0); СТОП = 20.0; ПРИПЛЪЗ = 0.02; ЧАСА_МАКС = 48

лог("чета…")
b = pd.read_parquet(f"{D}/parquet/xauusd_1min_bid_ask.parquet",
                    columns=["timestamp_utc", "open_bid", "high_bid", "low_bid",
                             "open_ask", "high_ask", "low_ask"])
b["ts"] = pd.to_datetime(b["timestamp_utc"]).dt.tz_localize(None)
b = b.dropna(subset=["open_bid", "open_ask"]).sort_values("ts").reset_index(drop=True)
дни = pd.read_parquet("f21_dni.parquet")

# клетката за всеки ден, ТОЧНО както `_cell_name`
def клетка(r):
    sl, ss = r["st_l"], r["st_s"]
    s = sl if sl > 0 else (ss if ss > 0 else 0)
    if s == 1: return "day1"
    if 2 <= s <= 3: return "fresh"
    if s == 0: return "mixed"
    return "stale"

дни["cell"] = дни.apply(клетка, axis=1)
дни["bull"] = дни["st_l"] > 0          # подреждането е БИЧО
лог("клетки по дни: " + str(дни["cell"].value_counts().to_dict()))

OB = b["open_bid"].to_numpy(); OA = b["open_ask"].to_numpy()
HB = b["high_bid"].to_numpy(); HA = b["high_ask"].to_numpy()
LB_ = b["low_bid"].to_numpy(); LA = b["low_ask"].to_numpy()
МИН = pd.DatetimeIndex(b["ts"]).minute.to_numpy()
ДАТА = pd.DatetimeIndex(b["ts"]).normalize()
N = len(b); ПРОЗ = ЧАСА_МАКС * 60

карта_кл = дни["cell"].to_dict()
кръгъл = np.flatnonzero(МИН == 0)
лог(f"часови проби общо: {len(кръгъл):,}")


def една(i, лонг):
    зн = 1.0 if лонг else -1.0
    вход = (OA[i] if лонг else OB[i]) + ПРИПЛЪЗ * зн
    tp = [вход + зн * t for t in ТП]; sl = вход - зн * СТОП
    j1 = min(i + ПРОЗ, N)
    hi = (HB[i + 1:j1] if лонг else HA[i + 1:j1])
    lo = (LB_[i + 1:j1] if лонг else LA[i + 1:j1])
    if len(hi) == 0: return None
    if лонг:
        th = [int(np.argmax(hi >= t)) if (hi >= t).any() else -1 for t in tp]
        sh = int(np.argmax(lo <= sl)) if (lo <= sl).any() else -1
    else:
        th = [int(np.argmax(lo <= t)) if (lo <= t).any() else -1 for t in tp]
        sh = int(np.argmax(hi >= sl)) if (hi >= sl).any() else -1
    пари = 0.0; взети = 0; бе = False
    for ni, (t, ti) in enumerate(zip(tp, th)):
        if ti < 0: continue
        if sh >= 0 and sh <= ti and not бе: break
        if sh >= 0 and sh <= ti and бе: break
        пари += (t - вход) * зн / 3.0; взети += 1
        if ni == 0: бе = True
    ост = 3 - взети
    if ост > 0:
        тек = вход if бе else sl
        if sh >= 0:
            пари += (тек - вход) * зн * ост / 3.0
        else:
            посл = (LB_[j1 - 1] if лонг else LA[j1 - 1])
            пари += (посл - вход) * зн * ост / 3.0
    return пари


лог("симулирам всички клетки…")
рез = []
for k, i in enumerate(кръгъл):
    if k % 30000 == 0 and k: лог(f"  {k:,}/{len(кръгъл):,}")
    д = ДАТА[i]
    кл = карта_кл.get(д)
    if kl := кл:
        p = една(i, True)
        if p is not None: рез.append((кл, "long", p))
        p = една(i, False)
        if p is not None: рез.append((кл, "short", p))

R = pd.DataFrame(рез, columns=["cell", "dir", "net"])
R.to_parquet("f21_sverka.parquet")

оф = json.load(io.open("backtest_stats.json", encoding="utf-8"))["fresh"]
print()
print("=" * 74)
print("СВЕРКА · моята машинария срещу официалните клетки (ЛОНГ)")
print("=" * 74)
print(f"  {'клетка':8s} {'мои n':>8s} {'мое нето':>10s} {'офиц. n':>8s} {'офиц. нето':>11s}  съвпада?")
for кл in ("day1", "fresh", "stale", "mixed"):
    g = R[(R["cell"] == кл) & (R["dir"] == "long")]
    o = (оф.get("long") or {}).get(кл) or {}
    if not len(g) or not o: continue
    моe, офн = g["net"].mean(), float(o.get("net", 0))
    знак = "✅" if (моe > 0) == (офн > 0) else "🔴 ОБРАТЕН ЗНАК"
    print(f"  {кл:8s} {len(g):8,d} {моe:+9.3f}$ {o.get('n',0):8,d} {офн:+10.2f}$  {знак}")
print()
print("  ⚠️ Ако знаците не съвпадат — грешката е МОЯ и mixed не значи нищо.")
