# -*- coding: utf-8 -*-
"""Какво ИСТИНСКИ е пращано — от live/sent_log.jsonl."""
import json, io, re, collections
pat = re.compile(r"Риск \$([0-9,]+)@([0-9.]+)%")
лот = re.compile(r"<b>([0-9.]+) лот</b>")
c = collections.Counter(); l = collections.Counter()
общо = 0
for ln in io.open("live/sent_log.jsonl", encoding="utf-8"):
    ln = ln.strip()
    if not ln:
        continue
    r = json.loads(ln); t = r.get("text") or ""
    общо += 1
    for m in pat.findall(t):
        c[m] += 1
    for m in лот.findall(t):
        l[m] += 1
print("общо карти:", общо)
print("баланс@риск:", dict(c))
print("лотове     :", dict(l))
