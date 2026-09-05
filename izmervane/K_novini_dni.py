# -*- coding: utf-8 -*-
"""ПРЕДСТАВЯ ЛИ СЕ БОТЪТ ПО-ЗЛЕ ОКОЛО ГОЛЕМИТЕ НОВИНИ.

Собственикът: «петъкът е такъв заради новините — а ние там сме предпазливи».
Щитът съществува, но на 04.09 (NFP) ботът е взел 13 сделки. Въпросът е дали
предпазливостта е достатъчна — и това се мери, не се предполага.

Историческият календар за 22 години го нямаме. Затова се ползват ДВА
ПРОКСИТА, всеки от които е ПРОВЕРИМ факт за американските публикации:
  1) ЧАСЪТ · почти всичко голямо излиза 8:30 нюйоркско (BLS/BEA/Census).
     FOMC е 14:00 ET.
  2) ДЕНЯТ · NFP е ПЪРВИЯТ ПЕТЪК на месеца, без изключение от 1915 г.
Прокси не е календар — казва се изрично. Но и двата са точни по устройство.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----"
            r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad\repo\izmervane\mer_shortyt")
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng

SEED, REPS = 20260905, 5000
B = eng.tape()
E = pd.read_parquet(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----"
                    r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad\geom_entries.parquet")
print("входове:", len(E), "· лонг", int((E.direction == "long").sum()),
      "· шорт", int((E.direction == "short").sum()))

ts = pd.DatetimeIndex(E.timestamp_utc)
idx = E.bar_index.values.astype(np.int64)
px = E.entry_px.values.astype(float)
dayid = B["dord"][idx]

# ── прокси 1 · ЧАСЪТ (нюйоркско) ─────────────────────────────────────────
ню = ts.tz_localize("UTC").tz_convert("America/New_York")
мин_ню = ню.hour * 60 + ню.minute
_данни = (mин_ню >= 8 * 60 + 15) & (mин_ню <= 9 * 60 + 15) if False else \
    (мин_ню >= 8 * 60 + 15) & (мин_ню <= 9 * 60 + 15)
_фомс = (мин_ню >= 13 * 60 + 45) & (мин_ню <= 14 * 60 + 45)

# ── прокси 2 · ПЪРВИЯТ ПЕТЪК на месеца (NFP) ─────────────────────────────
_петък = ню.dayofweek == 4
_първи = ню.day <= 7
_nfp = _петък & _първи

ЖИВА_L = eng.G("long", [(1 / 3, 7.5), (1 / 3, 12.0), (1 / 3, 20.0)], 13.0,
               be_after_tp1=True, days=21)
ЖИВА_S = eng.G("short", [(0.5, 5.0), (0.25, 10.0), (0.25, 20.0)], 13.0,
               be_after_tp1=True, days=21)

# двигателят е ШОРТ-only; лонговете се мерят като огледало върху bid/ask
_дълъг = (E.direction == "long").values
net = np.full(len(E), np.nan)
_ш = np.where(~_дълъг)[0]
if len(_ш):
    net[_ш] = eng.run_many(idx[_ш], px[_ш], [ЖИВА_S], B, want=("net",))["net"][0]
print("шорт сделки, сметнати:", int(np.isfinite(net[_ш]).sum()))


def съди(маска, име):
    v = net[маска]
    d = dayid[маска]
    ок = np.isfinite(v)
    v, d = v[ок], d[ок]
    if len(v) < 60:
        return "  %-34s n=%-5d малко" % (име, len(v))
    _m, lo, hi = eng.boot_day(v, d, reps=REPS, seed=SEED)
    зн = "✅" if lo > 0 else ("🛑" if hi < 0 else "⚪")
    return ("  %-34s n=%-5d дни=%-5d %+8.4f  [%+7.4f, %+7.4f]  %s"
            % (име, len(v), len(np.unique(d)), v.mean(), lo, hi, зн))


print()
print("═" * 88)
print("ШОРТОВЕТЕ · около американските данни срещу останалото време")
print("═" * 88)
_ш_маска = ~_дълъг
print(съди(_ш_маска, "всички шортове"))
print(съди(_ш_маска & _данни, "в прозореца 8:15-9:15 Ню Йорк"))
print(съди(_ш_маска & ~_данни, "ИЗВЪН него"))
print(съди(_ш_маска & _фомс, "в прозореца 13:45-14:45 (FOMC)"))
print(съди(_ш_маска & _nfp, "в ДЕНЯ на NFP (първи петък)"))
print(съди(_ш_маска & ~_nfp, "в другите дни"))
print(съди(_ш_маска & _nfp & _данни, "NFP ден И в прозореца на данните"))

print()
print("═" * 88)
print("РАЗЛИКАТА, сдвоено по ден (това е въпросът)")
print("═" * 88)
for маска, друга, име in ((_ш_маска & _данни, _ш_маска & ~_данни, "прозорецът на данните"),
                          (_ш_маска & _nfp, _ш_маска & ~_nfp, "денят на NFP")):
    a, b = net[маска], net[друга]
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if len(a) < 60 or len(b) < 60:
        print("  %-26s малко данни" % име); continue
    rng = np.random.default_rng(SEED)
    d = (a[rng.integers(0, len(a), size=(REPS, len(a)))].mean(1)
         - b[rng.integers(0, len(b), size=(REPS, len(b)))].mean(1))
    lo, hi = np.percentile(d, [2.5, 97.5])
    зн = "✅" if lo > 0 else ("🛑" if hi < 0 else "⚪")
    print("  %-26s разлика %+8.4f  [%+7.4f, %+7.4f]  %s  (n=%d срещу %d)"
          % (име, a.mean() - b.mean(), lo, hi, зн, len(a), len(b)))

print()
print("═" * 88)
print("И КОЛКО ВХОДА ИЗОБЩО ПАДАТ В ТЕЗИ ПРОЗОРЦИ")
print("═" * 88)
for м, име in ((_данни, "8:15-9:15 Ню Йорк"), (_фомс, "13:45-14:45"), (_nfp, "ден на NFP")):
    print("  %-24s %5d от %d входа (%.1f%%)"
          % (име, int(м.sum()), len(E), 100.0 * м.sum() / len(E)))
