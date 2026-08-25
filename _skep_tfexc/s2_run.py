# -*- coding: utf-8 -*-
"""СКЕПТИК · ПУСКАНЕ. Едни и същи входове през v13.7 (реконструирана) и v14.0 (жива)."""
import sys, os, importlib.util
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import ast
def src_of(path, name):
    txt = open(path, encoding="utf-8").read()
    t = ast.parse(txt)
    for n in ast.walk(t):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return ast.get_source_segment(txt, n)
    raise KeyError(name)

hdr = ("import numpy as np, pandas as pd\n"
       "TF_BASIS_ALPHA=0.25\nTF_BASIS_CAP=120.0\nTF_BASIS_CAP_PCT=0.03\nTF_BASIS_STUCK_N=12\n")
LB = os.path.join(BASE, "live_bot.py")
breaker = src_of(LB, "_прекъсвач")
v137_txt = open(os.path.join(HERE, "_v137.py"), encoding="utf-8").read()
NS_OLD = {}; exec(compile(v137_txt, "<v13.7>", "exec"), NS_OLD)
NS_NEW = {}; exec(compile(hdr + breaker + "\n" + src_of(LB, "_tf_basis"), "<v14.0>", "exec"), NS_NEW)
tf137, tf140 = NS_OLD["_tf_basis"], NS_NEW["_tf_basis"]


# ---------- реалистични данни: злато ~4639$, дневната е ПОД интрадей с ~48$ ----------
def build(dneven_minus_intra=-48.0, cena=4639.0, dni=40):
    idx_d = pd.bdate_range("2026-06-25", periods=dni, freq="B")
    rng = np.random.default_rng(7)
    close_intra = cena + np.cumsum(rng.normal(0, 6, dni))
    daily = pd.DataFrame({"Close": close_intra + dneven_minus_intra,
                          "Open": close_intra, "High": close_intra + 5,
                          "Low": close_intra - 5}, index=idx_d)
    # интрадей: 5-минутки, последният бар на деня = close_intra
    rows, ix = [], []
    for d, c in zip(idx_d, close_intra):
        for k in range(3):
            ix.append(d + pd.Timedelta(hours=13 + k))
            rows.append(c - (2 - k) * 1.0)
    intra = pd.DataFrame({"Close": rows, "Open": rows, "High": rows, "Low": rows},
                         index=pd.DatetimeIndex(ix))
    return intra, daily


def показ(име, f, intra, daily, state, n=60):
    notes = []
    val = None
    for _ in range(n):
        val = f(state, "tf_basis_g", intra, daily, notes)
    return val, notes, state


print("=" * 78)
print("КОНТРОЛ 0 · нормален вход, 1 рън")
intra, daily = build()
for име, f in (("v13.7", tf137), ("v14.0", tf140)):
    st, nt = {}, []
    v = f(st, "tf_basis_g", intra, daily, nt)
    print("  %s → tf_basis=%s · бележки=%s · state=%s" % (име, v, nt, st))

print()
print("=" * 78)
print("ОПИТ A · ИЗКЛЮЧЕНИЕ ВЪТРЕ (доставчикът върна колона 'close' вместо 'Close')")
print("         60 поредни ръна, стартово пазено -48.55")
intra_bad = intra.rename(columns={"Close": "close"})
for име, f in (("v13.7", tf137), ("v14.0", tf140)):
    st = {"tf_basis_g": -48.55}
    nt = []
    for _ in range(60):
        v = f(st, "tf_basis_g", intra_bad, daily, nt)
    print("  --- %s" % име)
    print("      върната стойност след 60 ръна : %s" % v)
    print("      БРОЙ бележки за 60 ръна       : %d" % len(nt))
    print("      първите 2 бележки             : %s" % nt[:2])
    print("      последната бележка            : %s" % (nt[-1] if nt else "—"))
    print("      state                         : %s" % st)

print()
print("=" * 78)
print("ОПИТ B · КОНТРОЛА — клонът «над тавана» (истински базис +4951$)")
intra_hi, daily_hi = build(dneven_minus_intra=+4951.0)
for име, f in (("v13.7", tf137), ("v14.0", tf140)):
    st = {"tf_basis_g": -48.55}
    nt = []
    for _ in range(60):
        v = f(st, "tf_basis_g", intra_hi, daily_hi, nt)
    отключване = any("🔓" in x for x in nt)
    print("  --- %s : стойност=%s · бележки=%d · отключване=%s" % (име, v, len(nt), отключване))

print()
print("=" * 78)
print("ОПИТ C · РЕАЛНИЯТ ПРОДУКЦИОНЕН ПЪТ: intra is None (m5 И m1 паднаха)")
print("         в live_bot.py:3520  src = m5 if m5 is not None else m1")
for име, f in (("v13.7", tf137), ("v14.0", tf140)):
    st = {"tf_basis_g": -48.55}
    nt = []
    for _ in range(60):
        v = f(st, "tf_basis_g", None, daily, nt)
    print("  --- %s : стойност=%s · бележки=%d · %s" % (име, v, len(nt), nt[:1]))
    print("            state=%s" % st)

print()
print("=" * 78)
print("ОПИТ D · РЕАЛЕН ПЪТ 2: малко застъпване (само m1=7д, празнична седмица → 4 дни)")
intra_s, daily_s = build(dni=4)
for име, f in (("v13.7", tf137), ("v14.0", tf140)):
    st = {"tf_basis_g": -48.55}
    nt = []
    for _ in range(60):
        v = f(st, "tf_basis_g", intra_s, daily_s, nt)
    print("  --- %s : стойност=%s · бележки=%d · %s" % (име, v, len(nt), nt[:1]))
