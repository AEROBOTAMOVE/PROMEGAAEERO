# -*- coding: utf-8 -*-
"""РЕАЛНИЯТ ПЪТ: _прочети (7 блока) + f_сливане, точно както го вика ботът."""
import sys, os, json, time, warnings, collections
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.abspath("."))
import numpy as np, pandas as pd
import brain.chart_brain as CB
import brain.b_сливане as SL

P = r'C:/Users/User/Downloads/ЛОЦО/f6_data/parquet/xauusd_15min_bid_ask.parquet'
raw = pd.read_parquet(P)
df = pd.DataFrame({
    "open":  raw["open_bid"].to_numpy(float),
    "high":  raw["high_bid"].to_numpy(float),
    "low":   raw["low_bid"].to_numpy(float),
    "close": raw["close_bid"].to_numpy(float),
    "volume":raw["volume_bid"].to_numpy(float),
}, index=pd.DatetimeIndex(raw["timestamp_utc"].to_numpy()))
df = df[~df.index.duplicated()].sort_index()

ОТ = os.environ.get("ОТ", "2026-05-29")
пълен = df.loc[:"2026-07-07"]
идx = пълен.index
start = int(np.searchsorted(идx.values, np.datetime64(ОТ + "T00:00:00")))
край = len(пълен)
print("обход:", идx[start], "->", идx[-1], " барове:", край - start)

изход = []
t0 = time.time()
for k in range(start, край):
    d = пълен.iloc[max(0, k - CB.ПРОЗОРЕЦ + 1): k + 1]
    if len(d) < CB.МИН_БАРОВЕ:
        continue
    R, _, гр = CB._прочети(d, "15м")
    a = SL._atr(d)
    поводи = SL._поводи(len(d) - 1, d, R)
    if not поводи:
        continue
    for лонг in (True, False):
        if not any(p["лонг"] == лонг for p in поводи):
            continue
        точки, съвп, всички, сур = SL._брои(лонг, поводи, d, R, a)
        изход.append(dict(
            t=str(d.index[-1]), лонг=лонг, точки=int(точки),
            Z1=bool(всички["Z1_дискаунт_премиум"]),
            Z2=bool(всички["Z2_хоризонти"]),
            Z2b=bool(всички["Z2b_единодушно"]),
            Z3=bool(всички["Z3_извън_стойността"]),
            всички={к: bool(v) for к, v in всички.items()},
        ))
    if (k - start) % 200 == 0:
        print(f"  {k-start}/{край-start}  {time.time()-t0:.0f}s  поводи={len(изход)}", flush=True)
print("готово за", round(time.time() - t0), "сек · посока-карти:", len(изход))
json.dump(изход, open("sw_full.json", "w", encoding="utf-8"), ensure_ascii=False)
