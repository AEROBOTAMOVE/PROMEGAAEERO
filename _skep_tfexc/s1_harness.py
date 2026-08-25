# -*- coding: utf-8 -*-
"""СКЕПТИК · възпроизвеждане на находката «except заобикаля прекъсвача».
Изгражда ДВЕ версии на _tf_basis:
  СТАРА (v13.7-подобна) = v13.5-текстът на трите изхода + прекъсвач САМО в клона «над тавана»
  НОВА  (v14.0 жива)     = каквото е в live_bot.py сега
и ги пуска с ЕДНИ И СЪЩИ входове.
"""
import ast, io, sys, os
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LB = os.path.join(BASE, "live_bot.py")
OLD = os.path.join(BASE, "live_bot.py.преди_deadlock")   # v13.5


def src_of(path, name):
    txt = open(path, encoding="utf-8").read()
    tree = ast.parse(txt)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef,)) and n.name == name:
            return ast.get_source_segment(txt, n)
    raise KeyError(name)


PRE = """
import numpy as np, pandas as pd
TF_BASIS_ALPHA = %r
TF_BASIS_CAP = %r
TF_BASIS_CAP_PCT = %r
TF_BASIS_STUCK_N = %r
"""


def consts():
    txt = open(LB, encoding="utf-8").read()
    ns = {}
    for line in txt.splitlines():
        for k in ("TF_BASIS_ALPHA", "TF_BASIS_CAP ", "TF_BASIS_CAP_PCT", "TF_BASIS_STUCK_N"):
            if line.startswith(k.strip() + " ="):
                pass
    return None


# --- константи, прочетени от живия файл ---
_t = open(LB, encoding="utf-8").read()
def _num(name):
    import re
    m = re.search(r"^%s\s*=\s*(.+)$" % name, _t, re.M)
    line = m.group(1)
    if "environ" in line:
        import re as r2
        mm = r2.search(r'"([-\d.]+)"\)', line)
        return float(mm.group(1))
    return float(line.split("#")[0].strip())

ALPHA = _num("TF_BASIS_ALPHA")
CAP = _num("TF_BASIS_CAP")
CAPPCT = _num("TF_BASIS_CAP_PCT")
STUCK = int(_num("TF_BASIS_STUCK_N"))
print("константи от живия файл: ALPHA=%s CAP=%s CAP_PCT=%s STUCK_N=%s"
      % (ALPHA, CAP, CAPPCT, STUCK))

breaker_src = src_of(LB, "_прекъсвач")
new_src = src_of(LB, "_tf_basis")
old_body = src_of(OLD, "_tf_basis")

# --- СТАРА версия: вземаме v13.5 тялото и вкарваме прекъсвача в клона «над тавана»
#     (точно това е v13.7 според находката: прекъсвач САМО там)
old_v137 = old_body.replace(
    '    _cap = TF_BASIS_CAP if cap is None else cap\n',
    '    _cap = cap\n')
old_v137 = old_v137.replace(
    '        now = float((j["Close_d"] - j["Close"]).tail(days).median())\n'
    '        if not np.isfinite(now) or abs(now) > _cap:\n'
    '            notes.append(f"контрактен базис {now:+.1f}$ извън диапазон — пазя стария")\n'
    '            return state.get(key, 0.0)\n',
    '        now = float((j["Close_d"] - j["Close"]).tail(days).median())\n'
    '        if _cap is None:\n'
    '            _ц = abs(float(j["Close_d"].iloc[-1]))\n'
    '            _cap = max(TF_BASIS_CAP, TF_BASIS_CAP_PCT * _ц)\n'
    '        if not np.isfinite(now) or abs(now) > _cap:\n'
    '            if np.isfinite(now):\n'
    '                _нов = _прекъсвач(state, key, now, notes, TF_BASIS_STUCK_N,\n'
    '                                  "контрактният базис")\n'
    '                if _нов is not None:\n'
    '                    return _нов\n'
    '            notes.append("контрактен базис %+.1f$ извън диапазон — пазя стария '
    '· %d-и пореден отказ" % (now, state.get(key + "_отказ", 0)))\n'
    '            return state.get(key, 0.0)\n')
assert "_прекъсвач(state" in old_v137, "вмъкването се провали"
assert old_v137.count("return state.get(key, 0.0)") >= 3, old_v137.count("return state.get(key, 0.0)")

hdr = ("import numpy as np, pandas as pd\n"
       "TF_BASIS_ALPHA=%r\nTF_BASIS_CAP=%r\nTF_BASIS_CAP_PCT=%r\nTF_BASIS_STUCK_N=%r\n"
       % (ALPHA, CAP, CAPPCT, STUCK))

NS_OLD, NS_NEW = {}, {}
exec(compile(hdr + breaker_src + "\n" + old_v137, "<v13.7>", "exec"), NS_OLD)
exec(compile(hdr + breaker_src + "\n" + new_src, "<v14.0>", "exec"), NS_NEW)
tf_old, tf_new = NS_OLD["_tf_basis"], NS_NEW["_tf_basis"]

open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_v137.py"), "w",
     encoding="utf-8").write(hdr + breaker_src + "\n" + old_v137)
print("\n=== СТАРАТА (v13.7) функция, последни 12 реда ===")
print("\n".join(old_v137.splitlines()[-12:]))
