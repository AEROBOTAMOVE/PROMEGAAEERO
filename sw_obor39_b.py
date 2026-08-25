# -*- coding: utf-8 -*-
import sys, json
sys.argv=["x"]
import live_bot as lb
print("VERSION:", lb.VERSION)
print("== 1) ГЕЙТЪТ ПРИ ОТРЯЗАН СПОТ (реален път: stale_price=(spot_g is None)) ==")
stats=json.loads(open("backtest_stats.json",encoding="utf-8").read())
for d in ("long","short"):
    for sp in (False, True):
        tr={}
        txt,ok=lb._advice_entry(d, 0, stats, None, False, 0, sym="XAUUSD", stale_price=sp, dd20=None, trace=tr)
        print(f"  {d:5} stale_price={sp!s:5} -> ok={ok}  |  {txt}")
print()
print("== 2) РЕПРОДУКЦИЯТА НА ОДИТОРА срещу РЕАЛНИТЕ аргументи ==")
sp={"bid":4011.5,"ask":4012.5,"mid":4012.0}
for base,lbl in ((6.0,"base=6.0 (одиторът; ботът НИКОГА не подава това)"),
                 (8.0,"base=8.0 (реалният аргумент за злато, ред 2956)")):
    t={}
    r=lb._spot_sane(sp, 4000.0, base, bar_rng=1.2, spot_jump=12.0, следа=t)
    print(f"  {lbl}: изход={'ЗАПАЗЕН' if r else 'ИЗХВЪРЛЕН'} следа={t}")
print()
print("== 3) КОЛКО ДОБАВЯ jump-клонът НАИСТИНА (сканиране по bar_rng, base=8.0) ==")
print("  bar_rng | tol без скок | tol със скок=30 | печели ли скокът")
for br in (0.5,1.2,2.0,3.2,4.44,6.0,8.0,12.0,20.0):
    a={}; b={}
    lb._spot_sane(sp, 4000.0, 8.0, bar_rng=br, spot_jump=None, следа=a)
    lb._spot_sane(sp, 4000.0, 8.0, bar_rng=br, spot_jump=30.0, следа=b)
    print(f"  {br:7.2f} | {a['допуск']:11.2f} | {b['допуск']:14.2f} | {'ДА' if b['допуск']>a['допуск'] else 'не'}")
