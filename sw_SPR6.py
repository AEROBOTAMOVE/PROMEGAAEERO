# -*- coding: utf-8 -*-
"""1) Единственият измерен ТЕСЕН случай (04.08 tp2 SHORT, цел 4086.41):
      стигна ли ASK по-късно нивото -> лимитната поръчка щеше ли да се напълни?
   2) Има ли РЕАЛНА (не сянка) сделка в 17-те дни журнал?"""
import json,io,datetime as dt
T=[]
for ln in io.open('live/live_journal.jsonl',encoding='utf-8'):
    ln=ln.strip()
    if not ln: continue
    r=json.loads(ln); T.append(r)
print("рънове:",len(T),"| с РЕАЛНА сделка:",sum(1 for r in T if r.get('trade')))
t0=dt.datetime.fromisoformat("2026-08-04T18:01")
цел=4086.41
след=[(r['run_utc'],r['spot'],r['spread']) for r in T
      if r.get('spot') and dt.datetime.fromisoformat(r['run_utc'])>=t0][:40]
първи=None
for k,(u,m,s) in enumerate(след):
    ask=m+(s or 0)/2
    if ask<=цел: първи=(u,round(m,3),round(ask,3),k); break
print("след 18:01 ASK<=4086.41 за пръв път:",първи)
print("първите 6 тика след това:",[(u,round(m,2)) for u,m,s in след[:6]])
