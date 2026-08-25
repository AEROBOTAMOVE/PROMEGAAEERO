# -*- coding: utf-8 -*-
import sys, json, collections, warnings
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore"); sys.path.insert(0,".")
import brain.b_сливане as SL
r = json.load(open("sw_full.json", encoding="utf-8"))
N=len(r)
сур=[]
for x in r:
    d={}
    for к,в in x["всички"].items():
        if в:
            т,г,_=SL.ТАБЛИЦА[к]; d[г]=d.get(г,0)+т
    сур.append(d)

print("[A] ЖИВ ЛИ Е ТАВАНЪТ КАТО ГРАНИЦА НАПРЕД (добавя се 1 условие в групата)")
for г in sorted(SL.ТАВАН_ГРУПА):
    на_макс = sum(1 for d in сур if d.get(г,0) >= SL.ТАВАН_ГРУПА[г])
    print(f"    {г}: кандидати ВЕЧЕ на тавана {на_макс:5d}/{N} = {на_макс/N:5.1%}"
          f"  → толкова щеше да реже таванът още на първото ново условие")

print("\n[B] хазардът, който таванът трябва да спре: «една група вдига картата»")
for праг in (9,14):
    к=[(x,d) for x,d in zip(r,сур) if x["точки"]>=праг]
    ост=[]
    for x,d in к:
        г_макс=max(d, key=lambda g: min(d[g],SL.ТАВАН_ГРУПА[g]))
        без=x["точки"]-min(d[г_макс],SL.ТАВАН_ГРУПА[г_макс])
        ост.append(без)
    if not к: continue
    print(f"    праг {праг}: n={len(к)} · след МАХАНЕ на цялата най-силна група"
          f" остават средно {sum(ост)/len(ост):.2f} т. · минимум {min(ост)} т."
          f" · още ≥{праг}: {sum(1 for b in ост if b>=праг)}")

print("\n[C] крайният контрафакт: всяка група дава НАЙ-МНОГО 1 точка")
for праг in (9,14):
    к=[(x,d) for x,d in zip(r,сур) if x["точки"]>=праг]
    оцел=sum(1 for x,d in к if sum(min(с,1) for с in d.values())>=праг)
    print(f"    праг {праг}: {len(к)} карти → оцеляват {оцел} (макс възможно = 8 точки)")

print("\n[D] колко точки ОБЩО реже целият механизъм на живо")
общо=0; cnt=0
for d in сур:
    c=sum(max(0,с-SL.ТАВАН_ГРУПА[г]) for г,с in d.items())
    общо+=c; cnt+= (c>0)
print(f"    отрязани точки общо: {общо} · засегнати кандидати: {cnt}/{N} = {cnt/N:.2%}")
