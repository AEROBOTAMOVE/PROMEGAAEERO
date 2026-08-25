# -*- coding: utf-8 -*-
import sys, io, re, html, json, datetime as dt
from pathlib import Path
sys.argv = ["x"]
БАЗА = Path(__file__).resolve().parent
sys.path.insert(0, str(БАЗА))
import огледало as og

def чист(t):
    return re.sub(r"<[^>]+>", "", html.unescape(str(t)))

К = og.карти()
К.update(og.одит_карта())
lb = og.lb

# ── трите функции, които огледалото НЕ покрива ──
try:
    К["90 · СПАЛ"] = lb._спал_msg(187, "2026-08-11T05:10", "2026-08-11T08:17")
except Exception as e:
    К["90 · СПАЛ"] = f"[ГРЕШКА {type(e).__name__}: {e}]"
try:
    К["91 · ОБРАТ"] = lb._обрат_msg("long", "short", og.macm, {"long": 3, "short": 0}, og.st)
except Exception as e:
    К["91 · ОБРАТ"] = f"[ГРЕШКА {type(e).__name__}: {e}]"
try:
    т = {"вход": 4449.2, "стоп": 4453.79, "цел": 4408.6, "посока": "short",
         "отворена": "2026-08-11T11:00", "цена": 4449.2}
    К["92 · МОЗЪК ИЗХОД"] = lb._мозък_изход_msg(т, "цел", 4408.6, 2)
except Exception as e:
    К["92 · МОЗЪК ИЗХОД"] = f"[ГРЕШКА {type(e).__name__}: {e}]"

out = []
for име in sorted(К):
    т = чист(К[име])
    out.append("=" * 66)
    out.append(f"### {име}   [{len(т.splitlines())} реда · {len(т)} знака]")
    out.append("=" * 66)
    out.append(т)
    out.append("")
p = Path(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad\KARTI.txt")
p.write_text("\n".join(out), encoding="utf-8")
print("OK", len(К), "карти ->", p)
