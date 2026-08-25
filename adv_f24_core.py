# -*- coding: utf-8 -*-
"""adv · АТАКА срещу F24. Не пипа нищо — само чете и мери."""
import warnings, json, io, sys, time
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

D = "C:/Users/User/Downloads/ЛОЦО/f6_data"
ТП = (0.20, 0.32, 0.54); СТОП = 0.54; ДНИ_МАКС = 21


def dc(p):
    d = pd.read_csv(p)
    c = [x for x in d.columns if x.lower() in ("date", "datetime", "observation_date")][0]
    d[c] = pd.to_datetime(d[c], errors="coerce")
    return d.dropna(subset=[c]).set_index(c).sort_index()


s = dc(f"{D}/silver_yahoo_full.csv")
s = s[["Open", "High", "Low", "Close"]].apply(pd.to_numeric, errors="coerce").dropna()
dx = dc(f"{D}/dxy_yahoo_full.csv")["Close"].reindex(s.index).ffill()
rr = pd.to_numeric(dc(f"{D}/DFII10.csv")["DFII10"], errors="coerce").reindex(s.index).ffill()

print("=" * 92)
print("0 · САНИТЕТ НА ДАННИТЕ silver_yahoo_full.csv")
print("=" * 92)
print(f"  редове {len(s):,} · {s.index[0].date()} → {s.index[-1].date()}")
bad_hl = (s["High"] < s["Low"]).sum()
bad_c = ((s["Close"] > s["High"]) | (s["Close"] < s["Low"])).sum()
bad_o = ((s["Open"] > s["High"]) | (s["Open"] < s["Low"])).sum()
dup = s.index.duplicated().sum()
rng = (s["High"] - s["Low"])
print(f"  High<Low: {bad_hl} · Close извън [L,H]: {bad_c} · Open извън: {bad_o} · дублирани дати: {dup}")
print(f"  дневен диапазон H-L: медиана {rng.median():.4f}$ · 10% {rng.quantile(.1):.4f} · 90% {rng.quantile(.9):.4f}")
print(f"  нулев диапазон (H==L, мъртъв бар): {(rng == 0).sum()} дни")
print(f"  ГЕОМЕТРИЯТА: ТП1 {ТП[0]}$ · СТОП {СТОП}$ → медианният ДНЕВЕН диапазон е "
      f"{rng.median()/ТП[0]:.2f}× ТП1 и {rng.median()/СТОП:.2f}× стопа")
# празнини
gaps = s.index.to_series().diff().dt.days
print(f"  най-голяма дупка между дни: {int(gaps.max())} дни на {s.index[int(gaps.values.argmax())].date()}")
print(f"  дни с дупка >7 дни: {int((gaps > 7).sum())}")
print()

d20 = dx.pct_change(20); r20 = rr - rr.shift(20)
H, L, C, O = s["High"].to_numpy(), s["Low"].to_numpy(), s["Close"].to_numpy(), s["Open"].to_numpy()
N = len(s)


def сделка(i, лонг, стоп_бие=True, следи=None):
    """копие на F24 `сделка()`; `стоп_бие=False` → ЦЕЛТА бие при съмнение"""
    зн = 1.0 if лонг else -1.0
    вх = C[i]
    tp = [вх + зн * t for t in ТП]; sl = вх - зн * СТОП
    пари = 0.0; взети = 0; бе = False; двусмислен = False
    for j in range(i + 1, min(i + 1 + ДНИ_МАКС, N)):
        hi, lo = H[j], L[j]
        тек = вх if бе else sl
        уд_ст = (lo <= тек) if лонг else (hi >= тек)
        нови = [k for k, t in enumerate(tp) if k >= взети
                and ((hi >= t) if лонг else (lo <= t))]
        if уд_ст and нови:
            двусмислен = True
        if уд_ст and (стоп_бие or not нови):
            пари += (тек - вх) * зн * (3 - взети) / 3.0
            if следи is not None: следи.append(двусмислен)
            return пари, взети, ("be" if бе else "sl"), двусмислен, j - i
        for k in нови:
            пари += (tp[k] - вх) * зн / 3.0
            взети = k + 1
            if k == 0: бе = True
            if k == 2:
                return пари, взети, "tp3", двусмислен, j - i
        if уд_ст and нови and not стоп_бие:
            # целта бие: доиграваме остатъка на стопа СЛЕД като са взети целите
            пари += (тек - вх) * зн * (3 - взети) / 3.0
            return пари, взети, ("be" if бе else "sl"), двусмислен, j - i
    посл = C[min(i + ДНИ_МАКС, N - 1)]
    пари += (посл - вх) * зн * (3 - взети) / 3.0
    return пари, взети, "time", двусмислен, min(ДНИ_МАКС, N - 1 - i)


def построй(лаг):
    """лаг=0 → както F24 (макро от СЪЩИЯ ден). лаг=1 → както ЖИВИЯ бот за златото."""
    mL = ((-d20.shift(лаг)) > 0) & ((-r20.shift(лаг)) > 0)
    mS = (d20.shift(лаг) > 0) & (r20.shift(лаг) > 0)
    стр = lambda x: x.fillna(False).groupby((~x.fillna(False)).cumsum()).cumsum().astype(int)
    return стр(mL), стр(mS)


vol20 = s["Close"].pct_change().rolling(20).std()
vr = vol20.rolling(504, min_periods=250).rank(pct=True)

рез = {}
for лаг in (0, 1):
    SL, SS = построй(лаг)
    for стоп_бие in (True, False):
        R = []
        for i in range(60, N - 2):
            sl_, ss_ = int(SL.iloc[i]), int(SS.iloc[i])
            for лонг in (True, False):
                п, вз, к, дв, дни = сделка(i, лонг, стоп_бие)
                R.append((s.index[i], "long" if лонг else "short",
                          sl_ if лонг else ss_, п, float(vr.iloc[i]) if pd.notna(vr.iloc[i]) else np.nan,
                          дв, дни, к))
        рез[(лаг, стоп_бие)] = pd.DataFrame(
            R, columns=["ден", "посока", "стрийк", "нето", "vr", "двусмислен", "дни", "как"])

T = рез[(0, True)]          # ТОЧНО каквото мери F24
T.to_pickle("adv_T_base.pkl")
рез[(0, False)].to_pickle("adv_T_tpwins.pkl")
рез[(1, True)].to_pickle("adv_T_lag1.pkl")
print(f"сделки: {len(T):,}  (сверка с F24: очаква 12858)")
print()

print("=" * 92)
print("1 · КОЛКО ЧЕСТО СТОП И ЦЕЛ СА В ЕДИН И СЪЩИ ДЕН (и решава конвенцията)")
print("=" * 92)
дв = T["двусмислен"].mean() * 100
print(f"  двусмислени сделки: {T['двусмислен'].sum():,} от {len(T):,} = {дв:.1f}%")
print(f"  разпределение на изходите: ")
for k, v in T['как'].value_counts().items():
    print(f"     {k:6s} {v:6,d}  {v/len(T)*100:5.1f}%")
print(f"  средна продължителност: {T['дни'].mean():.2f} дни · медиана {T['дни'].median():.0f} · "
      f"дял стигнали до 21: {(T['дни'] >= 21).mean()*100:.1f}%")
print(f"  РАЗМЕР НА ЕФЕКТА ОТ КОНВЕНЦИЯТА:")
print(f"     стопът бие (F24):  средно нето {T['нето'].mean():+.4f}$")
print(f"     целта бие:         средно нето {рез[(0, False)]['нето'].mean():+.4f}$")
print(f"     разлика:           {рез[(0, False)]['нето'].mean() - T['нето'].mean():+.4f}$/сделка")
print()

print("=" * 92)
print("2 · LOOK-AHEAD · F24 ползва макро от СЪЩИЯ ден; живият бот за златото ползва shift(1)")
print("=" * 92)
for им, tt in (("F24 (лаг 0)", T), ("живата конвенция (лаг 1)", рез[(1, True)])):
    for d in ("long", "short"):
        g = tt[tt["посока"] == d]
        for кл, ф in (("day1", g["стрийк"] == 1), ("fresh", g["стрийк"].between(2, 3)),
                      ("mixed", g["стрийк"] == 0), ("stale", g["стрийк"] >= 4)):
            x = g[ф]
            if len(x) < 30: continue
            print(f"  {им:24s} {d:6s} {кл:6s} n={len(x):5,d}  нето {x['нето'].mean():+.4f}$")
    print()
