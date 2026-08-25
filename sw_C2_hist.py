# -*- coding: utf-8 -*-
import subprocess, json, sys
out = subprocess.run(["git","log","--format=%H %ad","--date=short","--","live/outbox.jsonl"],
                     capture_output=True, text=True).stdout.splitlines()
print("комити с outbox.jsonl:", len(out))
maxa = {}
rows=0
for line in out:
    sha, d = line.split()[0], line.split()[1]
    blob = subprocess.run(["git","show",f"{sha}:live/outbox.jsonl"], capture_output=True).stdout.decode("utf-8","replace")
    for ln in blob.splitlines():
        if not ln.strip(): continue
        try: m=json.loads(ln)
        except Exception: continue
        rows+=1
        a=m.get("attempts")
        if a is not None:
            maxa.setdefault(a,0); maxa[a]+=1
print("общо редове в историята:", rows)
print("разпределение на attempts:", dict(sorted(maxa.items())))
