# -*- coding: utf-8 -*-
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("TG_TOKEN","x"); os.environ.setdefault("TG_CHAT","x")
import pandas as pd, numpy as np
import live_bot as lb

print("TF_BASIS_CAP      =", lb.TF_BASIS_CAP)
print("TF_BASIS_CAP_PCT  =", lb.TF_BASIS_CAP_PCT)
print("TF_BASIS_STUCK_N  =", lb.TF_BASIS_STUCK_N)

def построй(цена_дневна, базис, дни=30):
    """intra = 5-мин барове; daily = дневни. median(Close_d - Close) == базис."""
    idx = pd.date_range("2026-07-20", periods=дни, freq="D", tz="UTC")
    d = pd.DataFrame({"Close": [цена_дневна]*дни}, index=idx)
    # intra: по 3 бара на ден, последният = Close_d - базис
    ii, vv = [], []
    for t in idx:
        for k in range(3):
            ii.append(t + pd.Timedelta(hours=k))
            vv.append(цена_дневна - базис)
    i = pd.DataFrame({"Close": vv}, index=pd.DatetimeIndex(ii))
    return i, d

# живото състояние, дословно от live/meta.json
meta = json.load(open("live/meta.json", encoding="utf-8"))
state = {"tf_basis_g": meta["tf_basis_g"],
         "tf_basis_g_отказ": meta.get("tf_basis_g_отказ", 0),
         "tf_basis_g_отказани": meta.get("tf_basis_g_отказани", [])}
print("старт tf_basis_g =", state["tf_basis_g"])

ЦЕНА = 4639.0
ИСТИНА = -150.0            # точно сценария на находката
intra, daily = построй(ЦЕНА, ИСТИНА)
_ц = ЦЕНА
print("_cap на този бар  = max(%.1f, %.4f*%.1f) = %.2f" % (
    lb.TF_BASIS_CAP, lb.TF_BASIS_CAP_PCT, _ц, max(lb.TF_BASIS_CAP, lb.TF_BASIS_CAP_PCT*_ц)))
print()
for r in range(1, 31):
    notes = []
    v = lb._tf_basis(state, "tf_basis_g", intra, daily, notes)
    if r <= 3 or 10 <= r <= 14 or r >= 28:
        print("рън %2d: върнато %+8.3f · памет %+8.3f · отказ=%s · набл=%d"
              % (r, v, state["tf_basis_g"], state.get("tf_basis_g_отказ"),
                 len(state.get("tf_basis_g_отказани") or [])))
        for n in notes: print("        →", n)
print()
print("ФИНАЛНО:", state["tf_basis_g"], "· истина:", ИСТИНА)
