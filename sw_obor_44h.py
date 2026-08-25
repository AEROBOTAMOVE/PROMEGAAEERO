# -*- coding: utf-8 -*-
import json, io, os
P=os.path.dirname(os.path.abspath(__file__))
rows=[json.loads(l) for l in io.open(os.path.join(P,"live","sent_log.jsonl"),encoding="utf-8") if l.strip()]
d=[r for r in rows if r["utc"][:10] in ("2026-08-18","2026-08-19")]
print("=== 18-19.08 · МАКРО-СЪСТОЯНИЕ по пулсовете ===")
for r in d:
    if r["tag"]=="pulse":
        for ln in r["text"].split("\n"):
            if "двете" in ln or "макро" in ln: print(" ",r["utc"],"|",ln)
print()
print("=== 18-19.08 · ПЪРВАТА сигнална карта ===")
s=[r for r in d if r["tag"]=="signal"]
print(s[0]["utc"]); print(s[0]["text"])
