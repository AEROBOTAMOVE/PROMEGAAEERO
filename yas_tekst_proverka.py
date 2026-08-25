import sys, json, re
sys.argv=["x"]
import live_bot as lb
st=json.load(open("backtest_stats.json",encoding="utf-8"))
print("ZONE_W", lb.ZONE_W, "МАЛЪК", lb.МАЛЪК_РАЗМЕР_W, "СТОЯЩ_МАКС_Ч", lb.СТОЯЩ_МАКС_Ч)
for k in ("day1","fresh","stale","mixed"):
    for d in ("long","short"):
        s=st.get("fresh",{}).get(d,{}).get(k) or {}
        if s: print("fresh/%s/%s"%(d,k), {x:s.get(x) for x in ("n","win","net","lo","hi")})
# речник емоджи
src=open("selftest.py",encoding="utf-8").read()
m=re.search(r'_РЕЧНИК25 = set\("([^"]+)"\)',src)
print("РЕЧНИК:",m.group(1))
print("⏳ in речник:", "⏳" in m.group(1), "| 📅:", "📅" in m.group(1), "| ⛔:", "⛔" in m.group(1), "| 🚫:", "🚫" in m.group(1))
