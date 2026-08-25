# -*- coding: utf-8 -*-
import sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8",errors="replace")
D=r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0,D)
import live_bot as B

# Sabitieto ot nahodkata: 23:50 Sofia = 20:50 UTC (lyato). Sashtoto sabitie v cq forma:
cq={"events":[{"name":"vazhno","dt":"2026-08-20T20:50:00.000Z","impact":"high"}]}
ctx={'date':'2026-08-20','events':[{'time_sofia':'23:50','name':'vazhno','impact':'high'}]}
print("%-18s %-7s %-22s %s" % ("UTC","Sofia","_event_shield","_cq_macro_block"))
for iso in ['2026-08-20T20:35','2026-08-20T20:50','2026-08-20T21:05','2026-08-20T21:20','2026-08-20T21:29','2026-08-20T21:31']:
    print("%-18s %-7s %-22s %s" % (iso, B._sofia(iso), B._event_shield(ctx,iso), B._cq_macro_block(cq,iso)))
print()
print("Prozorec na _cq_macro_block: -20..+40 min, PALNA data, blokira DVETE posoki")
print("Prozorec na shield:          +-20 min, bez data, blokira SAMO short")
