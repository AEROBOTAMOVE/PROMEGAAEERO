# -*- coding: utf-8 -*-
"""№44 · ЖИВИТЕ стоящи карти: обвиняват ли свежестта, докато макрото е разбъркано?"""
import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
sent=[json.loads(l) for l in open('live/sent_log.jsonl',encoding='utf-8') if l.strip()]
ст=[s for s in sent if s.get("tag")=="standing"]
print("живи СТОЯЩИ карти в sent_log:", len(ст))
for s in ст:
    p=re.sub(r"<[^>]+>","",s["text"])
    print("---", s["utc"])
    print(p)
    print("   съдържа «не са единодушни»:", "не са единодушни" in p,
          "| съдържа «не е пресен»:", "не е пресен" in p)
