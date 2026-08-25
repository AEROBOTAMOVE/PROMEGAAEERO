# -*- coding: utf-8 -*-
import json, io, datetime as dt
rows=[json.loads(l) for l in io.open("live/brain_journal.jsonl",encoding="utf-8") if l.strip()]
res=[json.loads(l) for l in io.open("live/brain_result.jsonl",encoding="utf-8") if l.strip()]
pr=sorted([r for r in rows if r.get("праща")], key=lambda r:r["utc"])
print("=== 31-те ПРАТЕНИ: имат ли пълни нива (вход+стоп+цел)? ===")
без=0
for r in pr:
    ok = all(r.get(k) is not None for k in ("вход","стоп","цел"))
    if not ok:
        без+=1
        print("  БЕЗ ПЪЛНИ НИВА:", r["utc"], r.get("рамка"), r.get("посока"),
              "вход",r.get("вход"),"стоп",r.get("стоп"),"цел",r.get("цел"), "| ранг-повод:", r.get("повод"))
print("  пратени без пълни нива:", без, "от", len(pr))
print()
print("=== прозорците на РАЗВРЪЗКИТЕ ===")
w=[(r["отворен"], r.get("затворен"), r.get("рамка"), r.get("изход")) for r in res]
for a,b,f,x in sorted(w): print("  ", a, "->", b, f, x)
print()
def P(s): return dt.datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
win=[(P(a),P(b)) for a,b,_,_ in w if b]
print("=== всяка пратена карта: попада ли ВЪТРЕ в чужд отворен прозорец? ===")
блок=0
for r in pr:
    t=P(r["utc"])
    hit=[ (a,b) for a,b in win if a<t<=b ]
    mark = "БЛОКИРАНА(в чужд прозорец)" if hit else "свободно"
    if hit: блок+=1
    print("  ",r["utc"], r.get("рамка"), r.get("посока"), "->", mark, (hit[0] if hit else ""))
print("  блокирани от отворено следене:", блок, "от", len(pr))
