import sys, json, collections
sys.stdout.reconfigure(encoding='utf-8')
rows=[json.loads(l) for l in open('live/live_journal.jsonl',encoding='utf-8') if l.strip()]
rows.sort(key=lambda r: r.get("run_utc",""))
for w in ("повторно предлагане","стоящ сетъп"):
    print("===",w)
    for r in rows:
        for n in (r.get("notes") or []):
            if n.startswith(w): print("  ",r["run_utc"], r.get("v"), n)
