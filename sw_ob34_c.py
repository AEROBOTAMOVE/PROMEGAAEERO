# -*- coding: utf-8 -*-
import json, io
s=[json.loads(l) for l in io.open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
блок = ["2026-08-11T22:51","2026-08-11T22:56","2026-08-12T07:02","2026-08-12T12:42",
        "2026-08-12T12:47","2026-08-12T12:51","2026-08-12T18:41","2026-08-13T04:26",
        "2026-08-18T04:06","2026-08-18T13:46"]
br=[x for x in s if str(x.get("tag","")).startswith("brain:")]
print("общо brain: карти в sent_log:", len(br))
for t in блок:
    m=[x for x in br if x["utc"][:16]>=t and x["utc"][:16]<=t[:14]+str(int(t[14:16])+3).zfill(2)]
    print(t, "-> ПРАТЕНА в Telegram:", bool(m), [x["tag"] for x in m])
