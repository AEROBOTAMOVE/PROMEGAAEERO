# -*- coding: utf-8 -*-
import sys, re, html, json
from pathlib import Path
Б = Path(__file__).resolve().parent
sys.path.insert(0, str(Б)); sys.argv=["x"]
import огледало as ог
lb = ог.lb; st = ог.st
def чист(t): return re.sub(r"<[^>]+>", "", html.unescape(str(t)))

print("ZONE_W =", lb.ZONE_W, " МАЛЪК_РАЗМЕР_W =", lb.МАЛЪК_РАЗМЕР_W,
      " SL_D =", lb.SL_D, " PIP =", lb.PIP)

СЪВЕТ_ДА  = lb._advice_entry("long", 1, st, None, False, 0)
СЪВЕТ_МАЛ = lb._advice_entry("long", 5, st, None, False, 0)
print("присъда пресен :", СЪВЕТ_ДА)
print("присъда застоял:", СЪВЕТ_МАЛ)

for зона in (None, ("A","зона A"), ("B","зона B"), ("C","зона C")):
    for мал, сув in ((False, СЪВЕТ_ДА), (True, СЪВЕТ_МАЛ)):
        zw = lb.ZONE_W.get(зона[0], 1.0) if зона else 1.0
        множ = zw * (lb.МАЛЪК_РАЗМЕР_W if мал else 1.0)
        т = чист(lb._sig_msg("long", 6, 5, "СИЛЕН", {"mid":4365.2}, 4365.0,
              "2026-08-11T11:15", ог.lv, 4365.2, сув[0], ог.mac, 1 if not мал else 5,
              {"vol_rank":0.35}, st, 5000, 2.0, adv_ok=True, zone=зона))
        ред = [r for r in т.split("\n") if r.startswith("📏") or r.startswith("⚠")]
        print(f"зона={зона[0] if зона else '—'} малък={мал} множител={множ:.3f}  ->  {' | '.join(ред)}")
