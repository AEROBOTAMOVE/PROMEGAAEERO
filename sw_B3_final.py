# -*- coding: utf-8 -*-
import sys, io, re, collections
sys.argv=["x"]
import live_bot as lb
print("CHART_BRAIN_ON =", lb.CHART_BRAIN_ON, "| CB зареден:", lb.CB is not None)
T = lb.CB.ТАБЛИЦА
print("ЖИВА таблица:", len(T), "условия,", len(set(v[1] for v in T.values())), "групи")
print("МАКС_ТОЧКИ =", lb.CB.SL.МАКС_ТОЧКИ, "| сбор тавани =", sum(lb.CB.SL.ТАВАН_ГРУПА.values()))
# броячът, който ботът наистина строи (ред 253 в b_сливане: у = {к: False for к in ТАБЛИЦА})
src = io.open("brain/b_сливане.py", encoding="utf-8").read()
m = re.search(r"у: dict\[str, bool\] = \{.*?\}", src)
print("броячът:", m.group(0), "-> слотове:", len(T))
# кой файл какво твърди
for f, pat in (("brain/b_сливане.py", None), ("brain/chart_brain.py", None),
               ("README.md", None), ("CHANGELOG.md", None),
               ("brain/ВРЪЗКА_С_БОТА.md", None)):
    s = io.open(f, encoding="utf-8").read()
    for i, ln in enumerate(s.splitlines(), 1):
        if re.search(r"\d+\s+условия", ln):
            print(f"  {f}:{i}: {ln.strip()[:90]}")
