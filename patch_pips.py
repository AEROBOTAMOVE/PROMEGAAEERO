# -*- coding: utf-8 -*-
"""ОДИТ-67б · пипсовете стигат до ВСЯКА карта с разстояние."""
import io, sys, ast, hashlib
ops = []
p = "live_bot.py"
s = io.open(p, encoding="utf-8", newline="").read()


def rep(old, new, why, n=1):
    global s
    c = s.count(old)
    if c != n:
        print(f"  x «{why}»: {c} съвпадения, чакам {n}\n    {old[:120]!r}")
        sys.exit(1)
    s = s.replace(old, new)
    ops.append(why)


# ── сигналната карта: стоп ────────────────────────────────────────────────
rep('''        L.append(f"📏 стоп {abs(entry - lv['sl']):.2f}$/унция · по 1/3 на всяка цел")''',
    '''        L.append(f"📏 стоп {_разст(entry, lv['sl'], sym, dec)} · по 1/3 на всяка цел")''',
    "сигнал · стоп в пипсове", 2)

# ── мозъчната карта: «нивото иска X$ място» ───────────────────────────────
rep('''                        _лот_ред = f"📏 нивото иска {_рм:.2f}$ място"''',
    '''                        _лот_ред = f"📏 нивото иска {_пипс(_рм)} ({_рм:.2f}$) място"''',
    "мозък · мястото в пипсове")

# ── изходната карта: печалбата ────────────────────────────────────────────
io.open(p, "wb").write(s.encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
