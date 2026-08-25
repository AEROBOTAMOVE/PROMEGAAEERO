# -*- coding: utf-8 -*-
import sys, pathlib, tempfile, os
sys.argv=["x"]
import live_bot as lb
d=pathlib.Path(tempfile.mkdtemp(prefix="ordtest_"))
order=[]
def fake(text):
    order.append(text.splitlines()[0][:40]); return "SENT"
lb._send_raw=fake
st=[]
msgs=[("signal","⏸ БЕЗ ВХОД · ЗЛАТО нагоре"),
      ("brain-exit:стоп","🛑 СТОПЪТ удари · наблюдението от 18:11")]
tags=lb._outbox_flush(d, msgs, st, dry=False)
print("ред на ИЗПРАЩАНЕ:")
for i,t in enumerate(order): print("  ",i,t)
print("статуси:",st)
import io,json
sl=[json.loads(l)["tag"] for l in io.open(d/"sent_log.jsonl",encoding="utf-8")]
print("sent_log ред:",sl)
print("ПРЕНАРЕЖДАНЕ В FLUSH:", "НЯМА" if sl==["signal","brain-exit:стоп"] else "ИМА")
