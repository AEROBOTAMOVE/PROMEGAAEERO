# -*- coding: utf-8 -*-
"""СКЕПТИК·ПОСЛЕДИЦА — стъпка 8: щом схемата на доставчика се смени ЗАНАВСЕГДА
(единственият начин `except` да замрази ЗАВИНАГИ) — мълчи ли ботът, или умира шумно?"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H, live_bot as lb
H.patch()
lb._spot = lambda instr="XAU/USD", **k: {"bid":4599.8,"ask":4600.2,"mid":4600.0,"src":"swq","age_sec":1.0}
добър = H.fake_yf
def преименувана_колона(sym, period="2y", interval="1d"):
    df = добър(sym, period, interval)
    return df.rename(columns={"Close": "close"})     # доставчикът смени името
lb._yf = преименувана_колона
H.CFG.update(gold_end="2026-08-21", gold_px=4600.0, spot_mid=4600.0, intra_end="2026-08-21 12:00")
H.set_now("2026-08-21T12:05:00+00:00")
d = H.fresh("_skep_posl5/shema")
try:
    H.run(d)
    print("ботът МИНА мълчаливо (лошо)")
except Exception as e:
    print("рънът УМИРА ШУМНО:", type(e).__name__ + ":", str(e)[:120])
    print("мястото:", traceback.format_exc().strip().splitlines()[-3])
