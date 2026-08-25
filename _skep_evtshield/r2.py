import sys, os, json, datetime
sys.path.insert(0,os.getcwd())
import live_bot as B
print("cwd:",os.getcwd())
print("daily_context.json съществува в корена?", os.path.exists("daily_context.json"))
print("в live/?", os.path.exists("live/daily_context.json"))
n=[]
print("_daily_ctx с реалния default път ->", B._daily_ctx("daily_context.json","2026-08-21",n), "| бележки:",n)

# трета посока: вчерашен контекст, приет по датата на БАРА
p="_skep_evtshield/dc.json"
json.dump({"date":"2026-08-20","events":[{"time_sofia":"23:50","name":"важно","impact":"high"}]},open(p,"w",encoding="utf-8"))
n2=[]
ctx=B._daily_ctx(p,"2026-08-20",n2)      # барът е вчерашен
print("_daily_ctx(вчерашен файл, бар=2026-08-20) ->", ctx, "| бележки:",n2)
if ctx:
    for iso in ['2026-08-21T20:35','2026-08-21T20:50','2026-08-21T21:05']:
        print("   ", iso, "София", B._sofia(iso), B._event_shield(ctx,iso))
