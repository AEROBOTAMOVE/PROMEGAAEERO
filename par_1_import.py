# -*- coding: utf-8 -*-
import sys, json, io
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import live_bot as lb
print("VERSION", lb.VERSION)
print("PIP", lb.PIP, "SL_PIPS", lb.SL_PIPS, "SL_D", lb.SL_D)
print("TPS", lb.TPS)
print("S_TPS", lb.S_TPS, "S_SL", lb.S_SL)
print("MIN_N", getattr(lb,"MIN_N",None), "NEAR_HIGH_DD20", getattr(lb,"NEAR_HIGH_DD20",None))
print("ZONE_W", lb.ZONE_W)
print("МАЛЪК_РАЗМЕР_W", lb.МАЛЪК_РАЗМЕР_W)
st=json.load(open("backtest_stats.json",encoding="utf-8"))
print("stats top keys:", list(st.keys()))
print("fresh.long keys:", list(st.get("fresh",{}).get("long",{}).keys()))
for k,v in st.get("fresh",{}).get("long",{}).items():
    if isinstance(v,dict): print("  long",k, {kk:v.get(kk) for kk in ("n","win","net","lo","hi")})
for k,v in st.get("fresh",{}).get("short",{}).items():
    if isinstance(v,dict): print("  short",k, {kk:v.get(kk) for kk in ("n","win","net","lo","hi")})
