# -*- coding: utf-8 -*-
"""Отказващите/изчакващите карти, които огледалото НЕ рендерира."""
import sys, re, html, json, os, datetime as dt
from pathlib import Path
Б = Path(__file__).resolve().parent
sys.path.insert(0, str(Б)); sys.argv=["x"]
import огледало as ог
lb, st = ог.lb, ог.st
def чист(t): return re.sub(r"<[^>]+>", "", html.unescape(str(t)))
def показ(име, т):
    т = чист(т)
    print("="*68); print(f"### {име}  [{len(т.splitlines())} реда]"); print("="*68); print(т); print()

# ── сурови присъди ────────────────────────────────────────────────
print("########## СУРОВИ ПРИСЪДИ _advice_entry ##########")
слу = [
 ("злато mixed long",   ("long",0,st,None,False,0,"XAUUSD",False,None)),
 ("злато mixed short",  ("short",0,st,None,False,0,"XAUUSD",False,None)),
 ("злато fresh short",  ("short",2,st,None,False,0,"XAUUSD",False,None)),
 ("злато stale short",  ("short",5,st,None,False,0,"XAUUSD",False,None)),
 ("СРЕБРО long",        ("long",1,st,None,False,0,"XAGUSD",False,None)),
 ("СРЕБРО mixed",       ("long",0,st,None,False,0,"XAGUSD",False,None)),
 ("стара цена",         ("long",1,st,None,False,0,"XAUUSD",True,None)),
 ("стоп-пазач 2",       ("long",1,st,None,False,2,"XAUUSD",False,None)),
 ("стоп-пазач 4",       ("long",1,st,None,False,4,"XAUUSD",False,None)),
 ("US-щит шорт",        ("short",1,st,None,True,0,"XAUUSD",False,None)),
 ("НЯМА статистика",    ("long",1,{},None,False,0,"XAUUSD",False,None)),
]
for име,(a) in слу:
    t,ok = lb._advice_entry(*a)
    print(f"  {име:22s} ok={str(ok):5s} · {t}")
print()

# ── карти ─────────────────────────────────────────────────────────
lvs = lb._levels(4365.20, "short")
lv  = lb._levels(4365.20, "long")
macm = {"долар": False, "лихви": True, "миньори": False}

# сребро — отказ
_т,_ok = lb._advice_entry("long",1,st,None,False,0,"XAGUSD")
показ("СИГНАЛ · СРЕБРО отказ (ПОСТОЯНЕН)", lb._sig_msg(
  "long",6,5,"СИЛЕН",{"mid":65.15},65.10,"2026-08-11T11:15",
  lb._levels_silver(65.15,"long"),65.15,_т,ог.mac,1,{"vol_rank":.35},st,5000,2.0,
  adv_ok=_ok, sym="XAGUSD", dec=3))

# стара цена
_т,_ok = lb._advice_entry("long",1,st,None,False,0,"XAUUSD",stale_price=True)
показ("СИГНАЛ · стара цена (ВРЕМЕНЕН, минути)", lb._sig_msg(
  "long",6,5,"СИЛЕН",None,4365.0,"2026-08-11T11:15",lv,4365.20,_т,ог.mac,1,
  {"vol_rank":.35},st,5000,2.0,adv_ok=_ok))

# стоп-пазач
_т,_ok = lb._advice_entry("long",1,st,None,False,3)
показ("СИГНАЛ · стоп-пазач 3 (ВРЕМЕНЕН, до утре)", lb._sig_msg(
  "long",6,5,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-11T11:15",lv,4365.20,_т,ог.mac,1,
  {"vol_rank":.35},st,5000,2.0,adv_ok=_ok))

# US щит
_т,_ok = lb._advice_entry("short",1,st,None,True,0)
показ("СИГНАЛ · US-щит (ВРЕМЕНЕН, часове)", lb._sig_msg(
  "short",6,5,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-11T11:15",lvs,4365.20,_т,macm,1,
  {"vol_rank":.35},st,5000,2.0,adv_ok=_ok))

# няма статистика
_т,_ok = lb._advice_entry("long",1,{},None,False,0)
показ("СИГНАЛ · няма статистика (ПОВРЕДА)", lb._sig_msg(
  "long",6,5,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-11T11:15",lv,4365.20,_т,ог.mac,1,
  {"vol_rank":.35},st,5000,2.0,adv_ok=_ok))

# ── СТОЯЩ на различна възраст ────────────────────────────────────
for ч in (3, 23, 25, 276):
    показ(f"СТОЯЩ · възраст {ч}ч (таван {lb.СТОЯЩ_МАКС_Ч}ч)", lb._standing_msg(
      "long", ог.best, ч, {"mid":4365.2}, 4365.0, 4365.20, ог.brd,
      {"долар":True,"лихви":True}, None, "2026-08-11T11:20"))

# ── ОТВОРЕНА СДЕЛКА на различна възраст (време-изход 30 кал. дни) ──
for дни in (1, 15, 29):
    отв = dt.datetime(2026,8,11,9,12,tzinfo=dt.timezone.utc) - dt.timedelta(days=дни)
    tr = {"direction":"long","entry":4358.00,"opened":отв.isoformat(),
          "levels":{"tp1":4365.5,"tp2":4370.0,"tp3":4378.0,"sl":4338.0},
          "hit":{"tp1":True},"sym":"XAUUSD"}
    показ(f"СИГНАЛ при отворена · сделката е на {дни} дни от 30", lb._sig_msg(
      "long",6,5,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-11T11:15",lv,4365.20,
      ог.СЪВЕТ["да1"][0],ог.mac,1,{"vol_rank":.35},st,5000,2.0,adv_ok=True,open_trade=tr))
    показ(f"СТАТУС · сделката е на {дни} дни от 30", lb._status_msg(
      ог.brd,"long",tr,None,{"mid":4365.2},{"mid":65.15},0.0,0.0,ог.mac,
      {"long":1},0,"2026-08-11T11:15",st))

показ("ИЗХОД ПО ВРЕМЕ (kind='time')", lb._exit_msg("time",
   {"direction":"long","entry":4358.00,"opened":"2026-07-12T09:12",
    "levels":{"tp1":4365.5,"tp2":4370.0,"tp3":4378.0,"sl":4358.0},
    "hit":{"tp1":True},"sym":"XAUUSD"}, 4361.0, "2026-08-11T11:15","бар",False))
