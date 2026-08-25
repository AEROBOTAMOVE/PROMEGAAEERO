# -*- coding: utf-8 -*-
"""ТЕСТ 2 · СУХИЯТ РЪН ГУБИ ЛИ КАРТАТА, ИЛИ САМО Я ОТЛАГА?"""
import sys, json, pathlib, tempfile, shutil
sys.argv = ["x"]
import live_bot as lb

tmp = pathlib.Path(tempfile.mkdtemp(prefix="sw_zz3_"))
st = []
# рън 1 · СУХ (точно `python live_bot.py --out live` без --send)
sent1 = lb._outbox_flush(tmp, [("brain:15м:long", "<b>КАРТА</b>")], st, dry=True)
ob1 = [json.loads(l) for l in (tmp/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
print("рън1 СУХ  · sent_tags =", sent1)
print("рън1 СУХ  · останали в пощата =", [m["tag"] for m in ob1])
print("рън1 статуси:", st)

# рън 2 · ИСТИНСКИ (както Actions: --send). Телеграм отговаря SENT.
lb._send_raw = lambda t: "SENT"
st2 = []
sent2 = lb._outbox_flush(tmp, [], st2, dry=False)   # НИЩО НОВО не се ражда
ob2 = (tmp/"outbox.jsonl").read_text(encoding="utf-8").strip()
print("рън2 ЖИВ  · sent_tags =", sent2)
print("рън2 ЖИВ  · останали в пощата =", repr(ob2))
print("рън2 статуси:", st2)
sl = (tmp/"sent_log.jsonl").read_text(encoding="utf-8").strip()
print("sent_log:", sl[:120])
shutil.rmtree(tmp, ignore_errors=True)
