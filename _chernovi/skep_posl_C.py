# -*- coding: utf-8 -*-
"""СКЕПТИК·ПОСЛЕДИЦА — стъпка 3: КОЛКО МЕСТИ ДЪСКАТА замразеният базис,
и какво прави ботът, когато интрадей данните ги няма (единственият достижим клон)."""
import sys, os, io, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H

import live_bot as lb
from pathlib import Path

H.patch()
lb._spot = lambda instr="XAU/USD", **k: (None if H.CFG.get("spot_none") else {"bid": round((H.CFG.get("spot_mid_s",69.0) if instr!="XAU/USD" else H.CFG.get("spot_mid",4600.0))-0.2,3), "ask": round((H.CFG.get("spot_mid_s",69.0) if instr!="XAU/USD" else H.CFG.get("spot_mid",4600.0))+0.2,3), "mid": round((H.CFG.get("spot_mid_s",69.0) if instr!="XAU/USD" else H.CFG.get("spot_mid",4600.0)),3), "src": "swq", "age_sec": 1.0})
H.CFG.update(gold_end="2026-08-21", gold_px=4600.0, spot_mid=4600.0, intra_end="2026-08-21 12:00")
H.set_now("2026-08-21T12:05:00+00:00")
_истински = lb._tf_basis

print("=== C1 · ЕДНА И СЪЩА ДАННА, РАЗЛИЧЕН tf_adj (замразен срещу истински) ===")
резултати = {}
for X in (None, -61.6, -48.55, -25.5, -3.851, 0.0):
    if X is None:
        lb._tf_basis = _истински
        етикет = "истински (смята се)"
    else:
        lb._tf_basis = (lambda v: (lambda state, key, intra, daily, notes, days=20, cap=None:
                                   (v if key == "tf_basis_g" else _истински(state, key, intra, daily, notes, days=days, cap=cap))))(X)
        етикет = f"закован {X:+.3f}"
    d = H.fresh(f"_skep_posl5/{'ist' if X is None else str(X).replace('.','_').replace('-','m')}")
    H.run(d)
    j = H.last_journal(d)
    борд = j.get("board") or j.get("дъска")
    резултати[етикет] = (борд, j.get("dir") or j.get("посока"), j.get("class") or j.get("клас"),
                         len(H.SENT), j.get("tf_basis_g"))
    print(f"{етикет:24s} | посока={резултати[етикет][1]} клас={резултати[етикет][2]} "
          f"| карти={резултати[етикет][3]} | борд={борд}")

print()
print("=== C2 · КЛЮЧОВЕ В ДНЕВНИКА (за да не гадая имена) ===")
lb._tf_basis = _истински
d = H.fresh("_skep_posl5/keys"); H.run(d)
j = H.last_journal(d)
print(sorted(j.keys()))
