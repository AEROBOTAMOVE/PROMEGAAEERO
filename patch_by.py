import io, hashlib, re

p = "live_bot.py"
src = io.open(p, encoding="utf-8", newline="").read()
assert "trace=None" not in src, "кръпката вече е вътре"

# ── 1 · `_advice_entry` казва КОЙ ПЛАСТ е решил (по избор, не чупи викащите) ──
old_sig = ('def _advice_entry(direction, streak_n, stats, fast, shield, guard_n, '
           'sym="XAUUSD", stale_price=False):')
new_sig = ('def _advice_entry(direction, streak_n, stats, fast, shield, guard_n, '
           'sym="XAUUSD", stale_price=False, trace=None):')
assert src.count(old_sig) == 1
src = src.replace(old_sig, new_sig, 1)

# помощникът се вмъква веднага след докстринга на функцията
doc_end = '''    Г2: изходът е ясен — ДА / ИЗЧАКАЙ / НЕ. В5: губещ клас се казва явно."""
'''
helper = '''    Г2: изходът е ясен — ДА / ИЗЧАКАЙ / НЕ. В5: губещ клас се казва явно.
    ОДИТ-15/б: `trace` (по избор) казва КОЙ ПЛАСТ е решил. Без него дневникът
    записваше кофата дори когато решението е дошло от стоп-пазача, щита или
    старата цена — тоест ПРЕДИ клетката изобщо да бъде погледната. Който после
    брои «колко отказа клетката mixed», брои чужди откази."""
    def _by(k):
        if trace is not None:
            trace["by"] = k
'''
assert src.count(doc_end) == 1
src = src.replace(doc_end, helper, 1)

# всеки ранен изход се маркира
subs = [
    ('    if guard_n >= 2:\n        return "НЕ — 2 стопа днес',
     '    if guard_n >= 2:\n        _by("стоп-пазач")\n        return "НЕ — 2 стопа днес'),
    ('    if shield and direction == "short":\n        return f"НЕ СЕГА — US-щит',
     '    if shield and direction == "short":\n        _by("US-щит")\n        return f"НЕ СЕГА — US-щит'),
    ('    if stale_price:                                      # Г9',
     '    if stale_price:                                      # Г9'),
]
for a, b in subs:
    assert src.count(a) == 1, f"липсва котва: {a[:40]}"
    src = src.replace(a, b, 1)

# stale_price — маркерът се слага пред неговия return
a = '        return "ИЗЧАКАЙ — цената е ~10-15 мин стара'
b = '        _by("стара цена")\n        return "ИЗЧАКАЙ — цената е ~10-15 мин стара'
assert src.count(a) == 1
src = src.replace(a, b, 1)

# четирите изхода, които НАИСТИНА идват от клетката
for a, b in (
    ('            return (f"ИЗЧАКАЙ — пресен ({src_}), но исторически',
     '            return (f"ИЗЧАКАЙ — пресен ({src_}), но исторически'),
):
    pass
cell_rets = [
    ('        if seg.get("n", 0) >= MIN_N and (seg.get("net", 0) <= 0 or _noise(seg)):\n'
     '            why = ',
     '        if seg.get("n", 0) >= MIN_N and (seg.get("net", 0) <= 0 or _noise(seg)):\n'
     '            _by("клетка")\n            why = '),
    ('        return f"ДА — пресен сигнал ({dn})"',
     '        _by("клетка")\n        return f"ДА — пресен сигнал ({dn})"'),
    ('        return f"НЕ — {cls}: {seg[\'win\']}%',
     '        _by("клетка")\n        return f"НЕ — {cls}: {seg[\'win\']}%'),
    ('    return f"ДА (слаб) — {ctx}; малък размер"',
     '    _by("клетка")\n    return f"ДА (слаб) — {ctx}; малък размер"'),
]
for a, b in cell_rets:
    assert src.count(a) == 1, f"липсва котва на клетката: {a[:50]!r}"
    src = src.replace(a, b, 1)

# ── 2 · викането в main() подава trace и го записва ──────────────────────
old_call = '''    advice_txt, _adv_ok = _advice_entry(new_dir, streak_n, stats, fast_g, shield, guard.get(new_dir or "", 0),
                                        sym="XAUUSD", stale_price=(spot_g is None)) if new_dir else ("", False)'''
new_call = '''    _gate_trace = {}
    advice_txt, _adv_ok = _advice_entry(new_dir, streak_n, stats, fast_g, shield, guard.get(new_dir or "", 0),
                                        sym="XAUUSD", stale_price=(spot_g is None),
                                        trace=_gate_trace) if new_dir else ("", False)'''
assert src.count(old_call) == 1
src = src.replace(old_call, new_call, 1)

old_rec = '''                             "gate": ({"dir": new_dir, "streak": streak_n,
                                       "cell": _cell_name(streak_n), "ok": bool(_adv_ok),
                                       "why": advice_txt} if new_dir else None),'''
new_rec = '''                             # `by` = кой пласт РЕШИ. `cell` е кофата, която БИ важала —
                             # тя е меродавна САМО когато by == "клетка".
                             "gate": ({"dir": new_dir, "streak": streak_n,
                                       "cell": _cell_name(streak_n), "ok": bool(_adv_ok),
                                       "by": _gate_trace.get("by"),
                                       "why": advice_txt} if new_dir else None),'''
assert src.count(old_rec) == 1
src = src.replace(old_rec, new_rec, 1)

io.open(p, "wb").write(src.encode("utf-8"))
print(f"live_bot.py: {len(src.split(chr(10)))} реда · sha "
      f"{hashlib.sha256(src.encode('utf-8')).hexdigest()[:14]}")
