# -*- coding: utf-8 -*-
import json, io
rows=[json.loads(l) for l in io.open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
for r in rows:
    if r["utc"] in ("2026-08-18T15:32:13","2026-08-12T12:42:16","2026-08-18T16:22:00"):
        print("="*70); print(r["utc"], "|", r["tag"]); print(r["text"][:600])
