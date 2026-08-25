# -*- coding: utf-8 -*-
import sys, json, pathlib, tempfile
sys.argv=["x"]; import live_bot as lb
sys.stdout.reconfigure(encoding='utf-8')
print("POISON_HARD_FAILS =", lb.POISON_HARD_FAILS)
for tag in ("brain-exit:стоп","exit:sl","brain:15м:long"):
    d = pathlib.Path(tempfile.mkdtemp())
    m={"tag":tag,"text":"<b>🛑 СТОПЪТ удари</b>","first_ts":"2026-08-19T00:00:00",
       "attempts":9,"hard_fails":5}
    (d/"outbox.jsonl").write_text(json.dumps(m,ensure_ascii=False),encoding="utf-8")
    lb._send_raw = lambda t: "HARD_FAIL: 400"
    st=[]
    lb._outbox_flush(d,[],st,dry=False)
    rem=[json.loads(l) for l in (d/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"{tag:20} → остава={len(rem)}  ", [s for s in st][:2],
          ("plain=" + str(rem[0].get("plain")) if rem else ""))
