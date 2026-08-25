# -*- coding: utf-8 -*-
"""ОБОРВАНЕ 48: срещу кой часовник е мерено?"""
import sys, json, collections
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb

# --- 1. възпроизвеждам сметката на одитора (yml-крон), 365 дни ---
КРОН=[(range(0,60,5),set(range(5,22)),{1,2,3,4,5}),
      (range(0,60,10),{22,23},{0,1,2,3,4,5}),
      (range(0,60,15),set(range(0,5)),{1,2,3,4,5})]
def cdow(d): return (d.weekday()+1)%7
t0=datetime(2026,8,1); общо=zатв=вслот=0; чс=collections.Counter()
d=t0
while d<t0+timedelta(days=365):
    for mins,hrs,dows in КРОН:
        if cdow(d) in dows and d.hour in hrs and d.minute in mins:
            общо+=1; iso=d.isoformat(timespec="minutes")
            if lb._market_closed(iso):
                zатв+=1; чс[lb._sofia_hour(iso)]+=1
                if lb._weekend_slot(iso): вслот+=1
            break
    d+=timedelta(minutes=1)
print(f"[yml-часовник] планирани {общо} · при затворен пазар {zатв} · в слот {вслот}")
print("  софийски часове при затворен пазар:", dict(sorted(чс.items())))

# --- 2. СЪЩАТА сметка, но срещу РЕАЛНИЯ часовник (измерен от дневника) ---
# измерено: */5 непрекъснато от неделя 22:00 UTC до петък 20:59 UTC
общо2=zатв2=вслот2=0
d=t0
while d<t0+timedelta(days=365):
    w=d.weekday()   # 0=пон..6=нед
    жив = (w<=3) or (w==4 and d.hour<21) or (w==6 and d.hour>=22)
    if жив and d.minute%5==0:
        общо2+=1; iso=d.isoformat(timespec="minutes")
        if lb._market_closed(iso):
            zатв2+=1
            if lb._weekend_slot(iso): вслот2+=1
    d+=timedelta(minutes=1)
print(f"[РЕАЛЕН часовник] пускания {общо2} · при затворен пазар {zатв2} · в слот {вслот2}")

# --- 3. кодът работи ли, ако часовникът покрива уикенда? (юлски РЕАЛНИ моменти) ---
rows=[]
for ln in Path("live/archive/live_journal-2026-07.jsonl").read_text(encoding="utf-8",errors="replace").splitlines():
    ln=ln.strip()
    if ln:
        try: rows.append(json.loads(ln))
        except Exception: pass
ts=sorted(set(r["run_utc"] for r in rows if r.get("run_utc")))
зат=[t for t in ts if lb._market_closed(t)]
всл=[(t,lb._weekend_slot(t)) for t in зат if lb._weekend_slot(t)]
print(f"\n[ЮЛИ, реални моменти от дневника] всичко {len(ts)} · при затворен пазар {len(зат)} · ПОПАДАЩИ В СЛОТ {len(всл)}")
print("  първите 6:", всл[:6])
# колко РАЗЛИЧНИ (дата·слот) картички биха излезли
уник=sorted({(t[:10],s) for t,s in всл})
print(f"  различни картички (дата·слот), които днешният код би пуснал: {len(уник)} → {уник}")
print("  примерна картичка:", repr(lb._weekend_msg(уник[0][1], уник[0][0])) if уник else "—")
