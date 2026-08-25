import json, collections, datetime
p = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live/live_journal.jsonl"
rows=[]
for ln in open(p, encoding="utf-8"):
    ln=ln.strip()
    if ln:
        try: rows.append(json.loads(ln))
        except Exception: pass
print("общо записа:", len(rows), " период:", rows[0]["run_utc"], "→", rows[-1]["run_utc"])
none_ = [r for r in rows if r.get("spot") is None and not r.get("spot_rejected")]
print("spot=None БЕЗ отрязване от санитито:", len(none_))
ч = collections.Counter(r["run_utc"][11:13] for r in none_)
print("по час UTC:", dict(sorted(ч.items())))
# уикенд?
def dow(s):
    return datetime.datetime.strptime(s[:16], "%Y-%m-%dT%H:%M").weekday()
print("по ден от седмицата (0=пн..6=нд):", dict(sorted(collections.Counter(dow(r["run_utc"]) for r in none_).items())))
# най-дълга поредица
best=cur=0; cur_start=None; best_span=None
for r in rows:
    if r.get("spot") is None and not r.get("spot_rejected"):
        cur+=1
        if cur==1: cur_start=r["run_utc"]
        if cur>best: best=cur; best_span=(cur_start, r["run_utc"])
    else:
        cur=0
print("най-дългата поредица сухи (само мълчащ фийд):", best, best_span)
# и поредица от ВСЯКАКВО отсъствие на жива цена (както го брои сухият брояч: spot_g is None)
best2=cur2=0; sp2=None; st2=None
for r in rows:
    if r.get("spot") is None:
        cur2+=1
        if cur2==1: st2=r["run_utc"]
        if cur2>best2: best2=cur2; sp2=(st2, r["run_utc"])
    else: cur2=0
print("най-дългата поредица БЕЗ жива цена (вкл. отрязани):", best2, sp2)
# каденция
import statistics
ts=[datetime.datetime.strptime(r["run_utc"][:16], "%Y-%m-%dT%H:%M") for r in rows]
d=[(b-a).total_seconds()/60 for a,b in zip(ts,ts[1:]) if 0<(b-a).total_seconds()/60<600]
print("медианна пауза между ръна, мин:", statistics.median(d), " брой:", len(d))
