import sys, hashlib
sys.path.insert(0,r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
print("md5", hashlib.md5(open(sys.path[0]+"/live_bot.py","rb").read()).hexdigest())
import live_bot as B
print("--- A: sabitie 23:50 Sofia, minavame polunosht ---")
ctx={'date':'2026-08-20','events':[{'time_sofia':'23:50','name':'vazhno','impact':'high'}]}
for iso in ['2026-08-20T20:35','2026-08-20T20:50','2026-08-20T21:05','2026-08-20T21:20','2026-08-20T21:09']:
    print(iso,'Sofia',B._sofia(iso), B._event_shield(ctx,iso))
print("--- B: sabitie 00:10 Sofia, predupreditelen prozorec ---")
ctx2={'date':'2026-08-21','events':[{'time_sofia':'00:10','name':'BOJ','impact':'high'}]}
for iso in ['2026-08-20T20:20','2026-08-20T20:40','2026-08-20T21:00','2026-08-20T21:05','2026-08-20T21:15']:
    print(iso,'Sofia',B._sofia(iso), B._event_shield(ctx2,iso))
