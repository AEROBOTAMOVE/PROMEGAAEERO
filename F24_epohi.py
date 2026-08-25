# -*- coding: utf-8 -*-
"""F24в · ДЪРЖИ ЛИ СЕ В ДВЕТЕ ЕПОХИ + защо старите числа не се възпроизвеждат"""
import warnings, io, json
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
exec(io.open("F24_srebro.py", encoding="utf-8").read().split('RNG = np.random')[0]
     .replace('лог(f"сделки', '#').replace('print()', '#'))

st = json.load(io.open("backtest_stats.json", encoding="utf-8"))
RNG = np.random.default_rng(241)
РАЗХОД = 0.03


def оц(g, разход=РАЗХОД):
    if len(g) < 30: return None
    x = g["нето"] - разход
    d = pd.DataFrame({"n": x, "ден": g["ден"]}).groupby("ден")["n"].agg(["sum", "count"])
    S, C = d["sum"].to_numpy(), d["count"].to_numpy(); k = len(S)
    из = RNG.integers(0, k, size=(3000, k))
    m = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), len(x)


КЛ = {"day1": lambda g: g["стрийк"] == 1, "fresh": lambda g: g["стрийк"].between(2, 3),
      "mixed": lambda g: g["стрийк"] == 0, "stale": lambda g: g["стрийк"] >= 4}
ЕПОХИ = [("2000-2012", T["ден"] < "2013-01-01"), ("2013-2026", T["ден"] >= "2013-01-01")]

print("=" * 84)
print(f"ДВЕТЕ ЕПОХИ · след разход {РАЗХОД}$ · знакът трябва да е ЕДНАКЪВ, за да значи нещо")
print("=" * 84)
for d in ("long", "short"):
    for им, ф in КЛ.items():
        ред = f"  {d:6s} {им:6s}"
        зн = []
        for ен, м in ЕПОХИ:
            a = оц(T[(T["посока"] == d) & ф(T) & м])
            if not a: ред += f"  {ен}: малко"; зн.append(0); continue
            ред += f"  {ен} {a[0]:+7.4f}$ (n={a[3]:>5,d})"
            зн.append(np.sign(a[0]))
        print(ред + ("   ⚖️ съгласни" if зн[0] == зн[1] and зн[0] != 0 else "   🔴 РАЗЛИЧЕН ЗНАК"))

print()
print("=" * 84)
print("СТАРИТЕ ЧИСЛА ВЪВ ФАЙЛА срещу ПРЕИЗМЕРЕНИТЕ (и двете БЕЗ разход, за честно сравнение)")
print("=" * 84)
print(f"  {'':13s} {'СТАРО n':>8s} {'СТАРО нето':>11s} {'МОЕ n':>8s} {'МОЕ нето':>10s}")
for d in ("long", "short"):
    for им in ("fresh", "stale"):
        стар = (st.get("silver", {}).get(d, {}) or {}).get(им, {}) or {}
        g = T[(T["посока"] == d) & КЛ[им](T)]
        a = оц(g, 0.0)
        print(f"  {d:6s} {им:6s} {стар.get('n', '—'):>8} {стар.get('net', '—'):>11} "
              f"{a[3]:>8,d} {a[0]:>+10.4f}")
print()
print("  Старите нямат нито lo/hi, нито записан метод. Моите са в F24_srebro.py,")
print("  възпроизводими ред по ред. Затова СТАРИТЕ се запазват под `_старо`, но")
print("  решението минава по преизмерените.")
