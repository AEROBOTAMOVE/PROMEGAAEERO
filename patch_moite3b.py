# -*- coding: utf-8 -*-
"""ОДИТ-48 (част 2) · таванът на опашката реже, и числото на пулса идва от клетката."""
import io, sys, ast, hashlib

ops = []


def rep(old, new, why, n=1):
    global s
    c = s.count(old)
    if c != n:
        print(f"  x СПИРАМ «{why}»: {c} съвпадения, чакам {n}\n    {old[:140]!r}")
        sys.exit(1)
    s = s.replace(old, new)
    ops.append(why)


p = "live_bot.py"
s = io.open(p, encoding="utf-8", newline="").read()

_ЗАПИС = '    ob_f.write_text("\\n".join(json.dumps(m, ensure_ascii=False) for m in remaining), encoding="utf-8")'
_ТАВАН = '''    # 🔴 ОДИТ-48 · ТАВАНЪТ РЕАЛНО РЕЖЕ. Дотук беше само ОБЯВЕН (мое, v9.8), а
    # тестът ми «го пазеше», защото проверяваше единствено декларацията —
    # константа, която нищо не прави, и тест, който я пази. Хванато от армията.
    # ИЗХОДНИТЕ карти НИКОГА не се режат: те съобщават пари, вече на риск.
    if ОПАШКА_ТАВАН > 0 and len(remaining) > ОПАШКА_ТАВАН:
        _пази = [m for m in remaining
                 if str(m.get("tag", "")).split(":")[0] in EXIT_TAGS]
        _друго = [m for m in remaining
                  if str(m.get("tag", "")).split(":")[0] not in EXIT_TAGS]
        _място = max(0, ОПАШКА_ТАВАН - len(_пази))
        _орязани = len(_друго) - _място
        remaining = _пази + (_друго[-_място:] if _място else [])
        if _орязани > 0:
            statuses.append(f"🔴 опашката преля: {_орязани} НАЙ-СТАРИ карти "
                            f"изхвърлени (таван {ОПАШКА_ТАВАН}); изходните са запазени")
'''
rep(_ЗАПИС, _ТАВАН + _ЗАПИС, "2 · таванът реже")

# ── №3 · числото идва от клетката, по която съди гейтът ──────────────────
rep('        Л.append("📌 в такъв пазар дава −0.04$ на сделка (мерено, 40094 сделки)")',
    '''        # 🔴 ОДИТ-48 · ЧИСЛОТО ИДВА ОТ КЛЕТКАТА, ПО КОЯТО СЪДИ ГЕЙТЪТ.
        # Дотук пишеше зазидано «−0.04$ (40094 сделки)» — числото от _meta,
        # което описва СЛЕТИТЕ кофи ПРЕДИ разделянето от 04.08. Гейтът обаче
        # съди по `/fresh/long/mixed/net` = −0.47$. Число на карта, което не
        # идва от клетката, по която се решава, е точно това, което този бот
        # не бива да прави.
        _кл = ((стат or {}).get("fresh", {}).get("long", {}).get("mixed", {})
               if isinstance(стат, dict) else {})
        _нет = _кл.get("net")
        if _нет is not None:
            Л.append(f"📌 в такъв пазар мереното дава {float(_нет):+.2f}$ на сделка")
        else:
            Л.append("📌 в такъв пазар мереното правило не носи нищо")''',
    "3 · числото от клетката")

rep("def _защо_мълчи(macro_raw, streaks, new_dir=None):",
    "def _защо_мълчи(macro_raw, streaks, new_dir=None, стат=None):",
    "3 · функцията приема статистиката")

rep("    _обясн = _защо_мълчи(macro_raw, streaks, new_dir)",
    "    _обясн = _защо_мълчи(macro_raw, streaks, new_dir, стат=stats)",
    "3 · пулсът я подава")

rep("               spot_g, spot_s, macro, shield, weekend, macro_raw=None, streaks=None):",
    "               spot_g, spot_s, macro, shield, weekend, macro_raw=None, streaks=None,\n"
    "               stats=None):",
    "3 · пулсът я приема")

rep('''                                                 macro_raw=macro_health,
                                                 streaks=regime.get("streaks"))))''',
    '''                                                 macro_raw=macro_health,
                                                 streaks=regime.get("streaks"),
                                                 stats=stats)))''',
    "3 · ботът я подава на пулса")

rep("def _обрат_msg(старо, ново, macro_raw, streaks):",
    "def _обрат_msg(старо, ново, macro_raw, streaks, стат=None):",
    "3 · обратът я приема")

rep("    L += _защо_мълчи(macro_raw, streaks)",
    "    L += _защо_мълчи(macro_raw, streaks, стат=стат)",
    "3 · обратът я подава")

rep('                    _мк, regime.get("streaks"))))',
    '                    _мк, regime.get("streaks"), stats)))',
    "3 · ботът я подава на обрата")

io.open(p, "wb").write(s.encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
b = io.open(p, encoding="utf-8").read()
print(f"{p}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
