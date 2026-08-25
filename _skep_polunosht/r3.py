import sys, json
D=r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
dates=[]
with open(D+"/live/live_journal.jsonl",encoding="utf-8") as f:
    for ln in f:
        try: r=json.loads(ln)
        except Exception: continue
        u=r.get("run_utc") or r.get("utc")
        if u: dates.append(str(u)[:10])
print("jurnal: zapisi",len(dates),"ot",min(dates),"do",max(dates))
# noshtni runove 21:00-03:00 Sofia = 18:00-00:00 UTC (lyato +3)
noshtni=sum(1 for d in [] )
import collections
h=collections.Counter()
with open(D+"/live/live_journal.jsonl",encoding="utf-8") as f:
    for ln in f:
        try: r=json.loads(ln)
        except Exception: continue
        u=r.get("run_utc") or r.get("utc")
        if u and len(str(u))>=13: h[str(u)[11:13]]+=1
print("runove po UTC chas:",dict(sorted(h.items())))
# sent_log: ima li nyakoga etiket ot _event_shield?
n=0; hit=0; hit2=0
with open(D+"/live/sent_log.jsonl",encoding="utf-8") as f:
    for ln in f:
        n+=1
        if "⚠ ЩИТ" in ln: hit+=1
        if "предстои" in ln: hit2+=1
print(f"sent_log redove: {n} | s '⚠ ЩИТ': {hit} | s 'предстои': {hit2}")
