# -*- coding: utf-8 -*-
"""
СВЕРКА · кръпката по инструмента НЕ Е ПИПНАЛА ФИЗИКАТА

Правилото на тази поправка беше: по подразбиране нищо не се мени. Тук се
проверява, а не се твърди. Зареждат се СТАРИЯТ (от резервното копие) и НОВИЯТ
модул едновременно и се сравняват на ВСИЧКИТЕ 6846 входа, поле по поле.

Разминаване в `net`, `kind` или `n_tp` значи, че кръпката е сменила физиката —
тогава всяко число, мерено с новия инструмент, ще е несравнимо със записаното.
"""
import sys, shutil, importlib.util, warnings, time
warnings.filterwarnings("ignore")
import numpy as np
SP = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad"
sys.path.insert(0, SP)

t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)

# старият, под друго име
шпат = SP + r"\_stari_harness.py"
shutil.copy(SP + r"\geom_harness.py.преди_одита", шпат)
сп = importlib.util.spec_from_file_location("_stari_harness", шпат)
СТАР = importlib.util.module_from_spec(сп); сп.loader.exec_module(СТАР)
import geom_harness as НОВ
лог("двата модула са заредени")

B = НОВ.load_tape(); E = НОВ.build_entries(B)
СТАР.TIME_EXIT_DAYS = НОВ.TIME_EXIT_DAYS = 21
idxs = E["bar_index"].values; dirs = E["direction"].values; pxs = E["entry_px"].values
ГЕОМ = {"name": "доставената", "sl": 20.0,
        "tps": [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], "be_after_tp1": True}
лог(f"сверявам {len(idxs):,} входа…")

разл = {"net": 0, "kind": 0, "n_tp": 0, "exit_index": 0, "None": 0}
макс = 0.0; фил = []
for p in range(len(idxs)):
    a = СТАР._one_trade(int(idxs[p]), dirs[p], float(pxs[p]), ГЕОМ, B)
    b = НОВ._one_trade(int(idxs[p]), dirs[p], float(pxs[p]), ГЕОМ, B)
    if (a is None) != (b is None):
        разл["None"] += 1; continue
    if a is None:
        continue
    d = abs(a["net"] - b["net"]); макс = max(макс, d)
    if d > 0: разл["net"] += 1
    if a["kind"] != b["kind"]: разл["kind"] += 1
    if a["n_tp"] != b["n_tp"]: разл["n_tp"] += 1
    if a["exit_index"] != b["exit_index"]: разл["exit_index"] += 1
    фил.append(b["n_fills"])

print()
print("=" * 78)
print("СВЕРКА СТАР ↔ НОВ ИНСТРУМЕНТ · 6846 входа, доставената геометрия")
print("=" * 78)
for k, v in разл.items():
    print(f"  разминавания по {k:12s}: {v}")
print(f"  max|Δnet| = {макс:.2e}")
ок = макс == 0.0 and not any(разл.values())
print()
print("  " + ("✅ ФИЗИКАТА Е НЕПИПНАТА — записаните числа остават възпроизводими"
              if ок else "🔴 КРЪПКАТА Е СМЕНИЛА ФИЗИКАТА — не ползвай новия инструмент"))
if not ок:
    sys.exit(1)

# и новото поле: колко изпълнения наистина има
фил = np.array(фил)
print()
print("НОВОТО, КОЕТО ДОСЕГА НЕ СЕ ВИЖДАШЕ:")
print(f"  средно изпълнения на сделка : {фил.mean():.3f}")
print(f"  разпределение               : " +
      " · ".join(f"{k} изп: {(фил == k).mean()*100:.1f}%" for k in sorted(set(фил.tolist()))))
print(f"  слип на сделка (както е)    : {НОВ.SLIP_PER_TRADE:.3f}$")
print(f"  слип на изпълнение (истина) : {НОВ.SLIP_PER_TRADE * фил.mean():.4f}$")
print(f"  → доставената е недоплащала {НОВ.SLIP_PER_TRADE*(фил.mean()-1):.4f}$ на сделка")

# П1 · спирачката работи ли
print()
print("П1 · СПИРАЧКАТА:")
try:
    НОВ.simulate(E.head(50), ГЕОМ, B)
    print("  🔴 НЕ работи — пусна неприпокриване без заявяване")
except ValueError as e:
    print(f"  ✅ отказва: {str(e)[:88]}…")
try:
    НОВ.simulate(E.head(50), ГЕОМ, B, ne_e_sravnenie=True)
    print("  ✅ и пуска, когато е заявено изрично")
except Exception as e:
    print(f"  🔴 не пуска дори при заявяване: {type(e).__name__}")
лог("готово")
