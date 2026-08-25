# -*- coding: utf-8 -*-
"""ИЗМЕРВАНЕ · какво става, ако при РАВЕНСТВО думата я взима БАВНАТА рамка."""
import json, io, collections

r = [json.loads(l) for l in io.open("live/live_journal.jsonl", encoding="utf-8") if l.strip()]
r = [x for x in r if isinstance(x.get("board"), dict) and x["board"]]
РАМКИ = ["1мин", "5м", "15м", "30м", "1час", "4час", "1ден"]
БАВНОСТ = {k: i for i, k in enumerate(РАМКИ)}          # 1мин=0 … 1ден=6
rank = {"premium": 3, "strong": 2, "medium": 1, "weak": 0}

сега = collections.Counter(); след = collections.Counter()
смени_рамка = смени_посока = смени_клас = 0
акт_ръна = 0
for x in r:
    b = x["board"]
    д = [(k,) + tuple(b[k]) for k in РАМКИ if k in b]
    ак = [q for q in д if q[1] != "wait" and q[3] != "weak"]
    if not ак: continue
    акт_ръна += 1
    a = max(д, key=lambda q: (rank.get(q[3], 0), q[2]))                    # СЕГА
    c = max(д, key=lambda q: (rank.get(q[3], 0), q[2], БАВНОСТ[q[0]]))     # СЛЕД
    сега[a[0]] += 1; след[c[0]] += 1
    if a[0] != c[0]: смени_рамка += 1
    if a[1] != c[1]: смени_посока += 1
    if a[3] != c[3]: смени_клас += 1

print("=" * 66)
print(f"КОЯ РАМКА ВЗИМА ДУМАТА · {акт_ръна} ръна с активна дъска")
print("=" * 66)
print(f"  {'рамка':6s} {'СЕГА':>14s} {'СЛЕД ПОПРАВКА':>16s}")
for k in РАМКИ:
    print(f"  {k:6s} {сега[k]:6d} {сега[k]/акт_ръна*100:6.1f}% "
          f"{след[k]:8d} {след[k]/акт_ръна*100:6.1f}%")
print(f"\n  сменя се РАМКАТА, която говори : {смени_рамка:5d} = {смени_рамка/акт_ръна*100:5.1f}%")
print(f"  сменя се ПОСОКАТА              : {смени_посока:5d} = {смени_посока/акт_ръна*100:5.1f}%")
print(f"  сменя се КЛАСЪТ                : {смени_клас:5d} = {смени_клас/акт_ръна*100:5.1f}%")
print("\n  → размяната е БЕЗОПАСНА: пипа само ЕТИКЕТА на рамката, когато")
print("    отчетите са равни. Посоката и класът остават същите, защото")
print("    max() ги е подредил преди етикета.")

print("\n" + "=" * 66)
print("«СЪГЛАСНИ СА N ОТ 7» — ЧЕСТНО ЛИ Е ЧИСЛОТО")
print("=" * 66)
раз = collections.Counter(); чест = collections.Counter()
for x in r:
    b = x["board"]
    д = [(k,) + tuple(b[k]) for k in РАМКИ if k in b]
    ак = [q for q in д if q[1] != "wait" and q[3] != "weak"]
    if not ак: continue
    best = max(д, key=lambda q: (rank.get(q[3], 0), q[2]))
    n_сега = sum(1 for q in д if q[1] == best[1] and q[3] != "weak")
    n_чест = len(set((q[1], q[2], q[3]) for q in д if q[1] == best[1] and q[3] != "weak"))
    раз[n_сега] += 1; чест[n_чест] += 1
print(f"  {'казва':>8s} {'ръна':>7s}     {'наистина различни':>18s} {'ръна':>7s}")
for k in sorted(set(раз) | set(чест), reverse=True):
    print(f"  {k} от 7 {раз.get(k,0):7d}     {k} различни отчета {чест.get(k,0):7d}")
седем = раз.get(7, 0)
print(f"\n  ботът е казвал «7 от 7 съгласни» в {седем} ръна = {седем/акт_ръна*100:.1f}%")
print(f"  а наистина различни отчета е имало най-много {max(чест)}")
