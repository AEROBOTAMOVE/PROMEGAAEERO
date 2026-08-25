# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout=io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
st=json.load(open("backtest_stats.json",encoding="utf-8"))
print("tp_hits:",json.dumps(st.get("tp_hits"),ensure_ascii=False)[:1500])
print()
print("tp_hits_доставена:",json.dumps(st.get("tp_hits_доставена"),ensure_ascii=False)[:1500])
print()
print("време_изход_проверено:",json.dumps(st["_meta"].get("време_изход_проверено"),ensure_ascii=False)[:1200])
