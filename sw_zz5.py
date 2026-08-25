# -*- coding: utf-8 -*-
"""ТЕСТ 4 · ОТРОВНИЯТ ПЪТ: 3 твърди 400 → мозъчната карта се хвърля.
Колко пъти се е случвало в ЖИВИЯ бот и какъв е обхватът?"""
import sys, json, pathlib, tempfile, shutil
sys.argv = ["x"]
import live_bot as lb
tmp = pathlib.Path(tempfile.mkdtemp(prefix="sw_zz5_"))
lb._send_raw = lambda t: "HARD_FAIL:400 Bad Request: can't parse entities"
for i in range(4):
    st=[]
    new = [("brain:15м:long","<b>КАРТА")] if i==0 else []
    lb._outbox_flush(tmp, new, st, dry=False)
    print(f"рън{i+1}:", st)
print("поща накрая:", repr((tmp/"outbox.jsonl").read_text(encoding='utf-8')))
# СЪЩОТО, но за ИЗХОДНА карта
tmp2 = pathlib.Path(tempfile.mkdtemp(prefix="sw_zz5b_"))
for i in range(5):
    st=[]
    new = [("brain-exit:sl","<b>СТОПЪТ удари")] if i==0 else []
    lb._outbox_flush(tmp2, new, st, dry=False)
    print(f"изход рън{i+1}:", st)
shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(tmp2, ignore_errors=True)
