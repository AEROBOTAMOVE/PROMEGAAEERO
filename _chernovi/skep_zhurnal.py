# -*- coding: utf-8 -*-
"""СКЕПТИК · какво казва ЖИВИЯТ дневник за отхвърляните базиси (произход за разсейката)."""
import sys, io, os, json, re, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
Ж = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "live", "brain_journal.jsonl")
print("файл:", Ж, "· размер:", os.path.getsize(Ж), "байта")
общо = 0; отказ = []; ре = re.compile(r"отхвърлен скок на базиса \(([+-][\d.]+)\)")
дати = []
for ред in open(Ж, encoding="utf-8"):
    try: d = json.loads(ред)
    except Exception: continue
    общо += 1
    for n in (d.get("notes") or []):
        m = ре.search(n)
        if m:
            отказ.append(float(m.group(1))); дати.append(d.get("ts") or d.get("date"))
print("ръна в дневника:", общо, "· записи с «отхвърлен скок на базиса»:", len(отказ))
if отказ:
    print("първи/последен запис:", дати[0], "->", дати[-1])
    print("min=%.2f max=%.2f разсейка=%.2f$" % (min(отказ), max(отказ), max(отказ)-min(отказ)))
    c = collections.Counter(round(x,1) for x in отказ)
    print("най-чести стойности:", c.most_common(6))
