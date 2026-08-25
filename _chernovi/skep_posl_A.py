# -*- coding: utf-8 -*-
"""СКЕПТИК·ПОСЛЕДИЦА — стъпка 1: възпроизвеждам находката САМ, върху СТАРИЯ код."""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, numpy as np
import live_bot as lb

print("pandas", pd.__version__, "numpy", np.__version__)

# --- изваждам СТАРАТА (пред-поправка) функция от резервното копие ---
src = open("live_bot.py.преди_4114", encoding="utf-8").read()
i = src.index("def _tf_basis(")
j = src.index("\n\n\n", i)
old_src = src[i:j]
print("=== СТАРИЯТ ИЗТОЧНИК (последни 4 реда) ===")
print("\n".join(old_src.splitlines()[-4:]))
g = {"np": np, "pd": pd, "TF_BASIS_CAP": lb.TF_BASIS_CAP, "TF_BASIS_ALPHA": lb.TF_BASIS_ALPHA}
exec(compile(old_src, "OLD", "exec"), g)
old_tf = g["_tf_basis"]

def frames(diff, n=30, px=4600.0):
    idx = pd.date_range("2026-07-20", periods=n*24, freq="h")
    intra = pd.DataFrame({"Close": np.full(len(idx), px)}, index=idx)
    r = intra.resample("1D").agg(Close=("Close", "last")).dropna()
    daily = pd.DataFrame({"Close": r["Close"].values + diff}, index=r.index)
    return intra, daily

class Взривен(pd.DataFrame):
    """DataFrame, чийто достъп до колона гърми — имитира сменена схема."""
    @property
    def _constructor(self): return Взривен
    def __getitem__(self, k):
        raise KeyError("Close")

intra, daily = frames(-48.55)
print()
print("=== A1 · НОРМАЛЕН РЪН, СТАР КОД, pandas 3.0.1 ===")
st = {}; nt = []
print("стар  ->", old_tf(st, "tf_basis_g", intra, daily, nt), "| бележки:", nt, "| state:", st)
st2 = {}; nt2 = []
print("нов   ->", lb._tf_basis(st2, "tf_basis_g", intra, daily, nt2), "| бележки:", nt2, "| state:", st2)

print()
print("=== A2 · 60 РЪНА С ИЗКЛЮЧЕНИЕ ВЪТРЕ (KeyError) ===")
bad = Взривен(daily)
for име, fn in (("СТАР", old_tf), ("НОВ", lb._tf_basis)):
    st = {"tf_basis_g": -48.55}; nt = []
    v = None
    for _ in range(60):
        v = fn(st, "tf_basis_g", intra, bad, nt)
    print(f"{име}: върната={v} | бележки={len(nt)} | tf_basis_g={st.get('tf_basis_g')} "
          f"| ключове={ {k: st[k] for k in st if k != 'tf_basis_g'} }")
    if nt: print(f"   първа бележка: {nt[0]}"); print(f"   последна:       {nt[-1]}")
