import json, io, sys
sys.stdout.reconfigure(encoding="utf-8")
j=[json.loads(l) for l in io.open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
otv=[x for x in j if x.get("trade")]
print("ръна общо:", len(j), "· с отворена сделка:", len(otv))
# в кои часове (UTC) е пулсът: 06,11,19
puls=[x for x in otv if x["run_utc"][11:13] in ("06","11","19")]
print("от тях в пулс-час (06/11/19 UTC):", len(puls))
for x in puls[:10]: print("   ", x["run_utc"], str(x["trade"])[:80])
