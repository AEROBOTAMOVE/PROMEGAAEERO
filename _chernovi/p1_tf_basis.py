# -*- coding: utf-8 -*-
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pandas as pd, numpy as np
import live_bot as lb

def frames(diff, n=30, px=4600.0):
    """intra: часови барове за n дни; daily: същите дни, но с Close = intra + diff."""
    idx = pd.date_range("2026-07-20", periods=n*24, freq="h", tz=None)
    intra = pd.DataFrame({"Close": px + np.arange(len(idx))*0.0}, index=idx)
    r = intra.resample("1D").agg(Close=("Close","last")).dropna()
    daily = pd.DataFrame({"Close": r["Close"].values + diff}, index=r.index)
    return intra, daily

print("=== 1) ЖИВАТА СТОЙНОСТ ДНЕС ===")
meta_live = json.load(open("live/meta.json", encoding="utf-8"))
print("live/meta.json tf_basis_g =", meta_live.get("tf_basis_g"), " cap =", lb.TF_BASIS_CAP)

print()
print("=== 2) ИСТИНАТА НАДХВЪРЛЯ ТАВАНА -> ЗАМРЪЗВА ЗАВИНАГИ ===")
state = {"tf_basis_g": -61.599}          # точно живата стойност от продукцията
intra, daily = frames(-130.0)            # истинският контрактен базис = -130$
notes = []
for i in range(1000):
    v = lb._tf_basis(state, "tf_basis_g", intra, daily, notes)
print("след 1000 руна: state =", state)
print("вЪрната стойност :", v)
print("бележка          :", notes[-1])
print("брой бележки     :", len(notes))
print("има ли брояч на отказите? ", [k for k in state if "отказ" in k] or "НЯМА")

print()
print("=== 3) СЪЩИЯТ ВХОД, НО ПОД ТАВАНА -> приема се нормално ===")
state2 = {"tf_basis_g": -61.599}
intra2, daily2 = frames(-119.0)
n2 = []
for i in range(20):
    v2 = lb._tf_basis(state2, "tf_basis_g", intra2, daily2, n2)
print("след 20 руна при истина -119 (под 120):", state2["tf_basis_g"])

print()
print("=== 4) СРЕБРОТО: cap 9.0 ===")
state3 = {"tf_basis_s": -0.173}
intra3, daily3 = frames(-9.5, px=69.0)
n3 = []
for i in range(500):
    v3 = lb._tf_basis(state3, "tf_basis_s", intra3, daily3, n3, cap=lb.TF_BASIS_CAP_S)
print("след 500 руна:", state3, "бележка:", n3[-1])

print()
print("=== 5) КОЛКО ДАЛЕЧ Е ТАВАНЪТ (мерено от live_journal.jsonl) ===")
rows = [json.loads(l) for l in open("live/live_journal.jsonl", encoding="utf-8") if l.strip()]
import collections
d = collections.OrderedDict()
for r in rows:
    day = str(r.get("run_utc",""))[:10]
    if r.get("tf_basis") is not None:
        d.setdefault(day, []).append(r["tf_basis"])
days = list(d.items())
last = [(k, min(v)) for k, v in days[-16:]]
for k, v in last:
    print("  ", k, f"{v:+.3f}")
a = last[0]; b = last[-1]
dd = (pd.Timestamp(b[0]) - pd.Timestamp(a[0])).days
темп = (b[1]-a[1])/dd
print(f"дрейф {a[0]} {a[1]:+.2f} -> {b[0]} {b[1]:+.2f} за {dd} дни = {темп:+.2f}$/ден")
print(f"до таван -120$ остават {(-120 - b[1])/темп:.1f} дни при сЪщия темп")
