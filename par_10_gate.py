# -*- coding: utf-8 -*-
import sys, io, json
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import live_bot as lb
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
print("ПЪЛНА ТАБЛИЦА НА ГЕЙТА (злато) · MIN_N=%s"%lb.MIN_N)
print("%-6s %-7s %-8s %-9s %s"%("посока","стрийк","_cell_name","trace-кофа","присъда"))
for d in ("long","short"):
    for s in (0,1,2,3,4,7,20):
        tr={}
        txt,ok = lb._advice_entry(d,s,stats,None,False,0,sym="XAUUSD",stale_price=False,dd20=0.05,trace=tr)
        м = tr.get("мерено") or {}
        print("%-6s %-7s %-8s %-9s %s | %s"%(d,s,lb._cell_name(s),м.get("кофа"),"ДА " if ok else "НЕ ",txt))
print()
print("=== ЗНАК: съответства ли текстът на макро-състоянието? ===")
# _streaks: m_l = долар пада И лихви падат -> long streak
# карта за long трябва да казва 'падат'; за short 'растат'
for d in ("long","short"):
    txt,ok = lb._advice_entry(d,1,stats,None,False,0,sym="XAUUSD",stale_price=False,dd20=0.05)
    очаква = "падат" if d=="long" else "растат"
    print("  %s: '%s'  -> съдържа '%s'? %s"%(d,txt,очаква,очаква in txt))
print()
print("=== near_high клон (злато-шорт, стрийк 2-3, dd20 < %.3f) ==="%lb.NEAR_HIGH_DD20)
for dd in (0.001, 0.010, 0.020):
    for s in (2,3):
        tr={}
        txt,ok=lb._advice_entry("short",s,stats,None,False,0,sym="XAUUSD",stale_price=False,dd20=dd,trace=tr)
        print("  dd20=%.3f стрийк=%s -> %s | кофа=%s"%(dd,s,txt,(tr.get('мерено') or {}).get('кофа')))
print()
print("=== СРЕБРО (СРЕБРО_ВХОД=%s) ==="%lb.СРЕБРО_ВХОД)
for d in ("long","short"):
    for s in (0,1,2,5):
        txt,ok=lb._advice_entry(d,s,stats,None,False,0,sym="XAGUSD",stale_price=False)
        print("  %-6s %s -> %s | %s"%(d,s,"ДА" if ok else "НЕ",txt))
