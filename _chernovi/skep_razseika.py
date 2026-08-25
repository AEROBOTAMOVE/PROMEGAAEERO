# -*- coding: utf-8 -*-
"""СКЕПТИК · би ли РАБОТИЛА предложената поправка (разсейка<=3.0$) върху ИСТИНСКИТЕ данни?"""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ре = re.compile(r"отхвърлен скок на базиса \(([+-][\d.]+)\)")
редици = []; текуща = []
for r in open("live/live_journal.jsonl", encoding="utf-8"):
    try: d = json.loads(r)
    except Exception: continue
    v = None
    for x in (d.get("notes") or []):
        m = ре.search(x)
        if m: v = float(m.group(1))
    if v is None:
        if текуща: редици.append(текуща); текуща = []
    else:
        текуща.append(v)
if текуща: редици.append(текуща)
print("поредици от ПОРЕДНИ отказа:", len(редици))
дълги = [s for s in редици if len(s) >= 12]
print("поредици с дължина >= BASIS_STUCK_N(12):", len(дълги))
мин = 0
for s in дълги:
    п = s[-12:]                       # прозорецът, който прекъсвачът вижда
    р = max(п) - min(п)
    ок = р <= 3.0
    мин += 1 if ок else 0
    print("  дължина %-4d последни12: разсейка=%7.2f$  медиана~%.2f  -> предложената поправка %s"
          % (len(s), р, sorted(п)[6], "ОТКЛЮЧВА" if ок else "НЕ отключва (ПАК ЗАКЛЮЧЕНО)"))
print("\nобобщение: предложената поправка би отключила %d от %d реални дълги поредици" % (мин, len(дълги)))
