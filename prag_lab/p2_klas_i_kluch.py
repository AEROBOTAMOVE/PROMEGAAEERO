# -*- coding: utf-8 -*-
"""P2: клас-разпределение + СМЕНИ НА КЛЮЧА при мрежа от прагове, върху 4404 живи ръна."""
import json, io, collections
J="live/live_journal.jsonl"
rows=[json.loads(l) for l in io.open(J,encoding="utf-8") if l.strip()]

def board_of(d, TM, TS):
    """връща списък (frame, dir, score, tier) при прагове medium>=TM, strong>=TS"""
    mac=d.get("macro") or {}
    mrt=(d.get("macro_raw") or {}).get("мъртви") or []
    m3l=bool(mac) and all(mac.values()); m3s=bool(mac) and not any(mac.values())
    out=[]
    for f,v in (d.get("board") or {}).items():
        if not isinstance(v,list) or len(v)<3: continue
        dr,sc=v[0],v[1]
        if dr=="wait": tk="weak"
        else:
            m3 = m3l if dr=="long" else m3s
            tk = "premium" if m3 else ("strong" if sc>=TS else ("medium" if sc>=TM else "weak"))
            if tk=="premium" and mrt: tk="strong"
        out.append((f,dr,sc,tk))
    return out

def key_of(bd):
    o=sorted({f"{d}:{t}" for _f,d,_s,t in bd if t!="weak" and d!="wait"})
    return (f"{len(o)}|"+";".join(o)) if o else ""

# --- клас-разпределение при ЖИВИТЕ прагове
cnt=collections.Counter(); cnt_dir=collections.Counter()
for d in rows:
    for f,dr,sc,tk in board_of(d,4,6):
        cnt[tk]+=1; cnt_dir[(dr,tk)]+=1
tot=sum(cnt.values())
print("КЛАС-РАЗПРЕДЕЛЕНИЕ (живи прагове 4/6), 30828 клетки:")
for k in ("premium","strong","medium","weak"):
    print(f"   {k:8s} {cnt[k]:7d}  {100*cnt[k]/tot:6.2f}%")
print("   по посока:", dict(cnt_dir))
print()

# --- сверка на «79 смени»
def smeni(TM,TS, само_активни=False):
    last=None; n=0; keys=set(); aktiv=0; runs=0
    for d in rows:
        bd=board_of(d,TM,TS); k=key_of(bd)
        runs+=1
        if k: aktiv+=1; keys.add(k)
        if last is None: last=k; continue
        if k!=last: n+=1
        last=k
    return n, len(keys), aktiv, runs

n,nk,akt,runs = smeni(4,6)
print(f"ЖИВИ ПРАГОВЕ 4/6:  смени на ключа = {n}   различни ключа = {nk}   "
      f"ръна с активна дъска = {akt}/{runs}")
print()
print("МРЕЖА ОТ ПРАГОВЕ  (T_medium / T_strong):")
print(f"{'TM':>3}{'TS':>4}  {'смени':>7} {'разл.ключа':>11} {'активни ръна':>13}  {'Δсмени':>8} {'Δактивни':>9}")
base=None
grid=[(1,2),(2,3),(3,4),(3,5),(4,5),(4,6),(4,7),(5,6),(5,7),(5,8),(6,7),(6,8),(7,8),(7,9),(8,9),(9,10),(0,1)]
for TM,TS in grid:
    n,nk,akt,runs=smeni(TM,TS)
    if (TM,TS)==(4,6): base=(n,nk,akt)
for TM,TS in grid:
    n,nk,akt,runs=smeni(TM,TS)
    mark=" <== ЖИВОТО" if (TM,TS)==(4,6) else ""
    print(f"{TM:>3}{TS:>4}  {n:>7} {nk:>11} {akt:>13}  {n-base[0]:>+8} {akt-base[2]:>+9}{mark}")
