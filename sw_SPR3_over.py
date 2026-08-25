# -*- coding: utf-8 -*-
"""За ЦЕЛИТЕ, засечени по СПОТ пътя: колко е ПРЕВИШЕНИЕТО на средата над нивото,
сравнено с ПОЛОВИН СПРЕД? Ако превишението >= половин спред, лимитната поръчка
на нивото Е била изпълнима -> няма дефект. Дефектът е само в тесния прозорец."""
import json, io, re, datetime as dt, statistics as st
# индекс на журнала по run_utc
J={}
for ln in io.open('live/live_journal.jsonl',encoding='utf-8'):
    ln=ln.strip()
    if not ln: continue
    r=json.loads(ln)
    J[r['run_utc']]=r
print("рънове в журнала:",len(J))
sp=[r['spread'] for r in J.values() if r.get('spread')]
sp.sort()
print("СПРЕД (n=%d): медиана=%.3f p10=%.3f p90=%.3f"%(len(sp),sp[len(sp)//2],sp[len(sp)//10],sp[int(len(sp)*.9)]))
def num(s): return float(s.replace(',',''))
out=[]
for ln in io.open('live/sent_log.jsonl',encoding='utf-8'):
    ln=ln.strip()
    if not ln: continue
    r=json.loads(ln); t=str(r.get('tag') or '')
    if not (t.startswith('sh-exit:tp') or t.startswith('s-exit:tp')): continue
    m=re.search(r'(\d{2}):(\d{2}) София', r['text']) or re.search(r'· (\d{2}):(\d{2})\b', r['text'])
    if not m: continue
    u=dt.datetime.fromisoformat(r['utc']); sof=u+dt.timedelta(hours=3)
    d=(sof-sof.replace(hour=int(m.group(1)),minute=int(m.group(2)),second=0,microsecond=0)).total_seconds()/60
    if d<-60: d+=1440
    if d>3: continue                       # барен път -> не е предмет на находката
    ц=re.search(r'<code>([\d,\.]+)</code>\s*→\s*<code>([\d,\.]+)</code>', r['text'])
    if not ц: continue
    вх, ниво = num(ц.group(1)), num(ц.group(2))
    посока = 'short' if ниво<вх else 'long'
    # рънът: run_utc е закръглен на 5 мин преди r['utc']
    key=None
    for back in range(0,25):
        cand=(u-dt.timedelta(minutes=back)).strftime('%Y-%m-%dT%H:%M')
        if cand in J and J[cand].get('spot'): key=cand; break
    if key is None: out.append((r['utc'],t,'НЯМА РЪН',None,None,None)); continue
    mid=J[key]['spot']; spread=J[key].get('spread') or 0.0
    over = (mid-ниво) if посока=='long' else (ниво-mid)
    out.append((r['utc'],t.split(':')[1],посока,round(ниво,2),round(mid,3),round(spread,3),round(over,3),
                'ФАЛШИВ' if over < spread/2 else 'реален'))
print("\nЦЕЛИ по СПОТ път:",len(out))
for o in out: print(o)
bad=[o for o in out if len(o)>7 and o[7]=='ФАЛШИВ']
print("\nв тесния прозорец (среда мина, но BID/ASK още НЕ):",len(bad),"от",len(out))
