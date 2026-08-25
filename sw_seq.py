# -*- coding: utf-8 -*-
"""Двурънова симулация на ЕДИНСТВЕНИЯ реален път до тихия отрез."""
import sys, json, tempfile, shutil
from pathlib import Path
sys.argv=["x"]; import live_bot as lb

d=Path(tempfile.mkdtemp()); (d/"outbox.jsonl").write_text("", encoding="utf-8")
o=lb._send_raw

# РЪН N: сигналът се генерира, Телеграм дава 400
st1=[]
lb._send_raw=lambda t:"HARD_FAIL:400 Bad Request"
lb._outbox_flush(d,[("signal","🟢 ВХОД ДЪЛЪГ 4100")],st1)
print("РЪН N statuses:", st1)
print("РЪН N поща:", [json.loads(l)["tag"] for l in (d/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()])

# РЪН N+1а: сетъпът СТОИ → should_sig пак True → карта се регенерира
d2=Path(tempfile.mkdtemp()); shutil.copy(d/"outbox.jsonl", d2/"outbox.jsonl")
st2=[]; lb._send_raw=lambda t:"SENT (200)"
lb._outbox_flush(d2,[("signal","🟢 ВХОД ДЪЛЪГ 4102")],st2)
print("\nРЪН N+1а (сетъпът стои):", st2)

# РЪН N+1б: щит пали → should_sig=False → тих отрез
d3=Path(tempfile.mkdtemp()); shutil.copy(d/"outbox.jsonl", d3/"outbox.jsonl")
st3=[]
lb._outbox_flush(d3,[("status","борсата диша")],st3)
print("РЪН N+1б (щит пали) :", st3)
print("   старата ВХОДНА карта:", "ИЗЧЕЗНА БЕЗ ДУМА" if not any("signal" in s for s in st3) else "спомената")

# РЪН N+1в: същото, но с ИЗХОДНА карта — пази ли се?
d4=Path(tempfile.mkdtemp())
(d4/"outbox.jsonl").write_text(json.dumps({"tag":"exit:sl","text":"🛑 СТОПЪТ удари","first_ts":"2020-01-01T00:00:00"}), encoding="utf-8")
st4=[]; lb._send_raw=lambda t:"SEND_FAILED: мрежа"
lb._outbox_flush(d4,[("status","x")],st4)
print("\nРЪН N+1в ИЗХОДНА карта:", st4, "→ остава:",
      [json.loads(l)["tag"] for l in (d4/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()])
lb._send_raw=o
for x in (d,d2,d3,d4): shutil.rmtree(x, ignore_errors=True)
