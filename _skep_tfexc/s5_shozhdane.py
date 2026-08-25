# -*- coding: utf-8 -*-
"""СКЕПТИК · схожда ли се v14.0 след като `_тих` бутне базиса на 0.00,
и остава ли v13.7 заключена завинаги. ЖИВИ данни."""
import sys, os, importlib.util, ast
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
spec = importlib.util.spec_from_file_location("lb", os.path.join(BASE, "live_bot.py"))
lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)
gold_d = lb._yf("GC=F", "3y", "1d"); m5 = lb._yf("GC=F", "60d", "5m")
NS = {}; exec(compile(open(os.path.join(HERE, "_v137.py"), encoding="utf-8").read(), "<v137>", "exec"), NS)
tf137 = NS["_tf_basis"]

сцен = [("20 ръна БЕЗ интрадей (m5 и m1 паднаха)", None),
        ("после интрадей се ВРЪЩА", m5)]
for име, f in (("v13.7", tf137), ("v14.0", lb._tf_basis)):
    s = {"tf_basis_g": -3.851}; n = []
    for _ in range(20):
        v = f(s, "tf_basis_g", None, gold_d, n)
    сл = [v]
    for _ in range(30):
        сл.append(f(s, "tf_basis_g", m5, gold_d, n))
    print("%s: след 20 слепи ръна = %s; после 30 ръна с жив вход → %s ... %s"
          % (име, сл[0], сл[1:4], сл[-1]))
    print("      бележки общо: %d" % len(n))
print("\nистинската стойност днес: %s" % lb._tf_basis({}, "x", m5, gold_d, []))
