# -*- coding: utf-8 -*-
import json, io
rows=[json.loads(l) for l in io.open("live/brain_journal.jsonl",encoding="utf-8") if l.strip()]
pr=sorted([r for r in rows if r.get("праща")], key=lambda r:r["utc"])
res=[json.loads(l) for l in io.open("live/brain_result.jsonl",encoding="utf-8") if l.strip()]
FIX="2026-08-11T17:26"   # първата развръзка = моментът, от който следенето РАБОТИ (ОДИТ-34)
pre=[r for r in pr if r["utc"]<FIX]; post=[r for r in pr if r["utc"]>=FIX]
print("пратени ПРЕДИ фикса ОДИТ-34 (следенето изобщо не се отваряше):", len(pre))
print("пратени СЛЕД фикса:", len(post))
print("развръзки:", len(res))
print("покритие на форуърд-теста ОТ ЖИВИЯ КОД:", f"{len(res)}/{len(post)} = {100*len(res)/len(post):.0f}%")
print("непокрити от живия код:", len(post)-len(res))
print()
print("твърдението на одитора: 15/31 = %.0f%% («под половината»)" % (100*15/31))
print("реалното за днешния код:  15/25 = %.0f%%" % (100*15/25))
print()
# всяка ли пратена карта има пълен ред в дневника (нива на живата скала)?
пълни=sum(1 for r in pr if all(r.get(k) is not None for k in ("живо_вход","живо_стоп","живо_цел")))
print("пратени карти с ПЪЛЕН ред в brain_journal.jsonl (живи нива):", пълни, "от", len(pr))
