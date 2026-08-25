# -*- coding: utf-8 -*-
"""Кои числа СЪЩЕСТВУВАТ за изходните карти. Само четене."""
import sys, io, json, re
sys.argv = ["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import live_bot as lb

st = json.load(io.open("backtest_stats.json", encoding="utf-8"))
print("=== ключове от най-горно ниво ===")
print(list(st.keys()))
m = st.get("_meta", {})
print("\n=== _meta ключове ===")
print(list(m.keys()))
for k in ("НЕпреизмерено", "кое_чете_ботът", "тишина_мерена"):
    if k in m:
        print(f"\n--- _meta[{k}] ---")
        print(json.dumps(m[k], ensure_ascii=False, indent=1)[:2500])

print("\n=== търсене на думи: време / flip / обрат / 30 дни / tp_hits ===")
def обходи(о, път=""):
    if isinstance(о, dict):
        for k, v in о.items():
            yield from обходи(v, f"{път}.{k}")
    elif isinstance(о, list):
        yield път, f"[list n={len(о)}]"
    else:
        yield път, о
вс = list(обходи(st))
print("общо листа:", len(вс))
for дума in ("time", "време", "flip", "обрат", "tp_hit", "цел", "изход", "days", "дни_дър"):
    хит = [p for p, v in вс if дума.lower() in p.lower()]
    print(f"  «{дума}»: {len(хит)} → {хит[:12]}")

print("\n=== tp_hits* пълно ===")
for p, v in вс:
    if "tp_hit" in p.lower():
        print(f"  {p} = {v}")

print("\n=== _ladder_pnl: подът след ЦЕЛ 2 ===")
E = 4358.00
LV = {"sl": 4358.00, "tp1": 4365.50, "tp2": 4370.00, "tp3": 4378.00}
# стоп на входа, след ТП1+ТП2
ст, вз = lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, LV, E, 1, 0.0, {})
print(f"стоп на входа след ТП1+ТП2 → стълба={ст:+.2f}$ = {ст/lb.PIP:+.0f} пипса · взети={вз}")
ст1, вз1 = lb._ladder_pnl("sl", {"tp1": True}, LV, E, 1, 0.0, {})
print(f"стоп на входа след само ТП1  → стълба={ст1:+.2f}$ = {ст1/lb.PIP:+.0f} пипса · взети={вз1}")
print(f"ТП1 трета = {(LV['tp1']-E)/3:.2f}$ · ТП2 трета = {(LV['tp2']-E)/3:.2f}$ · ТП3 трета = {(LV['tp3']-E)/3:.4f}$")
print(f"сбор трите = {((LV['tp1']-E)+(LV['tp2']-E)+(LV['tp3']-E))/3:.4f}$ срещу «пълните» 20.00$")
print("_пари(13.17):", lb._пари(13.17), "| _пари(6.50):", lb._пари(6.50), "| _пари(4.00):", lb._пари(4.00))
print("S_TPS сребро:", lb.S_TPS)
