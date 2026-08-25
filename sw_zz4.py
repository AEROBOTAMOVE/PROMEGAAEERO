# -*- coding: utf-8 -*-
"""ТЕСТ 3 · КАКВО БИ СТАНАЛО, АКО ЧАСОВНИКЪТ СЕ НАВИВАШЕ ЕДВА СЛЕД ДОСТАВКА.
Мозъчните тагове НЕ са в DEDUP → втори екземпляр НЕ се маха."""
import sys, json, pathlib, tempfile, shutil
sys.argv = ["x"]
import live_bot as lb
print("DEDUP списък в кода:", [t for t in ("signal","s-signal","digest","status","pulse","cq-ref","standing")])
import inspect
src = inspect.getsource(lb._outbox_flush)
print("съдържа ли 'brain' в DEDUP реда:", [l.strip() for l in src.splitlines() if 'DEDUP = ' in l])

tmp = pathlib.Path(tempfile.mkdtemp(prefix="sw_zz4_"))
st=[]
lb._outbox_flush(tmp, [("brain:15м:long","КАРТА-А")], st, dry=True)   # рън 1: остава в пощата
lb._send_raw = lambda t: "SENT"
st2=[]
# рън 2: същият бар → мозъкът РАЖДА СЪЩИЯ сетъп пак (часовникът не е навит при «фикса»)
sent = lb._outbox_flush(tmp, [("brain:15м:long","КАРТА-А")], st2, dry=False)
sl = [json.loads(l) for l in (tmp/"sent_log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
print("доставени копия на СЪЩАТА карта:", len(sl), [s["text"] for s in sl])
print("статуси:", st2)
shutil.rmtree(tmp, ignore_errors=True)
