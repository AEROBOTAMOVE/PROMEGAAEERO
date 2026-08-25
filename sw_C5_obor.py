# -*- coding: utf-8 -*-
"""Адверсарна проверка на находка 10."""
import sys, json, tempfile, ast
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.argv = ["x"]
import live_bot as lb

d = Path(tempfile.mkdtemp())
lb._send_raw = lambda text: "SOFT_FAIL: мрежа"
st = []      # ← ТОЧНО списъкът, който main() слага в live_journal.jsonl["status"]
for i in range(3):
    lb._outbox_flush(d, [("exit:sl", "🛑 СТОПЪТ удари")] if i == 0 else [], st)
кола = [json.loads(l) for l in (d/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
print("A · след 3 провала, attempts в опашката:", [m.get("attempts") for m in кола])
print("B · statuses (отиват в live_journal['status']) —", len(st), "реда:")
for s in st: print("     ", s)

lb._send_raw = lambda text: "SENT (200)"
lb._outbox_flush(d, [], st)
print("C · след успеха statuses стана", len(st), "реда; последният:", st[-1])
print("D · реконструиран брой опити от statuses за 'exit:sl' =",
      sum(1 for s in st if s.startswith("exit:sl=")))

# E · ИНЕРТЕН ЛИ Е attempts? подавам абсурдна стойност и гледам дали нещо се променя
for стойност in (0, 999):
    d2 = Path(tempfile.mkdtemp())
    (d2/"outbox.jsonl").write_text(json.dumps(
        {"tag":"signal","text":"карта","first_ts":"2000-01-01T00:00:00",
         "attempts":стойност,"hard_fails":0}, ensure_ascii=False), encoding="utf-8")
    st2=[]
    lb._send_raw = lambda text: "SOFT_FAIL: мрежа"
    lb._outbox_flush(d2, [("signal","карта")], st2)
    ост=[json.loads(l) for l in (d2/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"E · attempts={стойност} → statuses={st2} · остават {len(ост)} карти, "
          f"нов attempts={[m['attempts'] for m in ост]}")

# F · тест: attempts участва ли в решението «отровно»?
d3 = Path(tempfile.mkdtemp())
(d3/"outbox.jsonl").write_text(json.dumps(
    {"tag":"digest","text":"x","first_ts":"2000-01-01T00:00:00",
     "attempts":10**6,"hard_fails":0}, ensure_ascii=False), encoding="utf-8")
st3=[]; lb._send_raw = lambda t: "SOFT_FAIL"
lb._outbox_flush(d3, [], st3)
print("F · attempts=1000000, hard_fails=0 →", st3,
      "· остава в опашката:", bool((d3/"outbox.jsonl").read_text(encoding="utf-8").strip()))
