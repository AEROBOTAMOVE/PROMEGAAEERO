# -*- coding: utf-8 -*-
"""№38: цитира ли _защо_мълчи старото −0.04$/40094 вместо клетката на гейта?"""
import sys, json, re
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb
stats = json.load(open("backtest_stats.json", encoding="utf-8"))

мета = (stats.get("_meta") or {})
print("_meta ключове:", list(мета)[:20])
for k in мета:
    if "40094" in json.dumps(мета[k], ensure_ascii=False) if isinstance(мета[k],(dict,list)) else False:
        print("  СТАРОТО ЧИСЛО е в _meta:", k, мета[k])

for пос in ("long","short"):
    кл = stats.get("fresh",{}).get(пос,{}).get("mixed",{})
    print(f"клетка fresh/{пос}/mixed: net={кл.get('net')} n={кл.get('n')}")
    ред = lb._защо_мълчи({"долар":0.0145,"лихви":-0.07}, {пос:0}, пос, стат=stats)
    т = "\n".join(ред)
    print(т)
    print("  съдържа ли 40094?", "40094" in т, "| съдържа ли −0.04$?", "−0.04$" in т or "-0.04$" in т)
    m = re.search(r"дава ([+−-]\d+\.\d\d)\$", т)
    print("  цитираното число:", m.group(1) if m else None,
          "| очаквано от клетката:", кл.get("net"))
    print("---")
# без стат
print("БЕЗ стат:", lb._защо_мълчи({"долар":0.0145,"лихви":-0.07}, {"long":0}))
