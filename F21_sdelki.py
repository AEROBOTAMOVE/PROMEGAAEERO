# -*- coding: utf-8 -*-
"""
F21 · СТЪПКА 2 · СДЕЛКИТЕ ВЪРХУ РАЗБЪРКАНИТЕ ДНИ

Геометрията е ДОСТАВЕНАТА, не измислена за случая:
    ТП1 +7.5 · ТП2 +12 · ТП3 +20 · СТОП −20 (долари на унция)
    стълба 1/3 на всяка цел · стоп на входа СЛЕД ТП1
    вход по ASK за лонг / BID за шорт · изход по обратната страна
    +0.02$/унция приплъзване · при съмнение в един бар — СТОПЪТ бие целта
    време-изход след 48 часа

Проби: на всеки кръгъл час, както е мерено оригинално (118 653 часови проби).
Пише f21_trades.parquet.
"""
import warnings, time, sys
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

D = "C:/Users/User/Downloads/ЛОЦО/f6_data"
t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)

ТП = (7.5, 12.0, 20.0)
СТОП = 20.0
ПРИПЛЪЗ = 0.02
ЧАСА_МАКС = 48

лог("чета баровете…")
b = pd.read_parquet(f"{D}/parquet/xauusd_1min_bid_ask.parquet",
                    columns=["timestamp_utc", "open_bid", "high_bid", "low_bid", "close_bid",
                             "open_ask", "high_ask", "low_ask", "close_ask", "session"])
b["ts"] = pd.to_datetime(b["timestamp_utc"]).dt.tz_localize(None)
b = b.dropna(subset=["open_bid", "open_ask"]).sort_values("ts").reset_index(drop=True)
лог(f"  {len(b):,} бара · {b['ts'].iloc[0]} → {b['ts'].iloc[-1]}")

дни = pd.read_parquet("f21_dni.parquet")
mixed_days = set(дни.index[дни["mixed"].fillna(False)].date)
лог(f"разбъркани дни: {len(mixed_days):,}")

TS = b["ts"].values
OB = b["open_bid"].to_numpy(np.float64); OA = b["open_ask"].to_numpy(np.float64)
HB = b["high_bid"].to_numpy(np.float64); HA = b["high_ask"].to_numpy(np.float64)
LB_ = b["low_bid"].to_numpy(np.float64); LA = b["low_ask"].to_numpy(np.float64)
SESS = b["session"].astype(str).to_numpy()
ЧАС = pd.DatetimeIndex(b["ts"]).hour.to_numpy()
МИН = pd.DatetimeIndex(b["ts"]).minute.to_numpy()
ДАТА = pd.DatetimeIndex(b["ts"]).date

# входните точки: първият бар на всеки кръгъл час в разбъркан ден
лог("избирам входните точки…")
кръгъл = (МИН == 0)
в_ден = np.array([d in mixed_days for d in ДАТА])
кандидати = np.flatnonzero(кръгъл & в_ден)
лог(f"  {len(кандидати):,} часови проби в разбъркани дни")

N = len(b)
ПРОЗ = ЧАСА_МАКС * 60


def симулирай(лонг):
    """връща DataFrame със сделките в дадената посока"""
    рез = []
    зн = 1.0 if лонг else -1.0
    for k, i in enumerate(кандидати):
        if k % 20000 == 0 and k:
            лог(f"    {'лонг' if лонг else 'шорт'} {k:,}/{len(кандидати):,}")
        вход = (OA[i] if лонг else OB[i]) + ПРИПЛЪЗ * зн
        tp = [вход + зн * t for t in ТП]
        sl = вход - зн * СТОП
        j1 = min(i + ПРОЗ, N)
        # изходът се съди по страната, на която ЗАТВАРЯШ: лонг продава на BID
        hi = (HB[i + 1:j1] if лонг else HA[i + 1:j1])
        lo = (LB_[i + 1:j1] if лонг else LA[i + 1:j1])
        if len(hi) == 0:
            continue
        # индекси на първо докосване
        if лонг:
            t_hits = [np.argmax(hi >= t) if (hi >= t).any() else -1 for t in tp]
            s_hit = np.argmax(lo <= sl) if (lo <= sl).any() else -1
        else:
            t_hits = [np.argmax(lo <= t) if (lo <= t).any() else -1 for t in tp]
            s_hit = np.argmax(hi >= sl) if (hi >= sl).any() else -1
        # стълбата
        пари = 0.0
        взети = 0
        бе = False           # стопът преместен на входа след ТП1
        край = None
        for ni, (t, ti) in enumerate(zip(tp, t_hits)):
            if ti < 0:
                continue
            # стопът преди тази цел? (при равенство СТОПЪТ бие)
            тек_sl = вход if бе else sl
            if s_hit >= 0 and s_hit <= ti:
                if not (бе and abs(тек_sl - вход) < 1e-9 and s_hit > t_hits[0]):
                    break
            пари += (t - вход) * зн / 3.0
            взети += 1
            if ni == 0:
                бе = True
            край = ("tp%d" % (ni + 1), ti)
        # остатъкът
        ост = 3 - взети
        if ост > 0:
            тек_sl = вход if бе else sl
            if s_hit >= 0:
                пари += (тек_sl - вход) * зн * ост / 3.0
                край = ("sl" if not бе else "be", s_hit)
            else:
                посл = (LB_[j1 - 1] if лонг else LA[j1 - 1])
                пари += (посл - вход) * зн * ост / 3.0
                край = ("time", len(hi) - 1)
        рез.append((b["ts"].iloc[i], "long" if лонг else "short", вход,
                    round(пари, 4), взети, край[0] if край else "?",
                    ЧАС[i], str(SESS[i]), ДАТА[i]))
    return pd.DataFrame(рез, columns=["ts", "dir", "entry", "net", "tps", "exit",
                                      "hour", "session", "date"])


лог("симулирам ЛОНГ…")
L = симулирай(True)
лог(f"  {len(L):,} сделки · нето {L['net'].mean():+.3f}$")
лог("симулирам ШОРТ…")
S = симулирай(False)
лог(f"  {len(S):,} сделки · нето {S['net'].mean():+.3f}$")

T = pd.concat([L, S], ignore_index=True)
T.to_parquet("f21_trades.parquet")
лог(f"записан f21_trades.parquet · {len(T):,} сделки")
print()
print("=" * 60)
print(f"ОБЩО В РАЗБЪРКАНО МАКРО: {len(T):,} сделки")
print(f"  печеливши : {(T['net']>0).mean()*100:.1f}%")
print(f"  нето      : {T['net'].mean():+.3f}$/сделка")
print(f"  общо      : {T['net'].sum():+,.0f}$")
print("=" * 60)
