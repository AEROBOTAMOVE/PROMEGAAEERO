# -*- coding: utf-8 -*-
import sys, re, json
sys.argv=["x"]; import live_bot as lb, стил
sys.stdout.reconfigure(encoding='utf-8')
_re=re.compile(r"<[^>]+>")
бд=[(l,"long",5,"medium","СРЕДЕН") for l in ("1мин","5м","15м","30м","1час","4час","1ден")]
мр={"долар":0.0145,"лихви":-0.07}; ст={"long":0}
tr={"entry":3300.0,"dir":"long","sl":3280.0,"tp1":3320.0,"tp2":3340.0,"tp3":3360.0,
    "hit":{"tp1":True},"lot":1.0,"lots":1.0}
sr={"entry":37.5,"dir":"long","sl":37.0,"tp1":38.0,"tp2":38.5,"tp3":39.0,
    "hit":{},"lot":1.0,"lots":1.0}
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
def пусни(етикет, trade, s_trade, stats=None):
    t=_re.sub("",lb._pulse_msg("09",бд,бд[-1],"long","x",False,trade,s_trade,
        {"mid":4370.12},{"mid":64.821},
        {"миньори":True,"долар":True,"лихви":False},False,False,
        macro_raw=мр,streaks=ст,stats=stats))
    n=len(t.split("\n"))
    print(f"{етикет}: {n} реда  {'✅' if n<=стил.МАКС_РЕДОВЕ else '🔴 НАД ТАВАНА 7'}")
    if n>стил.МАКС_РЕДОВЕ:
        for i,l in enumerate(t.split("\n"),1): print(f"    {i:2d} {l}")
пусни("както го тества selftest (trade=None, stats=None)", None, None, None)
пусни("същото + ОТВОРЕНА златна сделка          ", tr, None, None)
пусни("същото + злато И сребро                  ", tr, sr, None)
пусни("злато+сребро + истинската статистика      ", tr, sr, stats)
