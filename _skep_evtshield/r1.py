import sys, hashlib
sys.path.insert(0,r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
print("md5 live_bot.py:", hashlib.md5(open(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live_bot.py","rb").read()).hexdigest())
import live_bot as B
print("--- ПОСОКА 1: събитие 23:50 София, ±20 мин прозорец ---")
ctx={'date':'2026-08-20','events':[{'time_sofia':'23:50','name':'важно','impact':'high'}]}
for iso in ['2026-08-20T20:35','2026-08-20T20:50','2026-08-20T21:05','2026-08-20T21:20']:
    print(iso,'София',B._sofia(iso), B._event_shield(ctx,iso))
print("--- ПОСОКА 2: събитие 00:10 София, прозорец -60..-20 ---")
ctx2={'date':'2026-08-21','events':[{'time_sofia':'00:10','name':'BOJ','impact':'high'}]}
for iso in ['2026-08-20T20:20','2026-08-20T20:40','2026-08-20T21:00','2026-08-20T21:05','2026-08-20T21:15']:
    print(iso,'София',B._sofia(iso), B._event_shield(ctx2,iso))
