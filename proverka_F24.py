# -*- coding: utf-8 -*-
"""
ПРОВЕРКА НА F24 · В ДВЕТЕ ПОСОКИ

Правилото, което ме е хапало: тест, който проверява само че спирачката СПИРА,
не отличава «умна спирачка» от «закован отказ». Затова тук се проверява и
ОБРАТНОТО — че при СРЕБРО_СПРЕД=0.00 клетките ОЖИВЯВАТ. Ако не оживеят, значи
съм заковал среброто, вместо да го измеря.

И трето: ЗЛАТОТО да е БУКВАЛНО непроменено. Новото условие в `_noise` пипа
всичко, което мине през него.
"""
import io, os, json, importlib, sys, subprocess

СТ = json.load(io.open("backtest_stats.json", encoding="utf-8"))
ЗЛАТО_ПРЕДИ = {}


def пусни(спред):
    """живо зареждане с даден спред — в СВОЙ процес, за да е чист вносът"""
    код = r'''
import io, os, json, sys
os.environ["СРЕБРО_СПРЕД"] = "%s"
sys.argv = ["x"]
import live_bot as lb
st = json.load(io.open("backtest_stats.json", encoding="utf-8"))
lb._сребро_разход(st, None)
из = {}
for м, sym in (("злато", "XAUUSD"), ("сребро", "XAGUSD")):
    for d in ("long", "short"):
        for s in (0, 1, 2, 5):
            t, ok = lb._advice_entry(d, s, st, False, False, 0, sym=sym)
            из[f"{м}|{d}|{s}"] = [bool(ok), t]
print("@@@" + json.dumps(из, ensure_ascii=False))
''' % спред
    io.open("_t24.py", "w", encoding="utf-8").write(код)
    r = subprocess.run([sys.executable, "_t24.py"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    for ln in (r.stdout or "").splitlines():
        if ln.startswith("@@@"):
            return json.loads(ln[3:])
    print("🔴 не се пусна:", (r.stderr or "")[-600:])
    sys.exit(1)


A = пусни("0.03")     # по подразбиране
B = пусни("0.00")     # без разход — клетките трябва да оживеят

print("=" * 86)
print("1 · ПРИ ПОДРАЗБИРАНЕ (спред 0.03$) — среброто трябва да МЪЛЧИ навсякъде")
print("=" * 86)
сребро_да = []
for k, (ok, t) in A.items():
    if k.startswith("сребро"):
        _, d, s = k.split("|")
        print(f"  {d:6s} стрийк {s}: {'🟢 ПУСКА' if ok else '⛔ отказ':10s} · {t[:62]}")
        if ok:
            сребро_да.append(k)
print(f"\n  {'🔴 ПУСКА ' + str(len(сребро_да)) if сребро_да else '✅ НУЛА входа за сребро'}")

print()
print("=" * 86)
print("2 · ОБРАТНАТА ПОСОКА (спред 0.00$) — клетките трябва да ОЖИВЕЯТ")
print("=" * 86)
живи = [k for k, (ok, _) in B.items() if k.startswith("сребро") and ok]
for k in sorted(живи):
    print(f"  🟢 {k}  ·  {B[k][1][:62]}")
if живи:
    print(f"\n  ✅ {len(живи)} клетки оживяват → спирачката МЕРИ, не е закована")
else:
    print("\n  🔴 НИТО ЕДНА не оживя → значи съм заковал отказа, а не го измерил")

print()
print("=" * 86)
print("3 · ЗЛАТОТО трябва да е БУКВАЛНО еднакво в двата случая")
print("=" * 86)
разл = [k for k in A if k.startswith("злато") and A[k] != B[k]]
for k in sorted(A):
    if k.startswith("злато"):
        _, d, s = k.split("|")
        ok, t = A[k]
        print(f"  {d:6s} стрийк {s}: {'🟢 ПУСКА' if ok else '⛔ отказ':10s} · {t[:62]}")
print(f"\n  {'🔴 РАЗЛИКИ: ' + str(разл) if разл else '✅ златото не е пипнато от сребърния спред'}")

print()
print("=" * 86)
print("4 · НЕ съм счупил `_noise` за златото (клетки без `_епохи_съгласни`)")
print("=" * 86)
io.open("_t24b.py", "w", encoding="utf-8").write(
    'import sys, json, io\nsys.argv=["x"]\nimport live_bot as lb\n'
    'пр = [("празна", {}), ("злато mixed", {"lo": -1.015, "hi": 0.062}),\n'
    '      ("злато day1", {"lo": 1.655, "hi": 4.196}), ("без интервал", {"net": 5.0}),\n'
    '      ("епохи съгласни", {"lo": 0.1, "hi": 0.9, "_епохи_съгласни": True}),\n'
    '      ("епохи РАЗЛИЧНИ", {"lo": 0.1, "hi": 0.9, "_епохи_съгласни": False})]\n'
    'print("@@@" + json.dumps([[и, lb._noise(с)] for и, с in пр], ensure_ascii=False))\n')
r = subprocess.run([sys.executable, "_t24b.py"], capture_output=True, text=True,
                   encoding="utf-8", errors="replace")
ЧАКАМ = {"празна": False, "злато mixed": True, "злато day1": False, "без интервал": False,
         "епохи съгласни": False, "епохи РАЗЛИЧНИ": True}
for ln in (r.stdout or "").splitlines():
    if ln.startswith("@@@"):
        for и, v in json.loads(ln[3:]):
            ок = v == ЧАКАМ[и]
            print(f"  {и:18s} → шум={str(v):5s}  чакам {str(ЧАКАМ[и]):5s}  {'✅' if ок else '🔴 ГРЕШНО'}")
for f in ("_t24.py", "_t24b.py"):
    try:
        os.remove(f)
    except Exception:
        pass
