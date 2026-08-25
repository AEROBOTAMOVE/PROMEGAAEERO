import json, collections, pathlib
p = pathlib.Path(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live/live_journal.jsonl")
print("файл:", p, "| съществува:", p.exists(), "| байта:", p.stat().st_size if p.exists() else 0)
recs=[]
for ln in p.read_text(encoding="utf-8", errors="replace").splitlines():
    ln=ln.strip()
    if not ln: continue
    try: recs.append(json.loads(ln))
    except Exception: pass
print("общо записа:", len(recs))
keys=collections.Counter()
for r in recs: keys.update(r.keys())
print("\nнай-чести ключове:", keys.most_common(25))
# има ли изобщо санити-следа?
sled=[r for r in recs if any("сан" in str(k) or "допуск" in str(k) for k in r)]
print("\nзаписи с нещо 'сан/допуск' на ВЪРХОВНО ниво:", len(sled))
rej=[r for r in recs if r.get("spot_rejected") or r.get("spot_rejected_g")]
print("spot_rejected на върховно ниво:", len(rej))
