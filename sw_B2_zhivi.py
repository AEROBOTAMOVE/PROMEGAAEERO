# -*- coding: utf-8 -*-
import io, re, sys
p = "brain/b_сливане.py"
src = io.open(p, encoding="utf-8").read()
import brain.b_сливане as SL
T = SL.ТАБЛИЦА
# извън литерала: къде се присвоява у["ключ"] = ...
tail = src.split("ТАВАН_ГРУПА =",1)[1]
живи=[]; мъртви=[]
for k in T:
    if re.search(r'["\']' + re.escape(k) + r'["\']', tail):
        живи.append(k)
    else:
        мъртви.append(k)
print("присвоявани в кода:", len(живи))
print("НИКЪДЕ извън таблицата:", len(мъртви), мъртви)
