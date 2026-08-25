# -*- coding: utf-8 -*-
import ast, io
t=ast.parse(io.open("live_bot.py",encoding="utf-8").read())
for f in ast.walk(t):
    if isinstance(f,ast.If):
        ls=[n.lineno for n in ast.walk(f) if isinstance(n,ast.Call)
            and isinstance(n.func,ast.Name) and n.func.id=="_pulse_msg"]
        if ls:
            print("ПАЗАЧ на _pulse_msg (ред %d):"%f.lineno, ast.unparse(f.test)[:400])
            print("   съдържа ли 'key_age_h' или 'stale':",
                  ("key_age_h" in ast.unparse(f.test)) or ("stale" in ast.unparse(f.test)))
