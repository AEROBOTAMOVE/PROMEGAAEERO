# -*- coding: utf-8 -*-
"""ЛОВ 1 · единични проверки на състоянието, БЕЗ мрежа."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import live_bot as lb

R = 400   # брой поредни руна

print("=== A · ПРЕКЪСВАЧЪТ САМ Е ОКОВАН ЗАД ТАВАНА ===")
print("   ред 913:  if state[_бр_к] >= BASIS_STUCK_N and abs(now_b) <= cap:")
cap = lb._basis_cap(4700.0, "XAUUSD")
print(f"   cap при злато 4700$ = {cap:.2f}$  ·  BASIS_STUCK_N = {lb.BASIS_STUCK_N}")
st = {"basis_g": 25.515}
notes = []
spot = {"mid": 4600.0, "src": "swq"}       # истински базис = 4700-4600 = 100$ > cap 94$
for i in range(R):
    v = lb._basis_update(st, "basis_g", spot, 4700.0, notes, cap=cap, now_utc="2026-08-21T10:00")
print(f"   след {R} руна: basis_g={st['basis_g']}  брояч={st.get('basis_g_отказ')}  върнато={v}")
print("   последна бележка:", notes[-1])
print("   -> прекъсвачът НЕ се задейства НИКОГА, докато истината е над тавана")

print()
print("=== A2 · същото, но истината е ПОД тавана -> прекъсвачът работи ===")
st2 = {"basis_g": 25.515}
n2 = []
spot2 = {"mid": 4610.0, "src": "swq"}      # истински базис = 90$ < cap 94$
for i in range(30):
    v2 = lb._basis_update(st2, "basis_g", spot2, 4700.0, n2, cap=cap, now_utc="2026-08-21T10:00")
    if "🔓" in n2[-1]:
        print(f"   рун {i+1}: {n2[-1]}")
        break
print(f"   след 30 руна: basis_g={st2['basis_g']} брояч={st2.get('basis_g_отказ')}")

print()
print("=== B · СТУДЕНИЯТ СТАРТ НЯМА НИКАКЪВ ПРЕКЪСВАЧ (близнакът на поправката) ===")
st3 = {}                                   # чиста памет: meta.json е бил повреден/нов
n3 = []
spot3 = {"mid": 4600.0, "src": "swq"}
for i in range(R):
    v3 = lb._basis_update(st3, "basis_g", spot3, 4700.0, n3, cap=cap, now_utc="2026-08-21T10:00")
print(f"   след {R} руна: state={ {k:v for k,v in st3.items()} }")
print(f"   върнато={v3}   ключ 'basis_g' в паметта? {'basis_g' in st3}")
print("   брояч на отказите?", [k for k in st3 if "отказ" in k] or "НЯМА")
print("   бележка:", n3[-1])
print("   -> и 400-те бележки са ЕДНА И СЪЩА; нищо не ескалира")

print()
print("=== B2 · какво прави това с живата цена (веригата до мълчанието) ===")
следа = {}
s = lb._spot_sane(spot3, 4700.0 - v3, 8.0, bar_rng=4.0, spot_jump=None, следа=следа)
print("   _spot_sane(спот 4600, референция бар-базис =", 4700.0 - v3, ") ->", s)
print("   следа:", следа)
print("   -> spot=None на всеки рун = «стара цена» = нула входа")

print()
print("=== C · ЗАБРАНАТА ЗА РЕ-ВЛИЗАНЕ НЕ СЕ ЧИСТИ, КОГАТО НИЩО НЕ СЕ ЗАТВАРЯ ===")
meta = {}
ok, why = lb._reentry_ban(meta, "long", 2, why="2 стопа днес в тази посока — спирам до утре", set_it=True)
print("   сложена:", meta["reentry_ban"])
print("   ден 1:", lb._reentry_ban(meta, "long", 2))
print("   (никой не вика функцията, докато няма затворена сделка — ред 3267:")
print("    'if closed_kinds and actionable and trade is None:')")
print("   ден 2, стрийкът все още 2 (дневният бар е застоял/празник):",
      lb._reentry_ban(meta, "long", 2))
print("   причината, която се повтаря, казва «до утре», а няма дата в записа:",
      json.dumps(meta["reentry_ban"], ensure_ascii=False))

print()
print("=== D · СРЕБЪРНИЯТ КОНТРАКТЕН ТАВАН ===")
print("   TF_BASIS_CAP =", lb.TF_BASIS_CAP, " TF_BASIS_CAP_S =", lb.TF_BASIS_CAP_S)
