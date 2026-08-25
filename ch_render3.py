# -*- coding: utf-8 -*-
import sys, re, html
from pathlib import Path
sys.argv = ["x"]
БАЗА = Path(__file__).resolve().parent
sys.path.insert(0, str(БАЗА))
import огледало as og
def чист(t): return re.sub(r"<[^>]+>", "", html.unescape(str(t)))
lb = og.lb
К = {}
# реалистични макро-числа: долар +0.0032 = доларът ПАДА 0.32% (добро за златото)
_добро = {"долар": 0.0032, "лихви": 0.021, "миньори": 1.1}
_смес  = {"долар": -0.0028, "лихви": 0.021, "миньори": 1.1}
К["91a · ОБРАТ подредено"] = lb._обрат_msg((False, True), (True, True), _добро,
                                            {"long": 3, "short": 0}, og.st)
К["91b · ОБРАТ разбъркано"] = lb._обрат_msg((True, True), (False, True), _смес,
                                             {"long": 0, "short": 2}, og.st)
К["93 · ПУЛС с макро-обяснение"] = lb._pulse_msg("09", og.brd, og.best, "long",
    og.СЪВЕТ["не_смес"][0], False, None, None, {"mid": 4365.2}, {"mid": 65.15},
    og.macm, False, False, macro_raw=_смес, streaks={"long": 0, "short": 2}, stats=og.st)
К["94 · ПУЛС макро-фийдът мълчи"] = lb._pulse_msg("14", og.brd, og.best, "short",
    og.СЪВЕТ["не_шорт"][0], False, None, None, {"mid": 4365.2}, None,
    og.macm, False, False, macro_raw={"долар": None, "лихви": None},
    streaks={"long": 0, "short": 2}, stats=og.st)
out = []
for име in sorted(К):
    т2 = чист(К[име])
    out.append("=" * 66); out.append(f"### {име}   [{len(т2.splitlines())} реда · {len(т2)} знака]")
    out.append("=" * 66); out.append(т2); out.append("")
print("\n".join(out))
