# -*- coding: utf-8 -*-
"""s5 - three loose ends.

(1) DUPLICATES: how many of the 152 are actually the same trade set (a trail
    tighter than the initial stop makes that stop irrelevant), so the "152" that
    goes into the correction is honest about how many DISTINCT things were tried.
(2) NO STOP AT ALL - the endpoint of "wider stop", declared as ONE post-hoc check.
(3) MIRROR: the SAME 152 geometries on the 3525 LONG entries.  A long on the
    real tape is exactly a short on the NEGATED tape (bid<->ask roles swap), so
    the identical, already-verified engine can run it - and the identity is
    checked against gh._one_trade before it is used.
"""
import sys, time, json
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng, baza, mreja
import geom_harness as gh

t0 = time.time()
B = eng.tape()
G = mreja.family()
ng = len(G)

# ---------------------------------------------------------------- (1) duplicates
d = np.load(HERE / "_cache" / "res_real.npy")
sig = {}
for i in range(ng):
    sig.setdefault(np.nan_to_num(d[i]).tobytes(), []).append(i)
dups = {k: v for k, v in sig.items() if len(v) > 1}
print("### (1) РАЗЛИЧНИ ЛИ СА 152-те")
print("  различни набора сделки: %d от %d геометрии" % (len(sig), ng))
for v in list(dups.values()):
    print("     еднакви: %s" % " | ".join(G[i]["name"] for i in v))

# ---------------------------------------------------------------- (2) no stop
S = baza.shorts()
ridx, rpx, bidx, bpx = baza.make_sets(B, S)
NOSTOP = [eng.G("без стоп, 5д", [], 1e9, days=5), eng.G("без стоп, 1д", [], 1e9, days=1)]
r2, b2 = baza.run_grid(B, NOSTOP, ridx, rpx, bidx, bpx, verbose=False)
dd2, bm2 = baza.paired(r2, b2)
ok2 = ~np.isnan(r2).any(0) & ~np.isnan(bm2).any(0)
bt2 = baza.Boot(B["dord"][ridx][ok2])
print("\n### (2) НАЙ-ШИРОКИЯТ ВЪЗМОЖЕН СТОП - НИКАКЪВ (post-hoc, 2 проверки)")
print("  %-16s %10s %-22s %10s %-22s" % ("", "реален$", "95% инт.", "разлика", "95% инт."))
for i, g in enumerate(NOSTOP):
    m, lo, hi, se, t, _ = bt2.stats(np.vstack([r2[i][ok2], dd2[i][ok2]]))
    print("  %-16s %+10.4f  [%+.3f, %+.3f] %+10.4f  [%+.3f, %+.3f]"
          % (g["name"], m[0], lo[0], hi[0], m[1], lo[1], hi[1]))

# ---------------------------------------------------------------- (3) mirror
def negate(B):
    N = dict(B)
    N["ha"] = -B["lb"]; N["la"] = -B["hb"]; N["oa"] = -B["ob"]; N["ca"] = -B["cb"]
    N["ob"] = -B["oa"]
    N["hb"] = -B["la"]; N["lb"] = -B["ha"]; N["cb"] = -B["ca"]
    return N

NB = negate(B)
E = pd.read_parquet(baza.ENTRIES)
LO = E[E.direction == "long"].reset_index(drop=True)
lidx = LO.bar_index.values.astype(np.int64); lpx = LO.entry_px.values.astype(float)

print("\n### (3а) СВЕРКА на огледалото срещу gh._one_trade върху 3525 ЛОНГ входа")
allok = True
for nm, g, dd in [("стълба 7.5/12/20 SL20 BE 5д", eng.G("x", [(1/3,7.5),(1/3,12.0),(1/3,20.0)], 20.0, True, days=5), 5),
                  ("TP10 SL30 5д", eng.G("x", [(1.0,10.0)], 30.0, days=5), 5),
                  ("TP30 SL10 1д", eng.G("x", [(1.0,30.0)], 10.0, days=1), 1)]:
    gh.TIME_EXIT_DAYS = dd
    ghg = {"name": nm, "tps": g["tps"], "sl": g["sl"], "be_after_tp1": g["be_after_tp1"]}
    mi = np.full(len(LO), np.nan); rf = np.full(len(LO), np.nan); kb = 0
    for p in range(len(LO)):
        r1 = eng.one_short(int(lidx[p]), -float(lpx[p]), g, NB)
        rr = gh._one_trade(int(lidx[p]), "long", float(lpx[p]), ghg, B)
        if r1: mi[p] = r1["net"]
        if rr: rf[p] = rr["net"]
        if (r1 is None) != (rr is None) or (r1 and r1["kind"] != rr["kind"]): kb += 1
    e = np.abs(mi - rf); bad = int(np.nansum(e > 1e-9)); allok &= (bad == 0 and kb == 0)
    print("  %-30s max|dnet|=%.2e  mismatch=%d  kind=%d  mean=%+.4f" % (nm, float(np.nanmax(e)), bad, kb, float(np.nanmean(rf))))
gh.TIME_EXIT_DAYS = 5
print("  огледалото:", "PASS" if allok else "FAIL - нататък не важи")
assert allok

lb = eng.blind_idx(lidx, B, ndraw=baza.NDRAW, seed=baza.SEED_BLIND)
realL, blindL = baza.run_grid(NB, G, lidx, -lpx, lb, -B["oa"][lb], verbose=False)
dL, bmL = baza.paired(realL, blindL)
okL = ~np.isnan(realL).any(0) & ~np.isnan(bmL).any(0)
btL = baza.Boot(B["dord"][lidx][okL])
mD, loD, hiD, seD, tD, bmD = btL.stats(dL[:, okL])
mR, loR, hiR, _, _, _ = btL.stats(realL[:, okL])
pfw, _ = btL.maxt_p(mD, seD, bmD)
o = np.argsort(-mD)
print("\n" + "=" * 112)
print("ТАБЛИЦА 7 · ОГЛЕДАЛОТО - СЪЩИТЕ 152 геометрии върху %d ЛОНГ входа (контрол дали търсенето може да спечели ИЗОБЩО)" % okL.sum())
print("=" * 112)
print("%-32s %10s %10s %-22s %8s" % ("геометрия", "реален$", "разлика", "95% инт. на разликата", "p_сем"))
for i in o[:6]:
    print("%-32s %+10.4f %+10.4f  [%+.3f, %+.3f] %8.3f" % (G[i]["name"], mR[i], mD[i], loD[i], hiD[i], pfw[i]))
print("...")
for i in o[-3:]:
    print("%-32s %+10.4f %+10.4f  [%+.3f, %+.3f] %8.3f" % (G[i]["name"], mR[i], mD[i], loD[i], hiD[i], pfw[i]))
print("\nЛОНГ: интервал над нулата без поправка = %d от 152 · с max-t поправка p<0.05 = %d · реален нет > 0 = %d"
      % (int((loD > 0).sum()), int((pfw < 0.05).sum()), int((mR > 0).sum())))
print("ШОРТ (за сравнение):                   0 от 152 ·                        0 ·               0")
print("\n[%.0fs]" % (time.time() - t0))
