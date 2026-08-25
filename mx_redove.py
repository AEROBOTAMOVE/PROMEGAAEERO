# -*- coding: utf-8 -*-
"""ЗАЩО ДВА ИНСТРУМЕНТА ДАВАТ РАЗЛИЧЕН НОМЕР НА РЕД за един и същ ред."""
import io, sys, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

сур = io.open("live_bot.py", "rb").read()
т = сур.decode("utf-8")
print("байта:", len(сур))
print("брой \\n :", т.count("\n"))
print("брой \\r :", т.count("\r"))
print("брой \\r\\n:", т.count("\r\n"))
for име, зн in (("\\x0b ВЕРТ.ТАБ", "\x0b"), ("\\x0c ЛИСТ", "\x0c"),
                ("\\x1c", "\x1c"), ("\\x1d", "\x1d"), ("\\x1e", "\x1e"),
                ("\\x85 NEL", "\x85"), ("U+2028 LS", " "), ("U+2029 PS", " ")):
    n = т.count(зн)
    if n:
        print(f"  {име}: {n}")
print("len(splitlines()) =", len(т.splitlines()))
print("len(split('\\n'))  =", len(т.split("\n")))

# къде точно се разминават
i = 0
for ном, ред in enumerate(т.split("\n"), 1):
    for зн in ("\x0b", "\x0c", "\r", " ", "\x85"):
        if зн in ред:
            i += 1
            if i <= 12:
                print(f"  ред(\\n) {ном}: съдържа {зн!r} → {ред.strip()[:70]!r}")
print("общо редове с допълнителен разделител:", i)

# какво казва ast
t = ast.parse(т)
for n in ast.walk(t):
    if isinstance(n, ast.FunctionDef) and n.name in ("_exit_msg", "_shadow_exit_msg", "_sig_msg"):
        print(f"ast: {n.name} → lineno {n.lineno}")
