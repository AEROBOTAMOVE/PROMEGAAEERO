# -*- coding: utf-8 -*-
import sys, os, json, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.abspath("."))
import numpy as np, pandas as pd
import brain.b_диапазон as B7

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
assert df["close"].notna().all(), "NaN в цените!"
print("бара:", len(df), df.index[0], "->", df.index[-1])

sub = df.iloc[-6000:].copy()
start = 3000
recs = []
for k in range(start, len(sub)):
    r = B7.f_диапазон(sub, as_of=k)
    if r.get("празен"):
        continue
    сг = r.get("съгласие") or {}
    об = r.get("обем") or {}
    recs.append(dict(
        t=str(r["време"]), посока=r.get("посока"),
        главен=r["диапазон"]["състояние"],
        поз=r["диапазон"]["позиция_пц"],
        водеща=сг.get("водеща"), мнозинство=int(сг.get("мнозинство") or 0),
        единодушно=bool(сг.get("единодушно")),
        n_диск=int(сг.get("дискаунт") or 0), n_прем=int(сг.get("премиум") or 0),
        изм_долу=bool(об.get("изместена_надолу")), изм_горе=bool(об.get("изместена_нагоре")),
    ))
print("моменти:", len(recs))
json.dump(recs, open("sw_z_probe.json","w",encoding="utf-8"), ensure_ascii=False)
print("пример:", recs[100])
