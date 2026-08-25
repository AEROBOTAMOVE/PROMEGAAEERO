import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=["x"]; import live_bot as lb
print("NEAR_HIGH_DD20 =", lb.NEAR_HIGH_DD20, "| MIN_N =", lb.MIN_N)
st=json.load(open('backtest_stats.json',encoding='utf-8'))
nh=st.get("fresh",{}).get("short",{}).get("near_high")
print("near_high от ЖИВИЯ backtest_stats.json:", nh)

trace={}
txt, ok = lb._advice_entry("short", 2, st, False, False, 0, sym="XAUUSD",
                           stale_price=False, dd20=0.001, trace=trace)
print("\nПРИСЪДА:", (txt, ok))
print("trace:", trace)
print("cell, който дневникът ще запише: _cell_name(2) =", lb._cell_name(2))
print("by =", trace.get("by"))
print("\n→ РЕДЪТ, който би влязъл в live_journal.jsonl:")
print(json.dumps({"dir":"short","streak":2,"cell":lb._cell_name(2),"ok":ok,
                  "by":trace.get("by"),"мерено":trace.get("мерено"),"why":txt},
                 ensure_ascii=False))
