# -*- coding: utf-8 -*-
import json
rows=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
rej=[r for r in rows if r.get("spot_rejected")]
sig=[r for r in rej if any(str(s).startswith(("signal","s-signal")) for s in (r.get("status") or []))]
print("отрязани ръна с карта signal/s-signal:", len(sig))
for r in sig:
    g=r.get("gate") or {}
    print(f"  {r['run_utc']} v{r['v']:6} status={[s for s in r['status'] if 'signal' in s]} "
          f"gate.ok={g.get('ok')} by={g.get('by')} trade={r.get('trade')}")
print()
# сверка със sent_log — какъв е ТЕКСТЪТ на изпратената карта
try:
    sent=[json.loads(l) for l in open("live/sent_log.jsonl",encoding="utf-8") if l.strip()]
    print("sent_log ключове:", sorted(sent[-1].keys()))
    stamps={r["run_utc"] for r in sig}
    hit=[s for s in sent if str(s.get("kind","")).startswith(("signal","s-signal"))
         and any(str(s.get("run_utc") or s.get("ts") or "").startswith(t[:16]) for t in stamps)]
    print("намерени карти в sent_log:", len(hit))
    for h in hit[:4]:
        txt=str(h.get("text") or h.get("msg") or "")
        print("  ---", h.get("run_utc") or h.get("ts"), h.get("kind"))
        for line in txt.split("\n")[:6]: print("     ", line)
except Exception as e:
    print("sent_log:", type(e).__name__, e)
