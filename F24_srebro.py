# -*- coding: utf-8 -*-
"""
F24 · ПРЕИЗМЕРВАНЕ НА СРЕБЪРНИТЕ КЛЕТКИ

## Защо
Мерено днес от `backtest_stats.json`:
  · среброто НЯМА клетките `day1`, `mixed`, `ultra` — златото ги има
  · НИТО ЕДНА сребърна клетка няма `lo`/`hi` → `_noise()` СТРУКТУРНО не може
    да се задейства → +0.014$ минава за «ръб», без да се провери дали нулата
    е вътре в интервала
  · заради липсващата `mixed` гейтът падаше на `stale` — сливането, което за
    златото беше разделено на 04.08 (mixed −0.47$ срещу stale +0.94$)

## Какво МОГА и какво НЕ мога
Данните за среброто са ДНЕВНИ, без bid/ask (silver_yahoo_full.csv, 6491 реда,
2000–2026). Значи НЕ мога да го меря като златото (7.96M едноминутни бара с
двете страни на спреда). Това остава честното ограничение.
МОГА обаче двете неща, които не искат тикови данни:
  1. да добавя липсващите клетки по СЪЩИЯ дневен метод като съществуващите
  2. да сметна доверителни интервали → шум-пазачът оживява

## Метод
Геометрията е доставената за сребро: ТП 0.20/0.32/0.54 · стоп 0.54 · стълба 1/3
· стоп на входа след ТП1 · дневен барер (High/Low на всеки следващ ден) ·
при съмнение в един ден СТОПЪТ бие целта · време-изход 21 дни.
Подреждането е СЪЩОТО правило като златото: ДОЛАР + РЕАЛНИ ЛИХВИ.
Блоков бутстрап ПО ДЕН, 4000 повторения, 95% интервал.

## Честно за границите — влиза В САМИЯ ФАЙЛ
Дневна разделителна способност · без спред · без приплъзване.
Реалният резултат е ПО-ЛОШ от показания. Затова клетките получават и поле
`_разделителна`, което казва това на глас.
"""
import warnings, json, io, time
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

D = "C:/Users/User/Downloads/ЛОЦО/f6_data"
t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:5.1f}s] {s}", flush=True)

ТП = (0.20, 0.32, 0.54); СТОП = 0.54; ДНИ_МАКС = 21


def dc(p, кол=None):
    d = pd.read_csv(p)
    c = [x for x in d.columns if x.lower() in ("date", "datetime", "observation_date")][0]
    d[c] = pd.to_datetime(d[c], errors="coerce")
    return d.dropna(subset=[c]).set_index(c).sort_index()


s = dc(f"{D}/silver_yahoo_full.csv")
s = s[["Open", "High", "Low", "Close"]].apply(pd.to_numeric, errors="coerce").dropna()
лог(f"сребро: {len(s):,} дни · {s.index[0].date()} → {s.index[-1].date()}")

dx = dc(f"{D}/dxy_yahoo_full.csv")["Close"].reindex(s.index).ffill()
rr = pd.to_numeric(dc(f"{D}/DFII10.csv")["DFII10"], errors="coerce").reindex(s.index).ffill()
лог(f"макро сверено · долар {dx.notna().sum():,} · лихви {rr.notna().sum():,}")

# СЪЩОТО правило като златото
d20 = dx.pct_change(20); r20 = rr - rr.shift(20)
mL = ((-d20) > 0) & ((-r20) > 0)
mS = (d20 > 0) & (r20 > 0)
стр = lambda x: x.fillna(False).groupby((~x.fillna(False)).cumsum()).cumsum().astype(int)
SL, SS = стр(mL), стр(mS)

# волатилност за клетката ultra (както при златото: пресен + тих пазар)
vol20 = s["Close"].pct_change().rolling(20).std()
vr = vol20.rolling(504, min_periods=250).rank(pct=True)

H, L, C, O = s["High"].to_numpy(), s["Low"].to_numpy(), s["Close"].to_numpy(), s["Open"].to_numpy()
N = len(s)


def сделка(i, лонг):
    """дневен барер от ден i+1 нататък"""
    зн = 1.0 if лонг else -1.0
    вх = C[i]
    tp = [вх + зн * t for t in ТП]; sl = вх - зн * СТОП
    пари = 0.0; взети = 0; бе = False
    for j in range(i + 1, min(i + 1 + ДНИ_МАКС, N)):
        hi, lo = H[j], L[j]
        тек = вх if бе else sl
        уд_ст = (lo <= тек) if лонг else (hi >= тек)
        # СТОПЪТ БИЕ при съмнение в един и същи ден
        нови = [k for k, t in enumerate(tp) if k >= взети
                and ((hi >= t) if лонг else (lo <= t))]
        if уд_ст and not нови:
            пари += (тек - вх) * зн * (3 - взети) / 3.0
            return пари, взети, ("be" if бе else "sl")
        if уд_ст and нови:
            пари += (тек - вх) * зн * (3 - взети) / 3.0
            return пари, взети, ("be" if бе else "sl")
        for k in нови:
            пари += (tp[k] - вх) * зн / 3.0
            взети = k + 1
            if k == 0: бе = True
            if k == 2:
                return пари, взети, "tp3"
    посл = C[min(i + ДНИ_МАКС, N - 1)]
    пари += (посл - вх) * зн * (3 - взети) / 3.0
    return пари, взети, "time"


лог("симулирам…")
рез = []
for i in range(60, N - 2):
    sl_, ss_ = int(SL.iloc[i]), int(SS.iloc[i])
    for лонг in (True, False):
        стрийк = sl_ if лонг else ss_
        п, вз, к = сделка(i, лонг)
        рез.append((s.index[i], "long" if лонг else "short", стрийк, п,
                    float(vr.iloc[i]) if pd.notna(vr.iloc[i]) else np.nan))
T = pd.DataFrame(рез, columns=["ден", "посока", "стрийк", "нето", "vr"])
лог(f"сделки: {len(T):,}")

RNG = np.random.default_rng(24)


def клетка(g):
    if len(g) < 30: return None
    d = g.groupby("ден")["нето"].agg(["sum", "count"])
    S_, C_ = d["sum"].to_numpy(), d["count"].to_numpy(); k = len(S_)
    из = RNG.integers(0, k, size=(4000, k))
    m = S_[из].sum(axis=1) / np.maximum(C_[из].sum(axis=1), 1)
    return {"win": round(float((g["нето"] > 0).mean() * 100), 1),
            "net": round(float(g["нето"].mean()), 4),
            "n": int(len(g)), "дни": int(k),
            "lo": round(float(np.percentile(m, 2.5)), 4),
            "hi": round(float(np.percentile(m, 97.5)), 4)}


КЛЕТКИ = {
    "day1":  lambda g: g["стрийк"] == 1,
    "fresh": lambda g: g["стрийк"].between(2, 3),
    "mixed": lambda g: g["стрийк"] == 0,
    "stale": lambda g: g["стрийк"] >= 4,
    "ultra": lambda g: (g["стрийк"].between(1, 3)) & (g["vr"] < 0.40),
}
изх = {}
print()
print("=" * 78)
print("СРЕБЪРНИТЕ КЛЕТКИ · дневна разделителна · 95% блоков бутстрап по ден")
print("=" * 78)
print(f"  {'посока':6s} {'клетка':7s} {'n':>6s} {'дни':>5s} {'печели':>7s} {'нето':>9s} {'95% интервал':>22s}  присъда")
for d in ("long", "short"):
    изх[d] = {}
    for им, ф in КЛЕТКИ.items():
        g = T[(T["посока"] == d) & ф(T)]
        a = клетка(g)
        if not a: continue
        изх[d][им] = a
        шум = a["lo"] <= 0 <= a["hi"]
        пр = "ШУМ → отказ" if шум else ("ПУСКА" if a["net"] > 0 else "ГУБИ → отказ")
        print(f"  {d:6s} {им:7s} {a['n']:6,d} {a['дни']:5d} {a['win']:6.1f}% "
              f"{a['net']:+8.4f}$  [{a['lo']:+7.4f} .. {a['hi']:+7.4f}]  {пр}")

json.dump(изх, io.open("F24_srebro.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print()
лог("записан F24_srebro.json")
