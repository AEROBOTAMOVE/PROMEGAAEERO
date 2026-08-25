# -*- coding: utf-8 -*-
import sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
D=r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
n=0;hit=0;hit2=0
for ln in io.open(D+"/live/sent_log.jsonl",encoding="utf-8"):
    n+=1
    if "\u26a0 \u0429\u0418\u0422" in ln: hit+=1
    if "\u043f\u0440\u0435\u0434\u0441\u0442\u043e\u0438 " in ln: hit2+=1
print("sent_log redove:",n,"| s ZHIT etiket:",hit,"| s 'predstoi':",hit2)
