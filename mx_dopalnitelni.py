# -*- coding: utf-8 -*-
"""Ръбови варианти на карти 5 и 6 + ПЪЛЕН списък находки на стил.py."""
import sys, io
sys.argv = ["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
import runpy
_нем = io.StringIO()
_реален = sys.stdout


class _Тих(io.StringIO):
    buffer = io.BytesIO()


sys.stdout = _Тих()
m = runpy.run_path("mx_stopstoi4.py")
sys.stdout = _реален
import стил as st
import live_bot as lb

нов_стоп, нов_стои, К = m["нов_стоп"], m["нов_стои"], m["К"]
NOW = "2026-08-21T10:00"
доп = {}
доп["5д СТОП · СРЕБРО продажба · с гап"] = нов_стоп(
    "sl", {"direction": "short", "entry": 65.150, "sym": "XAGUSD", "opened": "2026-08-20T09:00",
           "levels": lb._levels_silver(65.150, "short"), "hit": {}},
    65.700, NOW, "бар", True, guard_n=0, next_line="", now_utc=NOW, dec=3)
доп["5е СТОП · ТРЕТИ стоп днес · продажба"] = нов_стоп(
    "sl", {"direction": "short", "entry": 4358.0, "sym": "XAUUSD", "opened": "2026-08-21T04:00",
           "levels": lb._levels(4358.0, "short"), "hit": {}},
    4378.00, NOW, "бар", False, guard_n=3,
    next_line="НЕ — 3 стопа днес в тази посока — спирам до утре", now_utc=NOW)
доп["5ж НУЛА след ЦЕЛ 1 И ЦЕЛ 2"] = нов_стоп(
    "sl", {"direction": "long", "entry": 4358.0, "sym": "XAUUSD", "opened": "2026-08-19T09:00",
           "levels": {"tp1": 4365.50, "tp2": 4370.00, "tp3": 4378.00, "sl": 4358.00},
           "hit": {"tp1": True, "tp2": True}, "hit_px": {"tp1": 4365.50, "tp2": 4370.00}},
    4358.00, NOW, "бар", False, guard_n=0, next_line="", now_utc=NOW)
доп["6д СТОИ · ПРОДАЖБА · 16ч · всичко натам"] = нов_стои(
    "short", 16.0, 4365.20, {"долар": False, "лихви": False, "миньори": False}, {},
    "2026-08-21T11:20")
доп["6е СТОИ · 40ч · само лихвите живи и СРЕЩУ"] = нов_стои(
    "long", 40.0, 4365.20, {"долар": False, "лихви": False},
    {"мъртви": ["долар (DXY)"]}, "2026-08-21T11:20")

for име in sorted(доп):
    ч = st.чист(доп[име])
    р = [x for x in ч.split("\n") if x.strip()]
    print("=" * 78)
    print(име)
    print(ч)
    print(f"--- редове={len(р)} знаци={len(ч)} най-дълъг={max(len(x) for x in р)}")

всичко = dict(К)
всичко.update(доп)
print("\n══ ВСИЧКИ НАХОДКИ НА стил.py (таван 15 реда) ══")
n = 0
for име in sorted(всичко):
    for в, x in st.провери(име, всичко[име], макс_редове=15):
        print(f"   [{в}] {име} :: {x}")
        n += 1
print(f"   ({n} находки общо)")

print("\n══ П11 · два различни минуса на един ред ══")
лош = [(и, л) for и, т in всичко.items() for л in st.чист(т).split("\n")
       if "-" in л and "−" in л]
print("   няма" if not лош else лош)

print("\n══ П11 · «🛑 СТОП» в началото на истинския стоп ══")
for и, т in sorted(всичко.items()):
    if и.startswith("5") and "НУЛА" not in и:
        п = st.чист(т).split("\n")[0]
        print(f"   {и}: startswith('🛑 СТОП') = {п.startswith('🛑 СТОП')}")

print("\n══ ГАБАРИТИ ══")
print("   редове макс:", max(len([x for x in st.чист(t).split("\n") if x.strip()])
                             for t in всичко.values()))
print("   знаци  макс:", max(len(st.чист(t)) for t in всичко.values()))
print("   заглавен ред макс:", max(len(st.чист(t).split("\n")[0]) for t in всичко.values()))
print("   латиница:", sorted({c for t in всичко.values() for c in st.чист(t)
                              if "a" <= c.lower() <= "z"}) or "няма")
