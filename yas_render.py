import sys, json, re
sys.argv=["x"]; import live_bot as lb
st=json.load(open("backtest_stats.json",encoding="utf-8"))
strip=lambda s: re.sub(r"<[^>]+>","",s)
def p(name,txt):
    t=strip(txt); n=len(t.split("\n"))
    print(f"--- {name}  [{n} реда]"); print(t); print()
mac={"долар":True,"лихви":True,"миньори":True}
brd=[("1час","long",6,"strong","СИЛЕН")]*7
best=("1час","long",6,"strong","СИЛЕН")
lv=lb._levels(4365.20,"long")
adv,ok=lb._advice_entry("long",1,st,None,False,0)
print("присъда day1:",adv,ok)
p("01 сигнал ДА зона B", lb._sig_msg("long",6,7,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-18T09:51",lv,4365.20,adv,mac,1,{"vol_rank":.5},st,1000,2.0,adv_ok=ok,zone=("B","x")))
adv5,ok5=lb._advice_entry("long",5,st,None,False,0)
print("присъда stale:",adv5,ok5)
p("04в сигнал ДА малък (зона A)", lb._sig_msg("long",6,7,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-18T09:51",lv,4365.20,adv5,mac,5,{"vol_rank":.5},st,1000,2.0,adv_ok=ok5,zone=("A","x")))
p("04 сигнал ДА зона A 10000$", lb._sig_msg("long",6,7,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-18T09:51",lv,4365.20,adv,mac,1,{"vol_rank":.5},st,10000,2.0,adv_ok=ok,zone=("A","x")))
advn,okn=lb._advice_entry("short",0,st,None,False,0)
print("присъда short0:",advn,okn)
p("02 БЕЗ ВХОД", lb._sig_msg("short",5,4,"ГОТОВ",{"mid":4365.2},4365.0,"2026-08-18T09:51",lb._levels(4365.2,"short"),4365.2,advn,mac,0,{"vol_rank":.5},st,1000,2.0,adv_ok=okn,shadow_on={"direction":"short","entry":4111.0}))
advw,okw=lb._advice_entry("short",2,st,None,False,0)
print("присъда short2:",advw,okw)
p("04б ИЗЧАКАЙ", lb._sig_msg("short",5,4,"ГОТОВ",{"mid":4365.2},4365.0,"2026-08-18T09:51",lb._levels(4365.2,"short"),4365.2,advw,mac,2,{"vol_rank":.5},st,1000,2.0,adv_ok=okw))
p("05 стоящ 14ч", lb._standing_msg("long",best,14.0,{"mid":4365.2},4365.0,4365.2,brd,mac,{},"2026-08-18T11:20"))
p("05б стоящ 48ч", lb._standing_msg("long",best,48.0,{"mid":4365.2},4365.0,4365.2,brd,mac,{},"2026-08-18T11:20"))
p("07 спряна", lb._спряна_msg("short",best,4365.2,"ре-влизане в пауза","точно след приключена сделка ръбът е изяден — мерено на 19.7 години: късните ре-влизания дават −1.59$/сделка","2026-08-18T11:20",brd))
tr={"direction":"long","entry":4358.0,"opened":"2026-08-11T09:00","levels":{"tp1":4365.5,"tp2":4370.0,"tp3":4378.0,"sl":4338.0},"hit":{},"sym":"XAUUSD"}
p("10 изход ТП1", lb._exit_msg("tp1",tr,4365.5,"2026-08-18T10:00","бар",False))
tr2=dict(tr); tr2["hit"]={"tp1":True,"tp2":True}; tr2["levels"]=dict(tr["levels"]); tr2["levels"]["sl"]=4358.0
p("14 изход БЕ", lb._exit_msg("sl",tr2,4358.0,"2026-08-18T10:00","бар",False))
p("изход ВРЕМЕ", lb._exit_msg("time",tr,4361.0,"2026-08-18T10:00","бар",False))
p("18 MA лонг", lb._ma_alert_msg("long","ema200",4365.2,st.get("ma_bounce",{}).get("long",{}).get("ma50",{}),mac))
mr={"долар":0.015,"лихви":-0.07}
p("20 пулс сутрин", lb._pulse_msg("09",brd,best,"long",adv,ok,None,None,{"mid":4365.2},None,mac,False,False))
p("36 пулс mixed", lb._pulse_msg("09",brd,best,"long",advn,False,None,None,{"mid":4365.2},None,mac,False,False,macro_raw=mr,streaks={"long":0},stats=st))
p("34 обрат подреди", lb._обрат_msg((False,True),(True,True),{"долар":0.015,"лихви":0.07},{"long":1},стат=st))
p("35 обрат разбърка", lb._обрат_msg((True,True),(True,False),mr,{"long":0},стат=st))
p("03 сделката тече", lb._sig_msg("long",6,7,"СИЛЕН",{"mid":4365.2},4365.0,"2026-08-18T09:51",lv,4365.20,adv,mac,1,{"vol_rank":.5},st,1000,2.0,adv_ok=ok,open_trade=tr2))
