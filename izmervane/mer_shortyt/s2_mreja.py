# -*- coding: utf-8 -*-
"""s2_mreja.py - 152 SHORT geometries against the blind short, paired entry by
entry, with a family-wise (max-t bootstrap) correction for having tried 152.

Also runs the WHOLE pipeline on pure noise (blind draws split in half, so the
true difference is exactly zero) - if the correction declares a winner there,
nothing it says about the real grid is worth anything."""
import sys, time, json
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import eng, baza, mreja

t0 = time.time()
B = eng.tape()
S = baza.shorts()
G = mreja.family()
ng = len(G)
ridx, rpx, bidx, bpx = baza.make_sets(B, S)
real, blind = baza.run_grid(B, G, ridx, rpx, bidx, bpx)
print("[sim] %.0fs" % (time.time() - t0))

d, bm = baza.paired(real, blind)
ok = ~np.isnan(real).any(0) & ~np.isnan(bm).any(0)
print("[valid] %d of %d short entries valid for ALL %d geometries (%d dropped)"
      % (ok.sum(), len(ok), ng, (~ok).sum()))
dayid = B["dord"][ridx][ok]
bt = baza.Boot(dayid)
print("[boot] %d trading days, %d block-bootstrap replicates" % (bt.k, bt.reps))

mD, loD, hiD, seD, tD, bmD = bt.stats(d[:, ok])          # delta vs blind
mR, loR, hiR, seR, tR, _   = bt.stats(real[:, ok])        # absolute
mB, loB, hiB, seB, tB, _   = bt.stats(bm[:, ok])          # blind
pfw, Mnull = bt.maxt_p(mD, seD, bmD)

np.save(HERE / "_cache" / "res_d.npy", d[:, ok])
np.save(HERE / "_cache" / "res_real.npy", real[:, ok])
np.save(HERE / "_cache" / "res_blind.npy", bm[:, ok])
np.save(HERE / "_cache" / "res_ok.npy", ok)

order = np.argsort(-mD)
print("\n" + "=" * 118)
print("ТАБЛИЦА 1 · НАЙ-ДОБРИТЕ 20 ОТ %d ГЕОМЕТРИИ, подредени по РАЗЛИКА срещу слепия шорт" % ng)
print("=" * 118)
print("%-32s %9s %9s %9s %-20s %7s %7s" %
      ("геометрия", "реален$", "сляп$", "РАЗЛИКА", "95% инт. на разликата", "t", "p_семейно"))
print("-" * 118)
for gi in order[:20]:
    print("%-32s %+9.4f %+9.4f %+9.4f  [%+.3f, %+.3f] %7.2f %7.3f" %
          (G[gi]["name"], mR[gi], mB[gi], mD[gi], loD[gi], hiD[gi], tD[gi], pfw[gi]))
print("-" * 118)
print("НАЙ-ЛОШИТЕ 5:")
for gi in order[-5:]:
    print("%-32s %+9.4f %+9.4f %+9.4f  [%+.3f, %+.3f] %7.2f %7.3f" %
          (G[gi]["name"], mR[gi], mB[gi], mD[gi], loD[gi], hiD[gi], tD[gi], pfw[gi]))

nz = int((loD > 0).sum()); nzneg = int((hiD < 0).sum())
print("\nгеометрии с интервал ИЗЦЯЛО НАД нулата (без поправка за 152 проверки): %d" % nz)
print("геометрии с интервал ИЗЦЯЛО ПОД нулата (без поправка):                  %d" % nzneg)
print("геометрии с p_семейно < 0.05 (max-t поправка за 152):                    %d" % int((pfw < 0.05).sum()))
print("геометрии с РЕАЛЕН нет над нулата и интервал над нулата:                 %d" % int((loR > 0).sum()))

print("\n" + "=" * 118)
print("ТАБЛИЦА 2 · ПО БЛОКОВЕ - най-доброто във всеки от шестте систематични опита")
print("=" * 118)
print("%-14s %4s %-30s %9s %9s %-20s %7s" %
      ("блок", "бр.", "най-добрата в блока", "реален$", "РАЗЛИКА", "95% инт.", "p_сем"))
print("-" * 118)
for blok in ["A 1цел 5д", "B 1цел 1д", "C 1цел мин", "D стълба", "E BE-движение", "F трал"]:
    ids = [i for i in range(ng) if G[i]["blok"] == blok]
    gi = ids[int(np.argmax(mD[ids]))]
    print("%-14s %4d %-30s %+9.4f %+9.4f  [%+.3f, %+.3f] %7.3f" %
          (blok, len(ids), G[gi]["name"], mR[gi], mD[gi], loD[gi], hiD[gi], pfw[gi]))

# ---------------------------------------------------------------- НЕГАТИВЕН КОНТРОЛ
print("\n" + "=" * 118)
print("ТАБЛИЦА 3 · НЕГАТИВЕН КОНТРОЛ - същите 152 геометрии върху ЧИСТ ШУМ")
print("(слепите тегления, разцепени на две половини по 6; истинската разлика е ТОЧНО нула)")
print("=" * 118)
with np.errstate(invalid="ignore"):
    nA = np.nanmean(blind[:, :6, :], axis=1)
    nB = np.nanmean(blind[:, 6:, :], axis=1)
dn = (nA - nB)[:, ok]
mN, loN, hiN, seN, tN, bmN = bt.stats(dn)
pfwN, _ = bt.maxt_p(mN, seN, bmN)
oN = np.argsort(-mN)
print("%-32s %9s %-20s %7s %7s" % ("най-добрата НА ШУМА", "РАЗЛИКА", "95% интервал", "t", "p_сем"))
for gi in oN[:3]:
    print("%-32s %+9.4f  [%+.3f, %+.3f] %7.2f %7.3f" % (G[gi]["name"], mN[gi], loN[gi], hiN[gi], tN[gi], pfwN[gi]))
print("\nна шума: интервал над нулата БЕЗ поправка = %d от %d   ·   с max-t поправка p<0.05 = %d от %d"
      % (int((loN > 0).sum()), ng, int((pfwN < 0.05).sum()), ng))
print("(ако второто не е 0, поправката не работи и таблица 1 не важи)")

json.dump({"n_geom": ng, "n_entries": int(ok.sum()), "n_days": bt.k,
           "names": [g["name"] for g in G], "blok": [g["blok"] for g in G],
           "real": mR.tolist(), "blind": mB.tolist(), "delta": mD.tolist(),
           "lo": loD.tolist(), "hi": hiD.tolist(), "t": tD.tolist(), "pfw": pfw.tolist(),
           "real_lo": loR.tolist(), "real_hi": hiR.tolist(),
           "noise_best_delta": float(mN.max()), "noise_nz": int((loN > 0).sum()),
           "noise_pfw_min": float(pfwN.min())},
          open(HERE / "rez_mreja.json", "w"), indent=1)
print("\n[общо %.0fs]" % (time.time() - t0))
