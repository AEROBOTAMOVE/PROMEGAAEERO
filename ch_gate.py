import sys, json, io
sys.argv=["x"]; sys.stdout=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import live_bot as lb
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
for d,sn in (("long",1),("long",0),("short",0),("long",5)):
    t={}
    txt,ok=lb._advice_entry(d,sn,stats,None,False,0,trace=t)
    print(d,sn,"->",ok,"|",txt)
    print("   trace:",json.dumps(t,ensure_ascii=False))
