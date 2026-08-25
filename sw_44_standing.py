# -*- coding: utf-8 -*-
"""№44: стоящата карта обвинява свежестта при СМЕСЕНО макро."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb
print("REOFFER_MAX_AGE_H =", lb.REOFFER_MAX_AGE_H, "| СТОЯЩ_МАКС_Ч =", lb.СТОЯЩ_МАКС_Ч)
board=[("1ден","long",5,"medium","СРЕДЕН"),("4час","long",6,"strong","СИЛЕН")]
for име, macro in (("СМЕСЕНО (долар за, лихви срещу)", {"долар":True,"лихви":False}),
                   ("ПОДРЕДЕНО", {"долар":True,"лихви":True}),
                   ("СРЕЩУ", {"долар":False,"лихви":False})):
    t = lb._standing_msg("long", board[-1], 14.0, {"mid":4000.0}, 4000.0, 4000.0,
                         board, macro, None, "2026-08-19T09:00:00")
    p = re.sub(r"<[^>]+>","",t)
    print("=====", име); print(p)
    print("  има ли «не е пресен»:", "не е пресен" in p,
          "| има ли «не са единодушни»:", "не са единодушни" in p)
