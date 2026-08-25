# -*- coding: utf-8 -*-
"""
ИЗМЕРВАНЕ · НАИСТИНА ЛИ СЕДЕМТЕ РАМКИ СА ЕДНА?

Не вярвам на одита на дума. Меря сам, върху ЖИВИЯ дневник — това е
истинска история на бота, не симулация.

И второ: доказвам ПРИЧИНАТА структурно, от самия код.
"""
import json, io, collections, ast, sys

r = [json.loads(l) for l in io.open("live/live_journal.jsonl", encoding="utf-8") if l.strip()]
r = [x for x in r if isinstance(x.get("board"), dict) and x["board"]]
РАМКИ = ["1мин", "5м", "15м", "30м", "1час", "4час", "1ден"]

print("=" * 72)
print(f"1 · ЕДНАКВИ ЛИ СА РАМКИТЕ · {len(r)} живи ръна")
print("=" * 72)

еднакви_посока = еднакви_всичко = 0
за_рамка_посока = collections.Counter()
разлики = collections.Counter()
for x in r:
    b = x["board"]
    пос = [b[k][0] for k in РАМКИ if k in b]
    цял = [tuple(b[k]) for k in РАМКИ if k in b]
    if len(set(пос)) == 1: еднакви_посока += 1
    if len(set(цял)) == 1: еднакви_всичко += 1
    разлики[len(set(цял))] += 1
    for k in РАМКИ:
        if k in b: за_рамка_посока[(k, b[k][0])] += 1

n = len(r)
print(f"  ВСИЧКИ 7 рамки сочат ЕДНА посока : {еднакви_посока:5d} / {n} = {еднакви_посока/n*100:5.1f}%")
print(f"  ВСИЧКИ 7 са БУКВАЛНО еднакви     : {еднакви_всичко:5d} / {n} = {еднакви_всичко/n*100:5.1f}%")
print(f"\n  колко РАЗЛИЧНИ отчета има в един рън (от 7 рамки):")
for k in sorted(разлики):
    print(f"    {k} различни · {разлики[k]:5d} ръна · {разлики[k]/n*100:5.1f}%")

print("\n  ⚠️  «съгласни са N от 7» на картите е броене на СЕДЕМ КОПИЯ.")

print("\n" + "=" * 72)
print("2 · КОЯ РАМКА ВЗИМА ДУМАТА (best)")
print("=" * 72)
rank = {"premium": 3, "strong": 2, "medium": 1, "weak": 0}
кой = collections.Counter()
for x in r:
    b = x["board"]
    д = [(k,) + tuple(b[k]) for k in РАМКИ if k in b]
    акт = [q for q in д if q[1] != "wait" and q[3] != "weak"]
    if not акт: continue
    best = max(д, key=lambda q: (rank.get(q[3], 0), q[2]))
    кой[best[0]] += 1
т = sum(кой.values()) or 1
for k, v in кой.most_common():
    print(f"    {k:5s} · {v:5d} · {v/т*100:5.1f}%")
print(f"\n  (при пълно равенство max() връща ПЪРВИЯ — това е «1мин»)")

print("\n" + "=" * 72)
print("3 · ПРИЧИНАТА · структурно доказателство от кода")
print("=" * 72)
s = io.open("live_bot.py", encoding="utf-8").read()
д = ast.parse(s)
sc = [x for x in ast.walk(д) if isinstance(x, ast.FunctionDef) and x.name == "_scores"][0]
изв = set()
for x in ast.walk(sc):
    if isinstance(x, ast.Subscript) and isinstance(x.value, ast.Subscript):
        if isinstance(x.value.value, ast.Name) and x.value.value.id == "df":
            изв.add(ast.unparse(x))
print("  какво чете _scores от рамката:")
for k in sorted(изв):
    print(f"    {k}")
print("""
  Тоест: от ЦЯЛАТА серия се чете САМО ПОСЛЕДНИЯТ БАР.
  А `refs` (sma50, sma20, ago5, ago20, low20, high20) са ЕДНИ И СЪЩИ —
  идват от ДНЕВНАТА крива, за всичките седем рамки.

  От петте лонг-теста:
    cN > sma50    ← Close на последния бар ≈ ЦЕНАТА СЕГА → еднакво за 7-те
    cN > sma20    ← същото                                → еднакво за 7-те
    cN > ago20    ← същото                                → еднакво за 7-те
    ago5/ago20    ← същото                                → еднакво за 7-те
    lN <= low20   ← Low на бара — ЕДИНСТВЕНОТО, което расте с рамката

  ЧЕТИРИ ОТ ПЕТ ТЕСТА СА ЕДНАКВИ ПО КОНСТРУКЦИЯ, не по съвпадение.""")

print("\n" + "=" * 72)
print("4 · КОЛКО БАРА ИМА ВСЯКА РАМКА (стига ли за своя 50-барова средна)")
print("=" * 72)
for lbl, iv, per, rule in ast.literal_eval(
        [ast.unparse(x.value) for x in ast.walk(д)
         if isinstance(x, ast.Assign) and getattr(x.targets[0], "id", "") == "TFS"][0]):
    if lbl == "1ден":
        print(f"    {lbl:5s} · дневна крива, 3г ≈ 750 бара · ✅")
    else:
        мин = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "60m": 60}.get(iv, 60)
        мин = мин * (4 if rule == "4h" else 1)
        дни = int((per or "60d").rstrip("d"))
        бара = int(дни * 23 * 60 / мин)
        print(f"    {lbl:5s} · {per} на {мин:3d}мин ≈ {бара:6d} бара · "
              f"{'✅' if бара > 60 else '❌ малко'}")
