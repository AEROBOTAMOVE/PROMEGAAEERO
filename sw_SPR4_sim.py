# -*- coding: utf-8 -*-
"""СИМУЛАЦИЯ на РЕАЛНАТА спот-серия (live_journal.jsonl, златото).
Сравнявам ДВА съдника за ЦЕЛИТЕ по спот-пътя:
  A) както е в бота: удар когато СРЕДАТА мине нивото; фил = нивото
  B) микроструктурно честният: удар когато BID>=цел (лонг) / ASK<=цел (шорт); фил = нивото
Меря: (1) колко често A пали в тесния прозорец, в който B още мълчи
       (2) от тях колко са ФАНТОМИ (B никога не пали преди стопа) -> това са ИСТИНСКИ пари
       (3) средна грешка в $/сделка"""
import sys, json, io
sys.argv=["x"]; import live_bot as lb
T=[]
for ln in io.open('live/live_journal.jsonl',encoding='utf-8'):
    ln=ln.strip()
    if not ln: continue
    r=json.loads(ln)
    if r.get('spot') and r.get('spread') and not r.get('spot_rejected'):
        T.append((r['run_utc'], float(r['spot']), float(r['spread'])))
print("тикове със ЖИВ спот:",len(T))
узък=0; фантом=0; общо=0; грешка=0.0; закъснение=[]
for посока in ("long","short"):
    зн = 1 if посока=="long" else -1
    for i in range(0,len(T)-1):
        _,mid,s = T[i]
        вх = mid + зн*s/2                      # _entry_side: лонг->ask, шорт->bid
        lv = lb._levels(round(вх,2), посока)
        tp, sl = lv["tp1"], lv["sl"]
        # път напред: първи тик, на който СРЕДАТА мине целта (както прави ботът)
        jA=None; jB=None; jSL=None
        for j in range(i+1, min(i+200,len(T))):
            _,m,sp2 = T[j]
            bid, ask = m-sp2/2, m+sp2/2
            if jSL is None and ((m<=sl) if посока=="long" else (m>=sl)): jSL=j
            if jA is None and ((m>=tp) if посока=="long" else (m<=tp)): jA=j
            if jB is None and ((bid>=tp) if посока=="long" else (ask<=tp)): jB=j
            if jA is not None and (jB is not None or jSL is not None): break
        if jA is None: continue
        if jSL is not None and jSL < jA: continue      # стопът пръв -> няма цел
        общо+=1
        if jB==jA: continue
        узък+=1
        if jB is None or (jSL is not None and jSL<jB):
            фантом+=1; грешка += abs(tp-вх)            # цялата «печалба» е фалшива
        else:
            закъснение.append(jB-jA)
print("сделки с ударена ЦЕЛ1 (по спот-съдника):",общо)
print("от тях в ТЕСНИЯ прозорец (среда мина, страната не):",узък, "= %.2f%%"%(100*узък/max(общо,1)))
print("от тях ФАНТОМИ (страната НИКОГА не стигна целта):",фантом, "= %.2f%%"%(100*фантом/max(общо,1)))
print("останалите се пълнят по-късно; закъснение (тикове по 5 мин): n=%d медиана=%s max=%s"
      %(len(закъснение), sorted(закъснение)[len(закъснение)//2] if закъснение else '-', max(закъснение) if закъснение else '-'))
print("средна ПАРИЧНА грешка: %.4f $/сделка (твърдението беше ~0.10)"%(грешка/max(общо,1)))
