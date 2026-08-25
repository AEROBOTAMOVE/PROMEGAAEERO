import sys,json,io,os
os.environ["СРЕБРО_СПРЕД"]="0.00"
sys.argv=["x"]; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import live_bot as lb
st=json.load(open('backtest_stats.json',encoding='utf-8'))
notes=[]
lb._сребро_разход(st,notes)
print("бележки:",notes)
for d in ("long",):
    for k in ("day1","fresh","stale","mixed","ultra"):
        c=st["silver"][d].get(k,{})
        print(f"  {d}/{k}: net={c.get('net')} lo={c.get('lo')} hi={c.get('hi')} шум={lb._noise(c)}")
print("СРЕБРО_ВХОД=",lb.СРЕБРО_ВХОД)
for sn in (1,2,5,0):
    print("сребро long streak",sn,"->",lb._advice_entry("long",sn,st,None,False,0,sym="XAGUSD"))
