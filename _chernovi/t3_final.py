# -*- coding: utf-8 -*-
"""ФИНАЛНА СВЕРКА срещу ТЕКУЩИЯ live_bot.py (файлът се редактира от друг агент —
затова всичко се пуска наново)."""
import sys, io, json, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE)
import os
os.chdir(BASE)
raw = open("live_bot.py", "rb").read()
print("live_bot.py sha1:", hashlib.sha1(raw).hexdigest(), "байта:", len(raw))
import live_bot as lb
import pandas as pd, numpy as np

print()
print("### 1 · _tf_basis (ред 984) — «пазя стария» БЕЗ прекъсвач")
idx = pd.date_range("2026-07-20", periods=720, freq="h")
intra = pd.DataFrame({"Close": [4600.0]*720}, index=idx)
r = intra.resample("1D").agg(Close=("Close", "last")).dropna()
daily = pd.DataFrame({"Close": r["Close"].values - 130.0}, index=r.index)
st = {"tf_basis_g": -61.599}     # ТОЧНО живата стойност от live/meta.json
notes = []
for i in range(150):
    v = lb._tf_basis(st, "tf_basis_g", intra, daily, notes)
print("   150 руна с истина -130$ (таван", lb.TF_BASIS_CAP, "):")
print("   state =", st, " върнато =", v)
print("   ключове с брояч:", [k for k in st if "отказ" in k] or "НЯМА")
print("   бележка (една и съща 150 пъти):", notes[-1])
# сребро
sts = {"tf_basis_s": -0.173}
ns = []
dailys = pd.DataFrame({"Close": r["Close"].values - 9.6}, index=r.index)
for i in range(50):
    vs = lb._tf_basis(sts, "tf_basis_s", intra, dailys, ns, cap=lb.TF_BASIS_CAP_S)
print("   сребро (таван", lb.TF_BASIS_CAP_S, "): state =", sts, "бележка:", ns[-1])

print()
print("### 2 · прекъсвачът на _basis_update (ред 942) е зад СЪЩИЯ таван")
cap = lb._basis_cap(4700.0, "XAUUSD")
st2 = {"basis_g": 25.515}; n2 = []
for i in range(200):
    v2 = lb._basis_update(st2, "basis_g", {"mid": 4600.0, "src": "swq"}, 4700.0, n2,
                          cap=cap, now_utc="2026-08-21T10:00")
print(f"   cap={cap:.1f}$  истина=100$  ->  basis_g={st2['basis_g']}  брояч={st2.get('basis_g_отказ')}")
print("   бележка:", n2[-1])

print()
print("### 3 · студеният старт (ред 923) няма НИКАКЪВ брояч")
st3 = {}; n3 = []
for i in range(200):
    v3 = lb._basis_update(st3, "basis_g", {"mid": 4600.0, "src": "swq"}, 4700.0, n3,
                          cap=cap, now_utc="2026-08-21T10:00")
print("   state =", st3, " върнато =", v3, " 'basis_g' записан?", "basis_g" in st3)
sl = {}
print("   _spot_sane ->", lb._spot_sane({"mid": 4600.0}, 4700.0 - v3, 8.0, bar_rng=4.0, следа=sl))
print("   следа:", sl)

print()
print("### 4 · brain_track.json няма изход по ВРЕМЕ")
import pathlib, tempfile
d = pathlib.Path(tempfile.mkdtemp())
f = d/"brain_track.json"; j = d/"brain_result.jsonl"
f.write_text(json.dumps({"посока": "long", "рамка": "15м", "степен": "🔥", "точки": 14,
                         "отворен": "2026-01-01T00:00", "вход": 4600.0, "стоп": 4500.0,
                         "цел1": 4700.0, "цел2": 4800.0, "цел1_взета": False},
                        ensure_ascii=False), encoding="utf-8")
нов = {"лонг": True, "рамка": "5м", "степен": "🔥", "точки": 15,
       "залог": {"вход": 4610.0, "стоп": 4605.0, "цел": 4620.0, "цел2": 4630.0}}
for i in range(500):
    msgs = lb._мозък_следене(f, j, 4650.0, "2027-06-01T12:00", нов=нов, бар=(4652.0, 4648.0))
т = json.loads(f.read_text(encoding="utf-8"))
print("   500 руна, 17 МЕСЕЦА по-късно (2027-06-01) — файлът още държи:")
print("   ", {k: т[k] for k in ("посока", "рамка", "отворен", "вход", "стоп", "цел1")})
print("   новото наблюдение прието ли е?", "НЕ" if т["рамка"] == "15м" else "да")
print("   карти:", msgs)
import re
src = open("live_bot.py", encoding="utf-8").read()
блок = src[src.index("def _мозък_следене"):src.index("def _мозък_изход_msg")]
print("   думи за възраст/време в цялата функция:",
      [w for w in ("ДНИ_МАКС", "days", "дни", "възраст", "timeout", "изтекъл", "age") if w in блок] or "НЯМА")
