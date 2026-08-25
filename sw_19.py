import sys, json, tempfile, pathlib
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=["x"]
import live_bot as lb

d = pathlib.Path(tempfile.mkdtemp(prefix="sw19_"))
# стар осиротял сигнал в пощата (от минал рън)
old = {"tag":"signal","text":"СТАР СИГНАЛ ЗА ВХОД","first_ts":"2020-01-01T00:00:00","attempts":1}
(d/"outbox.jsonl").write_text(json.dumps(old, ensure_ascii=False)+"\n", encoding="utf-8")

statuses=[]
sent = lb._outbox_flush(d, [("status","нещо ново")], statuses, dry=True)
print("STATUSES:", statuses)
print("останали в пощата:", [json.loads(l)["tag"] for l in (d/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()])
print("--- има ли дума за изхвърления сигнал? ---")
print(any("signal" in s and ("хвърл" in s or "махн" in s or "изхвърл" in s) for s in statuses))
