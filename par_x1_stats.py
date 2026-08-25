import json,sys
d=json.load(open('backtest_stats.json',encoding='utf-8'))
def walk(o,p=''):
    if isinstance(o,dict):
        if not o: print(p,'{}')
        for k,v in o.items(): walk(v,p+'.'+str(k))
    elif isinstance(o,list):
        print(p,'[list len=%d]'%len(o), str(o)[:120])
    else:
        print(p,'=',o)
walk(d)
