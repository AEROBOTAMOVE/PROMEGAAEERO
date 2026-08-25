# -*- coding: utf-8 -*-
"""
F22 · СДВОЕНО СРАВНЕНИЕ НА ГЕОМЕТРИЯТА

Първият ми опит ползваше `simulate` (без застъпване) — но по-широкият стоп
дава по-дълги сделки, значи ДРУГ брой сделки (2598 срещу 1099). Това не е
сравнение на геометрия, а сравнение на две различни извадки.

`simulate_paired` е точно за това: ВСЕКИ вход, без изхвърляне. Застъпващите се
сделки не са търгуем портфейл, но дават СДВОЕНА извадка — геометрия A и B върху
СЪЩИТЕ входове, така че разликата изолира геометрията от късмета на входа.

Критериите са от F22_geom.py, непроменени: 99.17% интервал на разликата
(Bonferroni за 6 сравнения) · превъзходство ≥ +0.20$ · и в двете епохи.
"""
import sys, warnings, time
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

SP = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad"
sys.path.insert(0, SP)
import geom_harness as GH

t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)

B = GH.load_tape()
E = GH.build_entries(B)
лог(f"входове: {len(E):,}")
ДЕН = pd.to_datetime(pd.Series(B["ts"])[E["bar_index"].values].values).normalize()

ПРОП = (0.375, 0.6, 1.0)
геом = lambda име, sl, дял=(1/3, 1/3, 1/3): {
    "name": име, "sl": sl,
    "tps": [(f, sl * p) for f, p in zip(дял, ПРОП)], "be_after_tp1": True}

ВАРИАНТИ = [
    ("0 доставената 20$", геом("g0", 20.0)),
    ("1 двойно широк 40$", геом("g1", 40.0)),
    ("2 половин 10$", геом("g2", 10.0)),
    ("3 един и половина 30$", геом("g3", 30.0)),
    ("4 три четвърти 15$", геом("g4", 15.0)),
    ("5 две и половина 50$", геом("g5", 50.0)),
    ("6 една цел 20$", геом("g6", 20.0, дял=(1.0, 0.0, 0.0))),
]

лог("сдвоена симулация…")
N = {}
for име, g in ВАРИАНТИ:
    N[име] = GH.simulate_paired(E, g, B)
    v = N[име]
    лог(f"  {име:24s} валидни {np.isfinite(v).sum():,} · нето {np.nanmean(v):+.3f}$")

база = N["0 доставената 20$"]
RNG = np.random.default_rng(22)
д = pd.Series(ДЕН)


def разлика(a, b, маска=None):
    ок = np.isfinite(a) & np.isfinite(b)
    if маска is not None:
        ок &= маска
    if ок.sum() < 200:
        return None
    dd = pd.DataFrame({"d": a[ок] - b[ок], "day": д[ок].values})
    g = dd.groupby("day")["d"].agg(["sum", "count"])
    S, C = g["sum"].to_numpy(), g["count"].to_numpy()
    k = len(S)
    из = RNG.integers(0, k, size=(4000, k))
    m = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    a_ = (100 - 99.17) / 2
    return S.sum() / C.sum(), np.percentile(m, a_), np.percentile(m, 100 - a_), int(ок.sum())


print()
print("=" * 80)
print("СДВОЕНО · разликата спрямо доставената, върху СЪЩИТЕ входове")
print("=" * 80)
print(f"  {'вариант':24s} {'нето':>9s} {'разлика':>10s} {'99.17% на разликата':>24s}")
поб = []
for име, _ in ВАРИАНТИ:
    v = N[име]
    if име.startswith("0"):
        print(f"  {име:24s} {np.nanmean(v):+8.3f}$  {'—':>9s}")
        continue
    r = разлика(v, база)
    if not r:
        print(f"  {име:24s} малко"); continue
    dd, lo, hi, n = r
    ок = lo > 0 and dd >= 0.20
    print(f"  {име:24s} {np.nanmean(v):+8.3f}$  {dd:+9.3f}$  "
          f"[{lo:+7.3f} .. {hi:+7.3f}]  {'✅ БИЕ' if ок else 'не бие'}")
    if ок:
        поб.append(име)

print()
if not поб:
    print("НИТО ЕДИН НЕ БИЕ ДОСТАВЕНАТА → F22 THREAD_ENDS · геометрията остава")
else:
    print("ПРОВЕРКА ПО ЕПОХИ (и двете трябва да бият)")
    гр = pd.Timestamp("2014-01-01")
    ранни = (д < гр).to_numpy(); късни = ~ранни
    for име in поб:
        ра = разлика(N[име], база, ранни)
        къ = разлика(N[име], база, късни)
        ок = ра and къ and ра[0] > 0 and къ[0] > 0
        print(f"  {име:24s} 2006-13 {ра[0]:+.3f}$ · 2014-26 {къ[0]:+.3f}$  "
              f"{'✅ ДВЕТЕ' if ок else '🔴 само едната'}")
лог("готово")
