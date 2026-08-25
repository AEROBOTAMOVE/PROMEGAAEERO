# -*- coding: utf-8 -*-
"""НАЙ-СИЛНОТО: реконструкция от ЖИВИЯ дневник, не от измислен вход.
За всеки жив рън с ОТВОРЕНА сделка ползвам ЗАПИСАНИТЕ macro_raw/trade/spot."""
import sys, json, collections
sys.argv=["x"]; sys.stdout.reconfigure(encoding="utf-8")
import live_bot as lb, стил
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
бд=[(l,"long",5,"medium","СРЕДЕН") for l in ("1мин","5м","15м","30м","1час","4час","1ден")]
бр=collections.Counter(); с_сделка=0; общо=0; примери=[]
for ln in open("live/live_journal.jsonl",encoding="utf-8"):
    try: d=json.loads(ln)
    except: continue
    общо+=1
    tr=d.get("trade")
    if not isinstance(tr,dict) or not tr: continue
    мр=d.get("macro_raw")
    if not isinstance(мр,dict): continue
    с_сделка+=1
    sp=d.get("spot")
    spot_g={"mid":float(sp)} if isinstance(sp,(int,float)) else None
    txt=lb._pulse_msg("09",бд,бд[-1],"long","x",False,tr,None,spot_g,None,
        {"миньори":True,"долар":True,"лихви":False},False,False,
        macro_raw=мр,streaks={"long":1},stats=stats)
    n=len([r for r in стил.чист(txt).split("\n") if r.strip()])
    бр[n]+=1
    if n>стил.МАКС_РЕДОВЕ and len(примери)<1:
        примери.append((d.get("run_utc"),стил.чист(txt)))
print(f"ръна в живия дневник: {общо}")
print(f"ръна с ОТВОРЕНА сделка И записано macro_raw: {с_сделка}")
над=sum(v for k,v in бр.items() if k>стил.МАКС_РЕДОВЕ)
print(f"разпределение на редовете: {dict(sorted(бр.items()))}")
print(f"НАД тавана 7: {над}/{с_сделка} = {100*над/max(с_сделка,1):.1f}%")
for u,t in примери:
    print(f"\nпример (жив рън {u}):")
    for i,l in enumerate(t.split("\n"),1): print(f"  {i:2d} {l}")
