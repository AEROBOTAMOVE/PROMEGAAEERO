# -*- coding: utf-8 -*-
"""СКЕПТИК·ПОСЛЕДИЦА — стъпка 2: ДОСТИЖИМ ЛИ Е `except`-ът през ИСТИНСКАТА тръба?
Всичко, което влиза в _tf_basis, минава първо през lb._yf. Пускам НАИСТИНА _yf
с подменен yfinance и гледам какво излиза."""
import sys, os, io, types, time as _t
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, numpy as np
import live_bot as lb
_t.sleep = lambda *a, **k: None            # без чакане в _retry

idx = pd.date_range("2026-07-20", periods=300, freq="5min", tz="America/New_York")
base = pd.DataFrame({"Open": 4600.0, "High": 4601.0, "Low": 4599.0,
                     "Close": np.linspace(4600, 4650, len(idx)), "Volume": 10}, index=idx)

def подай(df):
    m = types.ModuleType("yfinance")
    m.download = lambda *a, **k: df
    sys.modules["yfinance"] = m

случаи = {
    "1. MultiIndex колони (group_by на yfinance)":
        base.set_axis(pd.MultiIndex.from_product([base.columns, ["GC=F"]]), axis=1),
    "2. преименувана колона Close -> close":
        base.rename(columns={"Close": "close"}),
    "3. tz-aware индекс (NY), различен от дневния (naive)":
        base,
    "4. индексът е низове, не дати":
        base.set_axis([str(x) for x in base.index], axis=0),
    "5. празна рамка":
        base.iloc[0:0],
}
daily_idx = pd.date_range("2026-07-20", periods=30, freq="D")
daily = pd.DataFrame({"Close": np.linspace(4560, 4610, 30)}, index=daily_idx)

for име, df in случаи.items():
    подай(df)
    print("---", име)
    try:
        out = lb._yf("GC=F", "60d", "5m")
        print("   _yf МИНА: колони =", list(out.columns), "| tz =", getattr(out.index, 'tz', None),
              "| тип индекс =", type(out.index).__name__)
        st = {"tf_basis_g": -3.851}; nt = []
        v = lb._tf_basis(st, "tf_basis_g", out, daily, nt)
        print("   _tf_basis ->", v, "| бележки:", nt or "няма")
    except Exception as e:
        print(f"   _yf ГРЪМНА: {type(e).__name__}: {e}")
        print("   → gold_d (ред 3380) НЕ е в try → целият рън умира ШУМНО;")
        print("   → m5/m1 (ред 3509-3517) СА в try → src=None")
        st = {"tf_basis_g": -3.851}; nt = []
        print("   при src=None: _tf_basis ->", lb._tf_basis(st, "tf_basis_g", None, daily, nt),
              "| бележки:", nt or "няма")
