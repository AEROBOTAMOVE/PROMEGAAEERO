# -*- coding: utf-8 -*-
"""Разбивка: какъв ВИД е разликата, колко струва, и мени ли се с нощната рядкост.
Плюс: мъртъв ли е редът на проверките, който коментарът на 1582-83 защитава?"""
import sys, io, json, os
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd, numpy as np
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, "sw_ob41.py"), encoding="utf-8").read().split("def scal(")[0])
C = B["Close"].dropna()

def прогон(зн, стоп, ц1, ц2, t0, стъпка, макс_ч=48):
    """стъпка = през колко бара се взима СКАЛАРНА проба (1 = 5мин, 2 = 10мин, 3 = 15мин)"""
    sub = B.loc[(B.index > t0) & (B.index <= t0 + pd.Timedelta(hours=макс_ч))]
    sc = sb = None; ц1s = ц1b = False; двойно = 0
    for k, (ts, r) in enumerate(sub.iterrows()):
        hi, lo, cl = float(r["High"]), float(r["Low"]), float(r["Close"])
        if any(pd.isna(x) for x in (hi, lo, cl)):
            continue
        if sb is None:
            хс = (lo <= стоп) if зн == 1 else (hi >= стоп)
            хц = (ц2 is not None) and ((hi >= ц2) if зн == 1 else (lo <= ц2))
            if хс and хц:
                двойно += 1
            if хс:
                sb = "стоп"
            elif хц:
                sb = "цел2"
            elif not ц1b and ((hi >= ц1) if зн == 1 else (lo <= ц1)):
                ц1b = True
        if sc is None and k % стъпка == 0:
            if (cl <= стоп) if зн == 1 else (cl >= стоп):
                sc = "стоп"
            elif ц2 is not None and ((cl >= ц2) if зн == 1 else (cl <= ц2)):
                sc = "цел2"
            elif not ц1s and ((cl >= ц1) if зн == 1 else (cl <= ц1)):
                ц1s = True
        if sc is not None and sb is not None:
            break
    return sc, sb, двойно

геом = [(1 if r["посока"] == "long" else -1, r["стоп"] - r["вход"], r["цел1"] - r["вход"],
         (r["цел2"] - r["вход"]) if r.get("цел2") is not None else None) for r in R]
идx = C.index[(C.index >= pd.Timestamp("2026-07-21")) & (C.index <= pd.Timestamp("2026-08-18"))]

for стъпка, име in ((1, "5 мин (дневният ритъм)"), (2, "10 мин (нощ)"), (3, "15 мин (дълбока нощ)")):
    rng = np.random.default_rng(7)
    n = 0; видове = {}; pA = pB = 0.0; дв = 0
    for _ in range(3000):
        зн, dсл, d1, d2 = геом[rng.integers(len(геом))]
        t0 = идx[rng.integers(len(идx))]
        e = float(C.loc[t0])
        sc, sb, двойно = прогон(зн, e + dсл, e + d1, (e + d2) if d2 is not None else None, t0, стъпка)
        дв += двойно
        if sc is None and sb is None:
            continue
        n += 1
        p = {"стоп": -abs(dсл), "цел2": (abs(d2) if d2 is not None else 0.0), None: 0.0}
        pA += p.get(sc, 0.0); pB += p.get(sb, 0.0)
        if sc != sb:
            видове[(str(sb), str(sc))] = видове.get((str(sb), str(sc)), 0) + 1
    print("\n=== проба на %s ===  n=%d" % (име, n))
    print("   мозък %+.3f$/набл. · бар %+.3f$/набл. · ЗАВИШАВАНЕ %+.3f$ (%.1f%% от |бар|)"
          % (pA / n, pB / n, (pA - pB) / n, 100 * abs(pA - pB) / max(abs(pB), 1e-9)))
    for (b, a), c in sorted(видове.items(), key=lambda x: -x[1]):
        знак = "мозък по-добър" if {"стоп": -1, "цел2": 1, "None": 0}[a] > {"стоп": -1, "цел2": 1, "None": 0}[b] else "мозък по-лош"
        print("   бар=%-5s → мозък=%-5s : %4d (%.1f%%)  %s" % (b, a, c, 100 * c / n, знак))
    if стъпка == 1:
        print("   барове, в които СТОП и ЦЕЛ2 са ударени в един и същ бар: %d" % дв)

# --- мъртъв ли е редът на проверките при СКАЛАРНА цена? ---
print("\n=== коментарът на 1582-83 («стопът се проверява ПРЪВ… инак следенето би се хвалило») ===")
брой = 0
for r in R:
    зн = 1 if r["посока"] == "long" else -1
    for p in np.arange(r["вход"] - 60, r["вход"] + 60, 0.01):
        c_sl = (p - r["стоп"]) * зн <= 0
        c_t2 = r.get("цел2") is not None and (p - r["цел2"]) * зн >= 0
        c_t1 = (p - r["цел1"]) * зн >= 0
        if c_sl and (c_t1 or c_t2):
            брой += 1
print("   цени, при които ЕДНА скаларна проба удря и стоп, и цел (12000 проби × 15 записа): %d" % брой)
print("   → редът на проверките е взаимно изключващ се: няма какво да подрежда.")
