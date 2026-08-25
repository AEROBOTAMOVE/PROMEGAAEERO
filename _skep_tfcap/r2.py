# -*- coding: utf-8 -*-
import sys, os, json
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, D); sys.path.insert(0, os.path.join(D,"_skep_tfcap"))
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import live_bot as lb
from r1helper import make

for tb, price in ((-238.0, 4639.0), (-61.6, 4639.0), (-90.0, 4639.0), (-150.0, 4639.0), (-238.0, 2000.0)):
    state = {"tf_basis_g": -61.599}
    intra, daily = make(tb, price)
    осв = None
    for r in range(1, 41):
        notes=[]
        v = lb._tf_basis(state, "tf_basis_g", intra, daily, notes)
        if осв is None and abs(v - (-61.599)) > 1e-6:
            осв = r
    _ц = price + tb
    cap = max(lb.TF_BASIS_CAP, lb.TF_BASIS_CAP_PCT*abs(_ц))
    print("истина %+8.1f$ · цена %.0f · таван %.2f · отхвърля? %s · освободен на рън %s · крайна стойност %+.3f"
          % (tb, price, cap, abs(tb) > cap, осв, state["tf_basis_g"]))
