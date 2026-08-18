# -*- coding: utf-8 -*-
"""
F26 · ВРЕМЕТО-ИЗХОД: ИНСТРУМЕНТЪТ РЕЖЕ НА 5 ДНИ, БОТЪТ ДЪРЖИ 30

Намерено от адверсарния агент, потвърдено лично:
    geom_harness.py:63   TIME_EXIT_DAYS = 5      # trading days
    live_bot.py:2204     if age >= 30:           # КАЛЕНДАРНИ дни ≈ 21 търговски

Значи ВСЯКА клетка в `backtest_stats.json`, включително онези, по които гейтът
решава всеки вход, е мерена под правило за изход, което ботът НЕ изпълнява.
`_meta` описва геометрията като «време-изход» БЕЗ число — затова разминаването
е могло да живее.

МЕРЯ: същите входове, същата геометрия, само времето-изход 5 срещу 21 дни.
Ако клетките мръднат съществено, числата на гейта трябва да се преизмерят.
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
ДЕН = pd.to_datetime(pd.Series(B["ts"])[E["bar_index"].values].values).normalize()
лог(f"входове: {len(E):,} · колони: {list(E.columns)[:9]}")

ГЕОМ = {"name": "доставената", "sl": 20.0,
        "tps": [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], "be_after_tp1": True}

рез = {}
for дни in (5, 21):
    GH.TIME_EXIT_DAYS = дни
    рез[дни] = GH.simulate_paired(E, ГЕОМ, B)
    лог(f"  време-изход {дни:>2}д → нето {np.nanmean(рез[дни]):+.4f}$ "
        f"({np.isfinite(рез[дни]).sum():,} валидни)")

RNG = np.random.default_rng(26)
д = pd.Series(ДЕН)


def бут(x, маска=None):
    ок = np.isfinite(x)
    if маска is not None:
        ок &= маска
    if ок.sum() < 100:
        return None
    dd = pd.DataFrame({"v": x[ок], "d": д[ок].values}).groupby("d")["v"].agg(["sum", "count"])
    S, C = dd["sum"].to_numpy(), dd["count"].to_numpy(); k = len(S)
    из = RNG.integers(0, k, size=(3000, k))
    m = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    return (float(np.nansum(x[ок]) / ок.sum()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), int(ок.sum()))


print()
print("=" * 92)
print("F26 · ЕДНИ И СЪЩИ ВХОДОВЕ, САМО ВРЕМЕТО-ИЗХОД СЕ МЕНИ")
print("=" * 92)
# по посока
dirs = E["direction"].values
for име, м in (("ВСИЧКИ", None), ("ЛОНГ", dirs == "long"), ("ШОРТ", dirs == "short")):
    a5, a21 = бут(рез[5], м), бут(рез[21], м)
    if not (a5 and a21):
        continue
    print(f"  {име:7s} n={a5[3]:>6,d}   5д {a5[0]:+7.3f}$ [{a5[1]:+6.2f}..{a5[2]:+6.2f}]"
          f"   21д {a21[0]:+7.3f}$ [{a21[1]:+6.2f}..{a21[2]:+6.2f}]"
          f"   разлика {a21[0]-a5[0]:+7.3f}$")

# сдвоена разлика — това е точното число
ок = np.isfinite(рез[5]) & np.isfinite(рез[21])
р = рез[21] - рез[5]
dd = pd.DataFrame({"v": р[ок], "d": д[ок].values}).groupby("d")["v"].agg(["sum", "count"])
S, C = dd["sum"].to_numpy(), dd["count"].to_numpy(); k = len(S)
из = RNG.integers(0, k, size=(4000, k))
m = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
print()
print(f"  СДВОЕНА РАЗЛИКА (21д минус 5д) на {int(ок.sum()):,} общи сделки:")
print(f"    {S.sum()/C.sum():+.4f}$ на сделка  "
      f"[{np.percentile(m,2.5):+.4f} .. {np.percentile(m,97.5):+.4f}]")
_знач = np.percentile(m, 2.5) > 0 or np.percentile(m, 97.5) < 0
print(f"    {'🔴 РАЗЛИКАТА Е ЗНАЧИМА — клетките са мерени по чуждо правило' if _знач else '✅ разликата е в шума — клетките важат и за двата изхода'}")
# колко сделки изобщо доживяват до времето-изход
print()
for дни in (5, 21):
    GH.TIME_EXIT_DAYS = дни
лог("готово")
