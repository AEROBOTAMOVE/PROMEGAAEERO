# -*- coding: utf-8 -*-
"""№48: достижима ли е уикенд-картичката при реалните cron-и?"""
import sys
from datetime import datetime, timedelta, timezone
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb

# крон-ите от .github/workflows/aero-bot.yml
КРОН = [(range(0,60,5),  range(5,22), {0,1,2,3,4}),   # */5 5-21 * * 1-5
        (range(0,60,10), (22,23),     {6,0,1,2,3,4}), # */10 22,23 * * 0-5  (0=нед в cron)
        (range(0,60,15), range(0,5),  {0,1,2,3,4})]   # */15 0-4 * * 1-5
# cron: 0=нед..6=съб  →  python weekday(): 0=пон..6=нед. Превод:
def cron_dow(dt): return (dt.weekday()+1) % 7   # пон(0)->1 ... нед(6)->0

t0=datetime(2026,8,1,tzinfo=timezone.utc)
общо=0; затворено=0; в_слот=0; примери=[]
слотове={}
d=t0
while d < t0+timedelta(days=365):
    for mins,hours,dows in КРОН:
        if cron_dow(d) not in dows: continue
        if d.hour not in hours: continue
        if d.minute not in mins: continue
        общо+=1
        iso=d.replace(tzinfo=None).isoformat()
        if lb._market_closed(iso):
            затворено+=1
            s=lb._weekend_slot(iso)
            слотове[s]=слотове.get(s,0)+1
            if s:
                в_слот+=1
                if len(примери)<5: примери.append((iso,s))
        break
    d+=timedelta(minutes=1)
print("планирани пускания за 365 дни:", общо)
print("от тях при ЗАТВОРЕН пазар (уикенд-път):", затворено)
print("от тях ПОПАДАЩИ в слот (картичката излиза):", в_слот)
print("разпределение на слотовете при затворен пазар:", слотове)
print("примери:", примери)
# кои софийски часове изобщо се случват при затворен пазар
ч=set()
d=t0
while d < t0+timedelta(days=14):
    for mins,hours,dows in КРОН:
        if cron_dow(d) in dows and d.hour in hours and d.minute in mins:
            iso=d.replace(tzinfo=None).isoformat()
            if lb._market_closed(iso): ч.add(lb._sofia_hour(iso))
            break
    d+=timedelta(minutes=1)
print("СОФИЙСКИ часове, достижими при затворен пазар (2 седмици):", sorted(ч))
print("прозорците на картичката са: 9-11, 15-17, 20-22 София")
