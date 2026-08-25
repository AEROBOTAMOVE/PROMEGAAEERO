# -*- coding: utf-8 -*-
import sys, json, tempfile, shutil
from pathlib import Path
sys.argv = ["x"]
import live_bot as lb

def run(msgs, new_msgs=(), send=lambda t: "SENT (200)", dry=False):
    d = Path(tempfile.mkdtemp())
    (d/"outbox.jsonl").write_text("\n".join(json.dumps(m, ensure_ascii=False) for m in msgs), encoding="utf-8")
    st = []
    o = lb._send_raw; lb._send_raw = send
    try:
        sent = lb._outbox_flush(d, list(new_msgs), st, dry=dry)
    except SystemExit as e:
        sent = set(); st.append("SystemExit:"+str(e)[:60])
    finally:
        lb._send_raw = o
    rem = [json.loads(l) for l in (d/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    shutil.rmtree(d, ignore_errors=True)
    return sent, rem, st

print("=== A. ТОЧНО репро на одитора (dry) ===")
s,r,st = run([{"tag":"signal","text":"СТАР СИГНАЛ ЗА ВХОД","first_ts":"2020-01-01T00:00:00"}],
             new_msgs=[("status","нов статус")], dry=True)
print("statuses:", st)
print("остават:", [m["tag"] for m in r])

print()
print("=== B. Същото в РЕАЛЕН (не-dry) рън ===")
s,r,st = run([{"tag":"signal","text":"СТАР СИГНАЛ","first_ts":"2020-01-01T00:00:00","attempts":1}],
             new_msgs=[("status","нов статус")])
print("statuses:", st); print("sent:", s); print("остават:", [m["tag"] for m in r])

print()
print("=== C. Останалите ЧЕТИРИ пътеки за изхвърляне — говорят ли? ===")
# C1 повреден ред
d = Path(tempfile.mkdtemp()); (d/"outbox.jsonl").write_text('{"tag":"status"\n', encoding="utf-8")
st=[]; o=lb._send_raw; lb._send_raw=lambda t:"SENT (200)"
lb._outbox_flush(d, [], st); lb._send_raw=o
print("C1 повреден ред :", st); shutil.rmtree(d, ignore_errors=True)
# C2 дедуп
s,r,st = run([{"tag":"status","text":"а","first_ts":"2020-01-01T00:00:00"},
              {"tag":"status","text":"б","first_ts":"2020-01-01T00:00:01"}])
print("C2 дедуп        :", st)
# C3 отровно
s,r,st = run([{"tag":"digest","text":"х","first_ts":"2020-01-01T00:00:00","hard_fails":3}])
print("C3 отровно      :", st)
# C4 таван
big=[{"tag":f"note:{i}","text":"x","first_ts":"2020-01-01T00:00:00"} for i in range(lb.ОПАШКА_ТАВАН+5)]
s,r,st = run(big, send=lambda t:"SEND_FAILED: мрежа")
print("C4 таван        :", [x for x in st if "прел" in x] or "МЪЛЧИ")
# C5 осиротял
s,r,st = run([{"tag":"signal","text":"х","first_ts":"2020-01-01T00:00:00"}])
print("C5 осиротял     :", st or "МЪЛЧИ (нула статуса)")
