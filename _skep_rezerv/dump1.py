import json, collections
p = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live/live_journal.jsonl"
lines=[l for l in open(p, encoding="utf-8") if l.strip()]
r=json.loads(lines[-1])
print("ВСИЧКИ ключове:", list(r.keys()))
for k in ("macro","macro_raw","notes","бележки","status"):
    if k in r: print(k, "=", json.dumps(r[k], ensure_ascii=False)[:400])
# колко пъти макро-крачето е било мъртво според журнала
c=collections.Counter(); prim=[]
for l in lines:
    rr=json.loads(l)
    m=rr.get("macro") or {}
    mr=rr.get("macro_raw") or {}
    dead = (mr.get("мъртви") if isinstance(mr,dict) else None) or (m.get("мъртви") if isinstance(m,dict) else None)
    c[bool(dead)]+=1
    if dead and len(prim)<5: prim.append((rr.get("run_utc"), dead))
print("мъртво макро в журнала:", dict(c), prim)
# първите ръна след двата уикенда
for target in ("2026-08-09T22:01","2026-08-16T22:02"):
    for l in lines:
        rr=json.loads(l)
        if rr.get("run_utc")==target:
            print(target, "->", json.dumps({k:rr[k] for k in ("macro","macro_raw") if k in rr}, ensure_ascii=False)[:300])
            break
