# -*- coding: utf-8 -*-
"""СТРАНИЧНО: сребърният try глътне ли се, `s_trade` остава НЕДЕФИНИРАН,
а златната карта го чете. Пускам: САМО SI=F интрадей пада, златото е живо."""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H, live_bot as lb
H.patch()
lb._spot = lambda instr="XAU/USD", **k: {"bid":4599.8,"ask":4600.2,"mid":4600.0,"src":"swq","age_sec":1.0} \
    if instr=="XAU/USD" else {"bid":68.8,"ask":69.2,"mid":69.0,"src":"swq","age_sec":1.0}
добър = H.fake_yf
def без_сребро_интрадей(sym, period="2y", interval="1d"):
    if sym == "SI=F" and interval == "5m":
        raise RuntimeError("Yahoo мълчи за SI=F 5m")
    return добър(sym, period, interval)
lb._yf = без_сребро_интрадей
H.CFG.update(gold_end="2026-08-21", gold_px=4600.0, gold_step=0.5, spot_mid=4600.0,
             intra_end="2026-08-21 12:00")
H.set_now("2026-08-21T12:05:00+00:00")
d = H.fresh("_skep_posl5/bez_srebro")
try:
    H.run(d)
    j = H.last_journal(d)
    print("рънът МИНА. борд:", j.get("board"))
    print("статус:", j.get("status"), "| карти:", len(H.SENT))
except Exception as e:
    tb = traceback.format_exc().strip().splitlines()
    print("рънът ГРЪМНА:", type(e).__name__ + ":", e)
    print("\n".join(tb[-4:]))
