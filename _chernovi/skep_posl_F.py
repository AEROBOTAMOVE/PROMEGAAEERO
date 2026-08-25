# -*- coding: utf-8 -*-
"""СКЕПТИК·ПОСЛЕДИЦА — стъпка 6:
F1) достижимият клон (src=None): има ли изобщо КОГО да излъже замразеният базис?
F2) «замръзва до края на времето» — вярно ли е, или се самовъзстановява?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import live_bot as lb
import pandas as pd, numpy as np

H.patch()
lb._spot = lambda instr="XAU/USD", **k: {"bid": 4599.8, "ask": 4600.2, "mid": 4600.0,
                                         "src": "swq", "age_sec": 1.0}
_yf_добър = H.fake_yf
def yf_без_интрадей(sym, period="2y", interval="1d"):
    if sym == "GC=F" and interval in ("1m", "5m"):
        raise RuntimeError("Yahoo мълчи за интрадей")
    return _yf_добър(sym, period, interval)

H.CFG.update(gold_end="2026-08-21", gold_px=4600.0, gold_step=0.5,
             spot_mid=4600.0, intra_end="2026-08-21 12:00")
H.set_now("2026-08-21T12:05:00+00:00")

print("=== F1 · РЪН БЕЗ ИНТРАДЕЙ (src=None → клонът «няма данни») ===")
lb._yf = yf_без_интрадей
d = H.fresh("_skep_posl5/bez_intra")
изход = H.run(d)
j = H.last_journal(d)
print("борд :", j.get("board"))
print("tf_basis в дневника:", j.get("tf_basis"))
print("статус:", j.get("status"), "| карти пратени:", len(H.SENT))
print("бележки, споменаващи базис:", [n for n in (j.get("notes") or []) if "базис" in n] or "няма")
print("→ ВЪПРОСЪТ: коя рамка изобщо ПОЛЗВА tf_adj в този рън?")
print("   рамки в борда, различни от 1ден, които НЕ са wait/weak:",
      [k for k, v in (j.get("board") or {}).items() if k != "1ден" and v[0] != "wait" and v[2] != "weak"])

print()
print("=== F2 · САМОВЪЗСТАНОВЯВА ЛИ СЕ СТАРИЯТ КОД, ЩОМ ДАННИТЕ СЕ ОПРАВЯТ ===")
src = open("live_bot.py.преди_4114", encoding="utf-8").read()
i = src.index("def _tf_basis("); jx = src.index("\n\n\n", i)
g = {"np": np, "pd": pd, "TF_BASIS_CAP": lb.TF_BASIS_CAP, "TF_BASIS_ALPHA": lb.TF_BASIS_ALPHA}
exec(compile(src[i:jx], "OLD", "exec"), g)
old_tf = g["_tf_basis"]
idx = pd.date_range("2026-07-01", periods=60*24, freq="h")
intra = pd.DataFrame({"Close": np.full(len(idx), 4600.0)}, index=idx)
r = intra.resample("1D").agg(Close=("Close", "last")).dropna()
daily = pd.DataFrame({"Close": r["Close"].values - 61.6}, index=r.index)
class Взривен(pd.DataFrame):
    @property
    def _constructor(self): return Взривен
    def __getitem__(self, k): raise KeyError("Close")
st = {"tf_basis_g": -3.851}; nt = []
for _ in range(200):
    old_tf(st, "tf_basis_g", intra, Взривен(daily), nt)
print("след 200 счупени ръна:", st["tf_basis_g"], "| бележки:", len(nt))
ред = []
for k in range(20):
    ред.append(round(old_tf(st, "tf_basis_g", intra, daily, nt), 3))
print("щом данните се оправят, СТАРИЯТ код дава:", ред[:12], "...")
print("догонва ли истината (-61.6)?", abs(ред[-1] + 61.6) < 0.5)
