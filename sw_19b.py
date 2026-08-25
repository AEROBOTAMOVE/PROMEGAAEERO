import sys, json, tempfile, pathlib
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=["x"]
import live_bot as lb
d = pathlib.Path(tempfile.mkdtemp(prefix="sw19b_"))
(d/"outbox.jsonl").write_text("\n".join([
 json.dumps({"tag":"status","text":"стар статус","first_ts":"2020-01-01T00:00:00","attempts":1},ensure_ascii=False),
 json.dumps({"tag":"signal","text":"стар сигнал","first_ts":"2020-01-01T00:00:00","attempts":1},ensure_ascii=False),
])+"\n", encoding="utf-8")
statuses=[]
lb._outbox_flush(d, [("status","нов статус"),("signal","нов сигнал")], statuses, dry=True)
print("ДЕДУП STATUSES:", statuses)
