# -*- coding: utf-8 -*-
import sys, json, pathlib, tempfile
sys.argv=["x"]; import live_bot as lb
sys.stdout.reconfigure(encoding='utf-8')
out=pathlib.Path(tempfile.mkdtemp())
CB=lb.CB
_s={"_чака_запис":("15м|long",{"ранг":5,"точки":20,"време":"2026-08-19T10:00"})}
_b={}; CB.запиши_застудяване(_s,_b)
(out/"brain_state.json").write_text(json.dumps(_b,ensure_ascii=False),encoding="utf-8")
lb._send_raw=lambda t:"HARD_FAIL: 400 развален HTML"
msg=[("brain:15м:long","🧠 <b>карта")]
st=[]
for рън in range(1,5):
    s=lb._outbox_flush(out,msg if рън==1 else [],st,dry=False)
    rem=[json.loads(l) for l in (out/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"рън {рън}: в пощата={len(rem)} пратени={s} · {st[-1]}")
print("часовникът:",(out/"brain_state.json").read_text(encoding="utf-8"))
