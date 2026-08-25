import sys,json,io,os,importlib
sys.argv=["x"]; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import live_bot as lb
st=json.load(open('backtest_stats.json',encoding='utf-8'))
print("СРЕБРО_ВХОД=",lb.СРЕБРО_ВХОД," СРЕБРО_СПРЕД env=",os.environ.get("СРЕБРО_СПРЕД"))
notes=[]
st2=json.loads(json.dumps(st))
lb._сребро_разход(st2,notes)
print("бележки:",notes)
for d in ("long","short"):
    for k in ("day1","fresh","stale","mixed","ultra"):
        c=st2["silver"][d].get(k,{})
        print(f"  {d}/{k}: net={c.get('net')} lo={c.get('lo')} hi={c.get('hi')} n={c.get('n')}")
for sn in (0,1,2,5):
    print("сребро streak",sn,"->",lb._advice_entry("long",sn,st2,None,False,0,sym="XAGUSD"))
