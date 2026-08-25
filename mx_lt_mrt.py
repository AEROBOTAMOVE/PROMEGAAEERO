# -*- coding: utf-8 -*-
import sys, io, runpy
sys.argv=["x"]; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0,".")
_r=sys.stdout
class _T(io.StringIO): buffer=io.BytesIO()
sys.stdout=_T(); m=runpy.run_path("mx_stopstoi4.py"); sys.stdout=_r
import live_bot as lb
нс=m["нов_стои"]
print("MACRO_LBL:", lb.MACRO_LBL)
print()
print("### ЖИВОТО СЪСТОЯНИЕ, което live_bot.py:3120-3122 произвежда,")
print("### когато УМРЕ САМО ЕДНО краче: macro = {всички: False}, мъртви = [само умрелия]")
for мъртъв, посока in (("долар (DXY)","short"), ("долар (DXY)","long"),
                       ("миньори (GDX)","short"), ("миньори (GDX)","long")):
    macro = {k: False for k in lb.MACRO_LBL}      # <- точно както прави ботът
    health = {"мъртви": [мъртъв]}
    т = нс(посока, 20.0, 4365.20, macro, health, "2026-08-21T11:20")
    print(f"\n--- мъртво краче: {мъртъв} · посока: {посока} ---")
    for л in т.split("\n"):
        if л.startswith("📌 КАКВО") or л.startswith("⚠️"):
            print("   НОВАТА:", л)
    if not any(л.startswith("⚠️") for л in т.split("\n")):
        print("   НОВАТА: ⚠️ НЯМА НИКАКВО ПРЕДУПРЕЖДЕНИЕ")
    # старата
    с = lb._standing_msg(посока, ("1час",посока,7,"strong","СИЛЕН"), 20.0, None, 4370.0,
                         4365.20, [("1час",посока,7,"strong","СИЛЕН")]*7, macro, health,
                         "2026-08-21T11:20")
    for л in с.split("\n"):
        if л.startswith("📌 долар") or л.startswith("⚠️"):
            print("   СТАРАТА:", л)
