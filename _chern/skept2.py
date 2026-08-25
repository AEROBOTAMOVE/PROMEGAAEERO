# -*- coding: utf-8 -*-
import sys, io, importlib.util, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import numpy as np, pandas as pd
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("M", os.path.join(BASE,"live_bot.py"))
M = importlib.util.module_from_spec(spec); sys.modules["M"]=spec.loader and M; spec.loader.exec_module(M)
N = M.TF_BASIS_STUCK_N; K="tf_basis_g"

def ramki(delta):
    idx = pd.date_range("2026-08-01", periods=24*10, freq="h", tz="UTC")
    intra = pd.DataFrame({"Close": np.linspace(3700.0,3720.0,len(idx))}, index=idx)
    r = intra.resample("1D").agg(Close=("Close","last")).dropna()
    daily = pd.DataFrame({"Close": r["Close"].values+delta}, index=r.index)
    return intra, daily

print("ТЕСТ A · ОТРОВЕНО НАСЛЕДЕНО СЪСТОЯНИЕ (state.json отпреди поправката)")
print("  симулирам meta.json, донесъл tf_basis_g_отказ = 11 и празен списък,")
print("  после ЕДИН изроден образец над тавана.")
st = {K: -61.6, K+"_отказ": 11, K+"_отказани": []}
ig, dg = ramki(-900.0)
notes=[]; v = M._tf_basis(st, K, ig, dg, notes)
print("  върнато:", v, " state[%s]=%s"%(K, st.get(K)), " _отказ=", st.get(K+"_отказ"))
for n in notes: print("  бележка:", n)
print("  >>> ", "ДЕФЕКТ — закотви на глича" if abs(float(st[K])+900)<1 else "ЧИСТО — самолекува се")

print("\nТЕСТ Б · ОТРОВЕНО НАСЛЕДЕНО _отказ=11 + СПИСЪК с 11 стари наблюдения")
st = {K: -61.6, K+"_отказ": 11, K+"_отказани": [-62.0]*11}
notes=[]; v = M._tf_basis(st, K, ig, dg, notes)
print("  върнато:", v, " state[%s]=%s"%(K, st.get(K)))
for n in notes: print("  бележка:", n)
print("  (медианата на 11 честни + 1 глич трябва да е ≈ -62, НЕ -900)")

print("\nТЕСТ В · МОЖЕ ЛИ НОВИЯТ `_тих` БРОЯЧ ДА ЗАКЛЮЧИ ЗАВИНАГИ? 40 ръна без данни")
st = {}; i0,d0 = ramki(-61.6)
for _ in range(40): M._tf_basis(st, K, i0, d0, [])
vals=[]; osv=0
for i in range(1,41):
    notes=[]; v = M._tf_basis(st, K, None, d0, notes); vals.append(round(v,2))
    if any("🔓" in n for n in notes): osv+=1
print("  стойности ръна 1..40:", vals)
print("  брой освобождавания за 40 ръна:", osv, " краен _тих =", st.get(K+"_тих"))
print("  >>> ", "ЗАКЛЮЧВА — дефект" if osv==0 else "НЕ заключва — пуска се на 0.00 периодично")

print("\nТЕСТ Г · ВЪЗСТАНОВЯВА ЛИ СЕ САМ, щом данните се върнат след дълго мълчание?")
notes=[]; v = M._tf_basis(st, K, i0, d0, notes)
print("  първи рън с данни →", v, " (истина -61.6; EMA alpha=%s)"%M.TF_BASIS_ALPHA)
for _ in range(30): v = M._tf_basis(st, K, i0, d0, [])
print("  след още 30 ръна →", round(v,3), " _тих=", st.get(K+"_тих"), " _отказ=", st.get(K+"_отказ"))
