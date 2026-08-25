# -*- coding: utf-8 -*-
"""
F28б · СРАВНЕНИЕТО В ЕДИНИЦИ РИСК, НЕ В ДОЛАРИ НА УНЦИЯ

F28 сравни геометриите в $/унция и обяви THREAD_ENDS. Но има въпрос, който
този запис НЕ отговаря честно.

Ботът оразмерява ПО РИСК (live_bot.py:1315-1318):
    риск = balance * risk_pct / 100
    лот  = риск / SL_D / 100
Тоест при стоп 50$ вместо 20$ лотът е 2.5 ПЪТИ ПО-МАЛЪК. Собственикът рискува
едни и същи пари, каквато и да е геометрията. Значи «+0.820$ на унция» при 50$
стоп НЕ е 7.2 пъти по-добро от «−0.114$» при 20$ — трябва да се дели на риска.

ЧЕСТНАТА ЕДИНИЦА е R = нето / стоп: «колко от рискуваното си върнал».
Точно това усеща сметката му.

Мери се СЪЩОТО, само мерната единица се сменя. Критериите остават: 99.17%
интервал на сдвоената разлика (Bonferroni за 6 сравнения), превъзходство
≥ 0.01 R, и в двете епохи.
"""
import sys, warnings, time
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
SP = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad"
sys.path.insert(0, SP)
import geom_harness as GH
GH.TIME_EXIT_DAYS = 21

t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)
B = GH.load_tape(); E = GH.build_entries(B)
ДЕН = pd.to_datetime(pd.Series(B["ts"])[E["bar_index"].values].values).normalize()
лог(f"входове: {len(E):,} · време-изход {GH.TIME_EXIT_DAYS}д")

ПРОП = (0.375, 0.6, 1.0)
геом = lambda име, sl, дял=(1/3, 1/3, 1/3): {
    "name": име, "sl": sl,
    "tps": [(f, sl * p) for f, p in zip(дял, ПРОП)], "be_after_tp1": True}
ВАР = [("0 доставената 20$", 20.0, геом("g0", 20.0)),
       ("1 двойно широк 40$", 40.0, геом("g1", 40.0)),
       ("2 половин 10$", 10.0, геом("g2", 10.0)),
       ("3 един и половина 30$", 30.0, геом("g3", 30.0)),
       ("4 три четвърти 15$", 15.0, геом("g4", 15.0)),
       ("5 две и половина 50$", 50.0, геом("g5", 50.0)),
       ("6 една цел 20$", 20.0, геом("g6", 20.0, дял=(1.0, 0.0, 0.0)))]

N, R = {}, {}
for име, sl, g in ВАР:
    v = GH.simulate_paired(E, g, B)
    N[име] = v
    R[име] = v / sl                      # 🔴 ЕДИНИЦИ РИСК
    лог(f"  {име:24s} {np.nanmean(v):+7.3f}$/oz · {np.nanmean(R[име]):+8.5f} R")

RNG = np.random.default_rng(28)
д = pd.Series(ДЕН)


def разлика(a, b, маска=None, alpha=99.17):
    ок = np.isfinite(a) & np.isfinite(b)
    if маска is not None: ок &= маска
    if ок.sum() < 200: return None
    dd = pd.DataFrame({"d": a[ок] - b[ок], "day": д[ок].values})
    g = dd.groupby("day")["d"].agg(["sum", "count"])
    S, C = g["sum"].to_numpy(), g["count"].to_numpy(); k = len(S)
    из = RNG.integers(0, k, size=(4000, k))
    m = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    a_ = (100 - alpha) / 2
    return S.sum()/C.sum(), np.percentile(m, a_), np.percentile(m, 100 - a_), int(ок.sum())


база = R["0 доставената 20$"]
print()
print("=" * 86)
print("F28б · В ЕДИНИЦИ РИСК (R = нето / стоп) · така, както сметката го усеща")
print("=" * 86)
print(f"  {'вариант':24s} {'R/сделка':>10s} {'разлика':>10s} {'99.17% на разликата':>24s}")
поб = []
for име, sl, _ in ВАР:
    if име.startswith("0"):
        print(f"  {име:24s} {np.nanmean(база):+10.5f} {'—':>10s}"); continue
    r = разлика(R[име], база)
    if not r: continue
    dd, lo, hi, n = r
    ок = lo > 0 and dd >= 0.01
    print(f"  {име:24s} {np.nanmean(R[име]):+10.5f} {dd:+10.5f}  "
          f"[{lo:+9.5f} .. {hi:+9.5f}]  {'✅ БИЕ' if ок else 'не бие'}")
    if ок: поб.append(име)

print()
if not поб:
    print("НИТО ЕДИН НЕ БИЕ И В ЕДИНИЦИ РИСК → F28б THREAD_ENDS")
else:
    гр = pd.Timestamp("2014-01-01"); ранни = (д < гр).to_numpy()
    for име in поб:
        ра, къ = разлика(R[име], база, ранни), разлика(R[име], база, ~ранни)
        print(f"  {име:24s} 2006-13 {ра[0]:+.5f} · 2014-26 {къ[0]:+.5f} "
              f"{'✅ ДВЕТЕ' if ра and къ and ра[0] > 0 and къ[0] > 0 else '🔴 само едната'}")

# посоката: последователна ли е спрямо ширината
print()
print("ПОСОКАТА (за протокола — не е доказателство):")
for име, sl, _ in sorted(ВАР, key=lambda x: x[1]):
    if име.startswith("6"): continue
    print(f"  стоп {sl:5.0f}$ → {np.nanmean(R[име]):+9.5f} R · {np.nanmean(N[име]):+7.3f}$/oz")
лог("готово")
