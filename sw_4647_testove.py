# -*- coding: utf-8 -*-
"""№46 и №47: имат ли ЗЪБИ поправените тестове — проверка В ДВЕТЕ ПОСОКИ."""
import sys, json, copy
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb
stats=json.load(open("backtest_stats.json",encoding="utf-8"))

print("=== №46 · «П44 картата цитира ТОЧНО клетката» ===")
def проба(ст):
    кл=(ст.get("fresh",{}).get("long",{}).get("mixed",{})); нт=кл.get("net")
    т="\n".join(lb._защо_мълчи({"долар":0.0145,"лихви":-0.07},{"long":0},стат=ст))
    зп=("+" if float(нт)>=0 else "−")+f"{abs(float(нт)):.2f}$"
    return нт, зп, (зп in т), т
нт,зп,ок,т = проба(stats)
print(f"  истинската клетка net={нт} → чака «{зп}» → тестът: {'ЗЕЛЕН' if ок else 'ЧЕРВЕН'}")
print("   ред от картата:", [r for r in т.splitlines() if "$" in r])
# ОБРАТНАТА ПОСОКА: сменям клетката → следва ли я картата?
ст2=copy.deepcopy(stats); ст2["fresh"]["long"]["mixed"]["net"]=-3.33
нт2,зп2,ок2,т2 = проба(ст2)
print(f"  подменена клетка net={нт2} → «{зп2}» → тестът: {'ЗЕЛЕН' if ок2 else 'ЧЕРВЕН'}")
print("   ред от картата:", [r for r in т2.splitlines() if "$" in r])
# и че СТАРОТО число вече не се появява никъде
print("  «40094» в картата:", "40094" in т, "| «−0.04$»:", "−0.04$" in т)
print("  тестът би ли хванал зазидано число? (проба: подменям клетката, а картата да не мръдне)")
print("   → картата мръдна:", т != т2, "→ значи проверката НЕ е декоративна")

print()
print("=== №47 · L2-01 «изисква точно три семейства» ===")
print("  lb.EXIT_TAGS =", lb.EXIT_TAGS, "| брой:", len(lb.EXIT_TAGS))
задълж=("exit","s-exit","sh-exit","brain-exit")
print("  задължителните са вътре:", all(з in lb.EXIT_TAGS for з in задълж))
# ОБРАТНАТА ПОСОКА 1: пада ли тестът, ако добавя НОВО изходно семейство?
хип=tuple(lb.EXIT_TAGS)+("q-exit",)
т1=all(з in хип for з in задълж)
т2_=not (set(хип) & {"signal","s-signal","pulse","brain","digest","standing","ma","cq-ref","спал","обрат"})
т3=all("exit" in t for t in хип)
print("  с ДОБАВЕНО «q-exit» трите проверки дават:", т1, т2_, т3, "→ тестът НЕ пада")
# ОБРАТНАТА ПОСОКА 2: хваща ли, ако някой пъхне неизходен таг?
лош=tuple(lb.EXIT_TAGS)+("pulse",)
print("  с промъкнат «pulse»:",
      "нищо-неразвръзка" , not (set(лош) & {"signal","s-signal","pulse","brain","digest","standing","ma","cq-ref","спал","обрат"}),
      "| «exit» в името:", all("exit" in t for t in лош), "→ тестът ПАДА (както трябва)")
# ОБРАТНАТА ПОСОКА 3: маха ли се задължително семейство?
без=tuple(x for x in lb.EXIT_TAGS if x!="brain-exit")
print("  без «brain-exit»:", all(з in без for з in задълж), "→ тестът ПАДА (както трябва)")
