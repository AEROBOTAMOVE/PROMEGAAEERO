# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
d=json.load(open("СТАР_СПИСЪК_48.json",encoding="utf-8"))
for x in d:
    s=json.dumps(x,ensure_ascii=False)
    if "карта" in s or "СТРОЕЖ" in s or "b_карта" in s:
        print(x.get("n"), "|", x.get("file"), "|", x.get("severity"), "|", x.get("title"))
