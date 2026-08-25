# -*- coding: utf-8 -*-
"""РЕШАВАЩИЯТ опит — БЕЗ базис изобщо.
Двата тракера се пускат върху ЕДНА И СЪЩА фючърсна серия:
  A) «мозъчният»  — само Close на всеки 5м бар (една скаларна проба на рън)
  B) «реалният»   — High/Low на същите барове (track_trade)
Геометрията на всяко от 15-те живи наблюдения се пренася 1:1 (разстояния от входа),
входът се закотвя за фючърсния Close в мига на отваряне. Базисът се съкращава.
"""
import sys, io, json, os
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd, numpy as np
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, "sw_ob41.py"), encoding="utf-8").read().split("def scal(")[0])

C = B["Close"].dropna()

def прогон(зн, вход, стоп, ц1, ц2, t0, макс_ч=48):
    """връща (изход_скалар, кога_скалар, изход_бар, кога_бар, дълбочина_пропусната)"""
    sub = B.loc[(B.index > t0) & (B.index <= t0 + pd.Timedelta(hours=макс_ч))]
    sc = sb = None; tsc = tsb = None; проп = 0.0
    ц1s = ц1b = False
    for ts, r in sub.iterrows():
        hi, lo, cl = float(r["High"]), float(r["Low"]), float(r["Close"])
        if any(pd.isna(x) for x in (hi, lo, cl)):
            continue
        if sb is None:                                   # B: по High/Low, стопът пръв
            if (lo <= стоп) if зн == 1 else (hi >= стоп):
                sb, tsb = "стоп", ts
            elif ц2 is not None and ((hi >= ц2) if зн == 1 else (lo <= ц2)):
                sb, tsb = "цел2", ts
            elif not ц1b and ((hi >= ц1) if зн == 1 else (lo <= ц1)):
                ц1b = True
        if sc is None:                                   # A: само Close
            if (cl <= стоп) if зн == 1 else (cl >= стоп):
                sc, tsc = "стоп", ts
            elif ц2 is not None and ((cl >= ц2) if зн == 1 else (cl <= ц2)):
                sc, tsc = "цел2", ts
            elif not ц1s and ((cl >= ц1) if зн == 1 else (cl <= ц1)):
                ц1s = True
            else:
                проп = max(проп, ((стоп - lo) if зн == 1 else (hi - стоп)))
        if sc is not None and sb is not None:
            break
    return sc, tsc, sb, tsb, проп

print("\n%-3s %-5s %-17s %7s | %-6s %-16s | %-6s %-16s  %s"
      % ("№", "пос", "отворен", "стоп$", "A close", "кога", "B High/Low", "кога", "присъда"))
разл = 0; хвали = 0; кастри = 0
for i, rec in enumerate(R, 1):
    зн = 1 if rec["посока"] == "long" else -1
    t0 = pd.Timestamp(rec["отворен"])
    поз = C.index[np.searchsorted(C.index, t0)]
    if abs((поз - t0).total_seconds()) > 3600:
        print("%-3d пропуснат — няма фючърсна котировка около %s" % (i, t0)); continue
    e = float(C.loc[поз])
    dсл = rec["стоп"] - rec["вход"]; d1 = rec["цел1"] - rec["вход"]
    d2 = (rec["цел2"] - rec["вход"]) if rec.get("цел2") is not None else None
    sc, tsc, sb, tsb, проп = прогон(зн, e, e + dсл, e + d1, (e + d2) if d2 is not None else None, поз)
    м = ""
    if sc != sb:
        разл += 1
        печ = {"стоп": dсл * зн, "цел2": (d2 * зн if d2 is not None else 0), None: 0}
        if печ.get(sc, 0) > печ.get(sb, 0):
            хвали += 1; м = "⚠ A СЕ ХВАЛИ (+%.2f срещу %+.2f)" % (печ[sc], печ[sb])
        else:
            кастри += 1; м = "A се кастри (%+.2f срещу %+.2f)" % (печ[sc], печ[sb])
    print("%-3d %-5s %-17s %7.2f | %-6s %-16s | %-6s %-16s  %s"
          % (i, rec["посока"], rec["отворен"], abs(dсл), str(sc), str(tsc)[:16],
             str(sb), str(tsb)[:16], м))
print("\nразлики %d/15  ·  «хвали се» %d  ·  «кастри се» %d" % (разл, хвали, кастри))

# ── и общата картина: 3000 случайни входа със същата геометрия ──
rng = np.random.default_rng(7)
геом = [(1 if r["посока"] == "long" else -1, r["стоп"] - r["вход"], r["цел1"] - r["вход"],
         (r["цел2"] - r["вход"]) if r.get("цел2") is not None else None) for r in R]
идx = C.index[(C.index >= pd.Timestamp("2026-07-21")) & (C.index <= pd.Timestamp("2026-08-18"))]
n = A_луч = B_луч = равни = 0
пари_A = пари_B = 0.0
for _ in range(3000):
    зн, dсл, d1, d2 = геом[rng.integers(len(геом))]
    t0 = идx[rng.integers(len(идx))]
    e = float(C.loc[t0])
    sc, _, sb, _, _ = прогон(зн, e, e + dсл, e + d1, (e + d2) if d2 is not None else None, t0)
    if sc is None and sb is None:
        continue
    n += 1
    p = {"стоп": abs(dсл) * -1, "цел2": (abs(d2) if d2 is not None else 0.0), None: 0.0}
    пари_A += p.get(sc, 0.0); пари_B += p.get(sb, 0.0)
    if sc == sb:
        равни += 1
    elif p.get(sc, 0) > p.get(sb, 0):
        A_луч += 1
    else:
        B_луч += 1
print("\nМОНТЕ-КАРЛО, %d наблюдения със СЪЩАТА геометрия върху истински 5м злато:" % n)
print("  еднакъв изход: %d (%.1f%%)   A(мозък) по-добър: %d (%.1f%%)   B(бар) по-добър: %d (%.1f%%)"
      % (равни, 100 * равни / n, A_луч, 100 * A_луч / n, B_луч, 100 * B_луч / n))
print("  средно на наблюдение:  A(мозък) %+.3f$   B(бар) %+.3f$   ЗАВИШАВАНЕ %+.3f$/набл."
      % (пари_A / n, пари_B / n, (пари_A - пари_B) / n))
