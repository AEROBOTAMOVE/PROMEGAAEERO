# -*- coding: utf-8 -*-
import sys; sys.argv=["x"]; sys.stdout.reconfigure(encoding="utf-8")
import live_bot as lb, inspect
print("СПАЛ_МИН =", getattr(lb,"СПАЛ_МИН",None))
for a,b in [("2026-08-07T20:55","2026-08-09T22:01"),("2026-08-14T20:56","2026-08-16T22:02"),
            ("2026-08-12T08:00","2026-08-13T11:20")]:
    тм = lb._търговски_минути(a,b)
    print(f"{a} → {b} · търговски мин={тм} ({тм/60:.1f}ч) · пали={тм>=lb.СПАЛ_МИН}")
    if тм>=lb.СПАЛ_МИН:
        print(lb._спал_msg(a,b,тм) if len(inspect.signature(lb._спал_msg).parameters)==3 else lb._спал_msg(a,b))
