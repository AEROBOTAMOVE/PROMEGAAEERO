import sys,json,io,os
os.environ["СРЕБРО_СПРЕД"]="0.00"; os.environ["СРЕБРО_ВХОД"]="1"
sys.argv=["x"]; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import live_bot as lb
st=json.load(open('backtest_stats.json',encoding='utf-8'))
lb._сребро_разход(st,[])
for sn in (1,2,5,0):
    print("сребро long streak",sn,"->",lb._advice_entry("long",sn,st,None,False,0,sym="XAGUSD"))
