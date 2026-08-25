# -*- coding: utf-8 -*-
import sys, json, io, pathlib, tempfile
sys.argv=["x"]; import live_bot as lb
sys.stdout.reconfigure(encoding='utf-8')
d = pathlib.Path(tempfile.mkdtemp())
# 300 обикновени карти + 2 изходни в пощата
msgs=[]
for i in range(300):
    msgs.append({"tag":f"info{i}","text":f"t{i}","first_ts":"2026-08-19T00:00:00","attempts":0})
msgs.insert(5,{"tag":"brain-exit:стоп","text":"🛑 СТОПЪТ удари","first_ts":"2026-08-19T00:00:00","attempts":0})
msgs.insert(9,{"tag":"exit:sl","text":"🛑 exit","first_ts":"2026-08-19T00:00:00","attempts":0})
(d/"outbox.jsonl").write_text("\n".join(json.dumps(m,ensure_ascii=False) for m in msgs),encoding="utf-8")
lb._send_raw = lambda t: "SOFT_FAIL: тест"   # всички остават
st=[]
lb._outbox_flush(d, [], st, dry=False)
rem=[json.loads(l) for l in (d/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
print("ОПАШКА_ТАВАН =", lb.ОПАШКА_ТАВАН)
print("влезли:", len(msgs), "останали:", len(rem))
print("изходни останали:", [m["tag"] for m in rem if m["tag"].split(":")[0] in lb.EXIT_TAGS])
print("EXIT_TAGS =", lb.EXIT_TAGS)
print([s for s in st if "опашка" in s or "преля" in s])
