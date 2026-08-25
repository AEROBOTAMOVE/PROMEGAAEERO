# -*- coding: utf-8 -*-
"""СКЕПТИК · ЗНАЧИМОСТ. Колко често замразен tf_basis мени ОТЧЕТА на рамката?
Мери се на 60 дни ЖИВИ 5м данни: за всеки ден refs = дневната крива ДО този ден,
цената = последният 5м бар на деня. Сравняват се САМО ценовите тестове (макрото
се държи неутрално и еднакво в двата случая) — тоест разликата е чисто от tf_adj.
"""
import sys, os, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
spec = importlib.util.spec_from_file_location("lb", os.path.join(BASE, "live_bot.py"))
lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)

gold_d = lb._yf("GC=F", "3y", "1d")
m5 = lb._yf("GC=F", "60d", "5m")
macro = {"миньори": True, "долар": False, "лихви": True}   # неутрално, еднакво и в двата случая

dni = sorted(set(m5.index.normalize()))
print("дни с 5м данни: %d  (%s → %s)" % (len(dni), dni[0].date(), dni[-1].date()))

ЗАМРАЗЕН = -3.851        # стойността от 02.08 (живият журнал)
разлики = 0; общо = 0; примери = []
for d in dni:
    ден = m5[m5.index.normalize() == d]
    if len(ден) == 0: continue
    dd = gold_d[gold_d.index <= d]
    if len(dd) < 60: continue
    refs = lb._refs(dd)
    истина = lb._tf_basis({}, "t", m5[m5.index <= ден.index[-1]], dd, [])
    a = lb._scores(ден, refs, macro, price_adj=истина)
    b = lb._scores(ден, refs, macro, price_adj=ЗАМРАЗЕН)
    ра = lb._resolve(a[0], a[1], macro); рб = lb._resolve(b[0], b[1], macro)
    общо += 1
    if ра[:3] != рб[:3]:
        разлики += 1
        примери.append((str(d.date()), round(истина, 2), ра[:3], рб[:3]))

print("\nдни, в които ЗАМРАЗЕН tf_basis (-3.851) дава ДРУГ отчет от истинския: %d от %d"
      % (разлики, общо))
for x in примери[:15]:
    print("   %s  истински tf=%s  ИСТИНА %s   ЗАМРАЗЕНО %s" % x)

# и втори срез: колко от 10-те ценови теста се обръщат
обърнати = 0; дни_с_обрат = 0
for d in dni:
    ден = m5[m5.index.normalize() == d]
    dd = gold_d[gold_d.index <= d]
    if len(ден) == 0 or len(dd) < 60: continue
    refs = lb._refs(dd)
    истина = lb._tf_basis({}, "t", m5[m5.index <= ден.index[-1]], dd, [])
    a = lb._scores(ден, refs, macro, price_adj=истина)
    b = lb._scores(ден, refs, macro, price_adj=ЗАМРАЗЕН)
    d1 = abs(a[0] - b[0]) + abs(a[1] - b[1])
    if d1: дни_с_обрат += 1; обърнати += d1
print("\nдни, в които поне ЕДНА точка се мени: %d от %d · общо обърнати точки: %d"
      % (дни_с_обрат, общо, обърнати))
