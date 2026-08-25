# -*- coding: utf-8 -*-
import sys, datetime as dt, hashlib
from pathlib import Path
Б=Path(__file__).resolve().parent; sys.path.insert(0,str(Б)); sys.argv=["x"]
import огледало as ог
lb, st = ог.lb, ог.st
def h(t): return hashlib.sha1(str(t).encode()).hexdigest()[:10]

print("── ОТВОРЕНА СДЕЛКА: мени се САМО възрастта (изход по време = 30 кал. дни) ──")
хс, хп, хг = set(), set(), set()
for дни in (0,1,5,10,15,20,25,29):
    отв = dt.datetime(2026,8,11,9,12,tzinfo=dt.timezone.utc)-dt.timedelta(days=дни)
    tr={"direction":"long","entry":4358.00,"opened":отв.isoformat(),
        "levels":{"tp1":4365.5,"tp2":4370.0,"tp3":4378.0,"sl":4338.0},
        "hit":{"tp1":True},"sym":"XAUUSD"}
    с=lb._status_msg(ог.brd,"long",tr,None,{"mid":4365.2},{"mid":65.15},0.,0.,{"long":1},False,"2026-08-11",ог.mac)
    п=lb._pulse_msg("14",ог.brd,ог.best,"long","",True,tr,None,{"mid":4365.2},{"mid":65.15},
        ог.mac,False,False,macro_raw={"долар":.0145,"лихви":.07},streaks={"long":1},stats=st)
    г=lb._sig_msg("long",6,5,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-11T11:15",
        lb._levels(4365.2,"long"),4365.20,ог.СЪВЕТ["да1"][0],ог.mac,1,{"vol_rank":.35},st,5000,2.0,
        adv_ok=True,open_trade=tr)
    хс.add(с); хп.add(п); хг.add(г)
    print(f"  ден {дни:>2}/30 · статус {h(с)} · пулс {h(п)} · сигнал {h(г)}")
print(f"\n  РАЗЛИЧНИ карти: статус {len(хс)}/8 · пулс {len(хп)}/8 · сигнал {len(хг)}/8")
print("  → нито една карта не мърда, докато сделката отива към изхода по време\n")

print("── СТОЯЩ СЕТЪП: мени се САМО възрастта (таван %.0fч) ──" % lb.СТОЯЩ_МАКС_Ч)
х=set()
for ч in (1,6,12,23,24,25,48,276,999):
    т=lb._standing_msg("long",ог.best,ч,{"mid":4365.2},4365.0,4365.20,ог.brd,
        {"долар":True,"лихви":True},None,"2026-08-11T11:20")
    х.add(т)
    print(f"  {ч:>4}ч · {h(т)} · ред2: {[r for r in t.split(chr(10))][1] if (t:=__import__('re').sub('<[^>]+>','',т)) else ''}")
print(f"\n  РАЗЛИЧНИ карти: {len(х)}/9  (25ч..999ч дават ЕДНА И СЪЩА карта)")

print("\n── ПОСЛЕДНИЯТ РЕД на всеки отказ ──")
случаи=[("сребро ИЗКЛЮЧЕНО (постоянен)",("long",1,st,None,False,0,"XAGUSD",False)),
        ("стара цена (минути)",("long",1,st,None,False,0,"XAUUSD",True)),
        ("стоп-пазач (до утре)",("long",1,st,None,False,3,"XAUUSD",False)),
        ("US-щит (часове)",("short",1,st,None,True,0,"XAUUSD",False)),
        ("няма статистика (повреда)",("long",1,{},None,False,0,"XAUUSD",False)),
        ("mixed макро (медиана 4 дни)",("long",0,st,None,False,0,"XAUUSD",False)),
        ("ИЗЧАКАЙ клас (никога)",("short",2,st,None,False,0,"XAUUSD",False))]
import re,html
for име,а in случаи:
    т,ok=lb._advice_entry(*а)
    к=lb._sig_msg("long" if а[0]=="long" else "short",6,5,"СИЛЕН",
        None if а[7] else {"mid":4365.2},4365.0,"2026-08-11T11:15",
        lb._levels(4365.2,а[0]),4365.20,т,ог.mac,а[1],{"vol_rank":.35},st,5000,2.0,adv_ok=ok,
        sym=а[6],dec=2 if а[6]=="XAUUSD" else 3)
    р=re.sub("<[^>]+>","",html.unescape(к)).splitlines()
    print(f"  {име:32s} → {р[-1]}")
