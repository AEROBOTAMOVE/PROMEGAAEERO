# -*- coding: utf-8 -*-
"""
F24б · СРЕБРОТО СЛЕД РАЗХОДА — присъдата

F24а мери БЕЗ спред. Това е числото «в лаборатория». Сребърният спред при
брокер е ~0.025–0.04$/oz. Прилагам го и гледам КОЯ клетка оцелява.
Мери се СЪЩАТА извадка, същият бутстрап — само пренесена с разхода.
"""
import warnings, json, io
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
exec(io.open("F24_srebro.py", encoding="utf-8").read().split('RNG = np.random')[0]
     .replace('лог(f"сделки', '#').replace('print()', '#'))

RNG = np.random.default_rng(240)
РАЗХОДИ = [0.0, 0.02, 0.03, 0.04]


def кл(g, разход):
    if len(g) < 30: return None
    x = g.copy(); x["n2"] = x["нето"] - разход
    d = x.groupby("ден")["n2"].agg(["sum", "count"])
    S, C = d["sum"].to_numpy(), d["count"].to_numpy(); k = len(S)
    из = RNG.integers(0, k, size=(4000, k))
    m = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    return (float(x["n2"].mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), len(x))


КЛЕТКИ = {"day1": lambda g: g["стрийк"] == 1,
          "fresh": lambda g: g["стрийк"].between(2, 3),
          "mixed": lambda g: g["стрийк"] == 0,
          "stale": lambda g: g["стрийк"] >= 4,
          "ultra": lambda g: (g["стрийк"].between(1, 3)) & (g["vr"] < 0.40)}

print("=" * 88)
print("СРЕБРОТО СЛЕД РАЗХОДА · нето$/сделка · ✅ = целият 95% интервал НАД нулата")
print("=" * 88)
print(f"  {'посока':6s} {'клетка':7s} {'n':>6s}" + "".join(f"{f'спред {r:.2f}$':>19s}" for r in РАЗХОДИ))
оцел = []
for d in ("long", "short"):
    for им, ф in КЛЕТКИ.items():
        g = T[(T["посока"] == d) & ф(T)]
        if len(g) < 30: continue
        ред = f"  {d:6s} {им:7s} {len(g):6,d}"
        for r in РАЗХОДИ:
            a = кл(g, r)
            ок = a[1] > 0
            ред += f"  {a[0]:+7.4f}{'✅' if ок else ('·' if a[2] > 0 else '❌')}"
            ред += f"{'':>9s}" if False else ""
            if r == 0.03 and ок: оцел.append(f"{d}/{им}")
        print(ред)
print()
print("  ✅ печели уверено · · шум (нулата е вътре) · ❌ губи уверено")
print()
print(f"ПРИ РЕАЛИСТИЧЕН СПРЕД 0.03$ ОЦЕЛЯВАТ: {', '.join(оцел) if оцел else '🔴 НИТО ЕДНА КЛЕТКА'}")

# колко пари изобщо би направило среброто за година при 0.03$
g = T[(T["посока"] == "long")]
n_год = len(g) / ((T["ден"].max() - T["ден"].min()).days / 365.25)
print(f"\nЗа мащаб: сребро LONG прави {n_год:.0f} сделки/год.")
for r in (0.0, 0.03):
    print(f"  при спред {r:.2f}$ → {(g['нето'].mean()-r)*n_год:+8.2f}$/год на унция "
          f"({(g['нето'].mean()-r)/0.001:+7.0f} пипса)")
print(f"\nЗлатото за сравнение: +0.54$/сделка най-слаб режим, спред 0.45$ → ръб 3.1× разхода.")
