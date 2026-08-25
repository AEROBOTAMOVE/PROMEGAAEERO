import sys,json,io,re
sys.argv=["x"]; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import live_bot as lb
st=json.load(open('backtest_stats.json',encoding='utf-8'))
strip=lambda s: re.sub(r"<[^>]+>","",s)
mac={"долар":True,"лихви":True,"миньори":True}
for d in ("long","short"):
    for m in ("ma50","ma200"):
        mb=st["ma_bounce"][d][m]
        print("### %s %s  net=%s lo=%s hi=%s n=%s"%(d,m,mb.get("net"),mb.get("lo"),mb.get("hi"),mb.get("n")))
        print(strip(lb._ma_alert_msg(d,m,4365.20,mb,mac)))
        print("   _пари казва:", lb._пари(float(mb["net"])))
        print()
