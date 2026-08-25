# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s = open('_chernovi/_prefix_lb.py', encoding='utf-8').read()
i = s.index('def _reentry_ban')
print("=== ПРЕДИ ФИКСА (ff5d328a = v13.7) ===")
print(s[i:i+1200])
print("=== ИЗВИКВАНИЯ ПРЕДИ ФИКСА ===")
for m in re.finditer(r'_reentry_ban', s):
    ln = s[:m.start()].count('\n')+1
    line = s.splitlines()[ln-1]
    print(ln, '|', line.strip())
