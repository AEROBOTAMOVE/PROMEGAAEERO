import numpy as np, pandas as pd
def make(true_basis, price=4639.0, ndays=30):
    idx = pd.date_range("2026-07-20", periods=ndays, freq="D", tz="UTC")
    ii=[]
    for d in idx: ii += list(pd.date_range(d, periods=6, freq="1h"))
    ii = pd.DatetimeIndex(ii)
    intra = pd.DataFrame({"Close": np.full(len(ii), price)}, index=ii)
    last = intra.resample("1D").agg(Close=("Close","last")).dropna()
    daily = pd.DataFrame({"Close": last["Close"].values + true_basis}, index=last.index)
    return intra, daily
