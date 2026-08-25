# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
rows=[json.loads(l) for l in open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
br=[r for r in rows if str(r.get("tag","")).startswith("brain:")]
нови=[r for r in br if r["utc"]>="2026-08-11T14:16"]
print("карти в НОВИЯ формат:", len(нови))
print("с долен ред 🧪 :", sum(1 for r in нови if r["text"].split("\n")[-1].startswith("🧪")))
print("с ✗ :", sum(1 for r in нови if "✗" in r["text"]))
print("с мерено (n= / 'мерено') :", sum(1 for r in нови if "n=" in r["text"] or "мерено" in r["text"]))
print("с 'НОВО' :", sum(1 for r in нови if "НОВО" in r["text"]))
print("със степен на 1-ва позиция:", sum(1 for r in нови if not r["text"].startswith("👁")))
print("входни карти (👁 ГЛЕДАЙ):", sum(1 for r in нови if r["text"].startswith("👁")))
print("с ред за съотношение (× риска):", sum(1 for r in нови if "× риска" in r["text"] or "× и " in r["text"]))
вх=[r for r in нови if r["text"].startswith("👁")]
print("\nвходни без съотношение:", sum(1 for r in вх if "×" not in r["text"]), "от", len(вх))
for r in вх[:2]:
    print("---", r["utc"]); print(r["text"])
