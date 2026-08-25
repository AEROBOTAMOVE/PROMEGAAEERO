import sys, os, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, D)
import live_bot as lb
stats = json.load(open(os.path.join(D, "backtest_stats.json"), encoding="utf-8"))
print("stats ключове:", list(stats.keys())[:12])
for sym in ("XAGUSD", "XAUUSD"):
    for stale in (False, True):
        tr = {}
        txt, ok = lb._advice_entry("long", 3, stats, None, False, 0, sym=sym, stale_price=stale, trace=tr)
        print(f"{sym} stale={stale!s:5} -> ok={ok}  «{txt}»  by={tr.get('by')}")
