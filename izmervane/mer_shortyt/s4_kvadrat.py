# -*- coding: utf-8 -*-
"""s4 - the R:R square the task asked for, printed as a square, plus the best
ABSOLUTE net in the whole family (beating the blind short and making money are
two different questions and both have to be answered)."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "rez_mreja.json"))
nm = R["names"]; dl = np.array(R["delta"]); rl = np.array(R["real"])
lo = np.array(R["lo"]); hi = np.array(R["hi"]); rlo = np.array(R["real_lo"]); rhi = np.array(R["real_hi"])
idx = {n: i for i, n in enumerate(nm)}
SL = [10.0, 15.0, 20.0, 30.0, 40.0, 60.0]; TP = [5.0, 7.5, 10.0, 15.0, 20.0, 30.0, 40.0]

print("=" * 100)
print("ТАБЛИЦА 5 · R:R КВАДРАТЪТ (една цел, без стълба, 5 дни) - РАЗЛИКА спрямо слепия шорт, $/сделка")
print("=" * 100)
print("%-8s" % "стоп\цел" + "".join("%9s" % ("%g" % t) for t in TP))
for s in SL:
    row = "SL %-5g" % s
    for t in TP:
        row += "%9.3f" % dl[idx["TP%g SL%g 5д" % (t, s)]]
    print(row)
print("\nСЪЩИЯТ КВАДРАТ, но АБСОЛЮТЕН нет $/сделка (положително = прави пари)")
print("%-8s" % "стоп\цел" + "".join("%9s" % ("%g" % t) for t in TP))
for s in SL:
    row = "SL %-5g" % s
    for t in TP:
        row += "%9.3f" % rl[idx["TP%g SL%g 5д" % (t, s)]]
    print(row)
print("\nR:R по искането: 1:1 / 1:0.75 / 1:0.5 при стоп 20$")
for t, lab in ((20.0, "1:1  "), (15.0, "1:0.75"), (10.0, "1:0.5 ")):
    i = idx["TP%g SL20 5д" % t]
    print("  %s  TP%-5g SL20 5д   реален %+.4f [%+.3f, %+.3f]   разлика %+.4f [%+.3f, %+.3f]"
          % (lab, t, rl[i], rlo[i], rhi[i], dl[i], lo[i], hi[i]))

o = np.argsort(-rl)
print("\n" + "=" * 100)
print("ТАБЛИЦА 6 · НАЙ-ДОБРИЯТ АБСОЛЮТЕН НЕТ от 152-те (прави ли ИЗОБЩО пари някоя геометрия)")
print("=" * 100)
print("%-32s %10s %-22s %10s %-22s" % ("геометрия", "реален$", "95% инт. на реалния", "разлика", "95% инт. на разликата"))
for i in o[:8]:
    print("%-32s %+10.4f  [%+.3f, %+.3f] %+10.4f  [%+.3f, %+.3f]"
          % (nm[i], rl[i], rlo[i], rhi[i], dl[i], lo[i], hi[i]))
print("\nгеометрии с реален нет > 0: %d от %d" % (int((rl > 0).sum()), len(rl)))
print("геометрии с реален нет, чийто 95%% интервал е ИЗЦЯЛО над 0: %d" % int((rlo > 0).sum()))
print("\nТАВАНЪТ ОТ ШУМ: най-добрата от 152 върху чист шум даде %+.4f$ (интервалът ѝ Е над нулата)."
      % R["noise_best_delta"])
print("Най-добрата от 152 върху ИСТИНСКИТЕ входове даде %+.4f$ - ПО-МАЛКО, отколкото шумът произвежда сам."
      % dl.max())
