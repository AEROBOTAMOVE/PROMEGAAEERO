# -*- coding: utf-8 -*-
import sys, os, json, importlib.util
import numpy as np, pandas as pd
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, D)
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import live_bot as lb

print("TF_BASIS_CAP =", lb.TF_BASIS_CAP, "| PCT =", lb.TF_BASIS_CAP_PCT, "| STUCK_N =", lb.TF_BASIS_STUCK_N)

def make(true_basis, price=4639.0, ndays=30):
    idx = pd.date_range("2026-07-20", periods=ndays, freq="D", tz="UTC")
    # интрадей: 6 бара на ден
    ii = []
    for d in idx:
        ii += list(pd.date_range(d, periods=6, freq="1h"))
    ii = pd.DatetimeIndex(ii)
    intra = pd.DataFrame({"Close": np.linspace(price-20, price, len(ii)),
                          "High": np.linspace(price-20, price, len(ii))+1,
                          "Low": np.linspace(price-20, price, len(ii))-1}, index=ii)
    # дневен Close = интрадей последен на деня + true_basis
    last = intra.resample("1D").agg(Close=("Close","last")).dropna()
    daily = pd.DataFrame({"Close": last["Close"].values + true_basis}, index=last.index)
    return intra, daily

# живото състояние от live/meta.json
meta = json.load(open(os.path.join(D,"live","meta.json"), encoding="utf-8"))
state = {"tf_basis_g": meta["tf_basis_g"]}
print("старт от живото tf_basis_g =", state["tf_basis_g"])
intra, daily = make(150.0)
_ц = float(daily["Close"].iloc[-1])
print("цена на бара (Close_d) = %.1f  ->  _cap = max(%.1f, %.2f*%.1f) = %.2f"
      % (_ц, lb.TF_BASIS_CAP, lb.TF_BASIS_CAP_PCT, _ц, max(lb.TF_BASIS_CAP, lb.TF_BASIS_CAP_PCT*_ц)))
for r in range(1, 31):
    notes = []
    v = lb._tf_basis(state, "tf_basis_g", intra, daily, notes)
    if r <= 3 or r >= 11 and r <= 15 or r >= 28:
        print("рън %2d: върнато %+9.3f · в паметта %+9.3f · брояч=%s · набл=%d"
              % (r, v, state.get("tf_basis_g"), state.get("tf_basis_g_отказ"),
                 len(state.get("tf_basis_g_отказани") or [])))
        for n in notes: print("        бележка:", n)
print("ключове в state:", sorted(state.keys()))
