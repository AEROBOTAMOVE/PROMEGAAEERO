# -*- coding: utf-8 -*-
"""Колко дълго трае «доларът и лихвите се карат» — мерено, не гадано."""
import sys, numpy as np, pandas as pd
sys.argv=["x"]
d = pd.read_parquet("f21_dni.parquet")
print("колони:", list(d.columns))
print("редове:", len(d), "от", d.index.min() if not isinstance(d.index, pd.RangeIndex) else d.iloc[0].to_dict())
print(d.head(3).to_string())
