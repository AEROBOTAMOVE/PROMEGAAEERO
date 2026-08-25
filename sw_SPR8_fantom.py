# -*- coding: utf-8 -*-
import sys, json, io
sys.argv=["x"]; import live_bot as lb
T=[]
for ln in io.open('live/live_journal.jsonl',encoding='utf-8'):
    ln=ln.strip()
    if not ln: continue
    r=json.loads(ln)
    if r.get('spot') and r.get('spread') and not r.get('spot_rejected'):
        T.append((float(r['spot']), float(r['spread'])))
общо=узък=ф_стоп=ф_край=0; грешка=0.0
for посока in ("long","short"):
    зн=1 if посока=="long" else -1
    for i in range(len(T)-1):
        mid,s=T[i]; вх=mid+зн*s/2
        lv=lb._levels(round(вх,2),посока); tp,sl=lv["tp1"],lv["sl"]
        jA=jB=jSL=None
        край=min(i+600,len(T))
        for j in range(i+1,край):
            m,sp=T[j]; bid,ask=m-sp/2,m+sp/2
            if jSL is None and ((m<=sl) if посока=="long" else (m>=sl)): jSL=j
            if jA is None and ((m>=tp) if посока=="long" else (m<=tp)): jA=j
            if jB is None and ((bid>=tp) if посока=="long" else (ask<=tp)): jB=j
            if jA is not None and jB is not None: break
            if jA is not None and jSL is not None: break
        if jA is None: continue
        if jSL is not None and jSL<jA: continue
        общо+=1
        if jB==jA: continue
        узък+=1
        if jB is not None and (jSL is None or jB<jSL): continue      # напълва се по-късно, 0 пари
        if jSL is not None: ф_стоп+=1; грешка+=abs(tp-вх)
        else: ф_край+=1                                             # прозорецът свърши, неизвестно
print("ЦЕЛ1 засечена по спот-съдника: n=%d"%общо)
print("тесен прозорец (среда мина, страната не): %d (%.2f%%)"%(узък,100*узък/общо))
print("  → напълва се по-късно на СЪЩОТО ниво, 0.00$ грешка: %d"%(узък-ф_стоп-ф_край))
print("  → ФАНТОМ (стопът удари преди страната да стигне): %d (%.2f%%)"%(ф_стоп,100*ф_стоп/общо))
print("  → неопределени (прозорецът от 600 тика свърши): %d"%ф_край)
print("ПАРИЧНА грешка, ако спотът беше ЕДИНСТВЕНИЯТ съдник: %.4f $/сделка"%(грешка/общо))
print("производството: спот-съдникът решава 20%% от целите → %.4f $/сделка"%(0.20*грешка/общо))
