# -*- coding: utf-8 -*-
"""ОДИТ-47 (тестове) · П45 пази признанието за съня."""
import io, ast

p = "selftest.py"
s = io.open(p, encoding="utf-8", newline="").read()
assert "П45" not in s, "П45 вече съществува"

_ЧАСОВНИК = '\n    meta["последен_рън"] = now_utc'

БЛОК = '''# ═══ П45 · БОТЪТ ЗНАЕ, ЧЕ Е СПАЛ (ОДИТ-47) ═══════════════════════════════
# Мерено на 1965 живи ръна: една дупка от 447 МИНУТИ в работно време (06.08,
# 18:36→02:03 София). В целия sent_log няма нищо между 15:36 и 23:03 UTC и
# собственикът не е разбрал. Алармата в aero-bot.yml се пали с `if: failure()`
# — тоест само при ПАДНАЛ рън. Рън, който не тръгва, не пада: най-опасният
# случай беше единственият невидим.
_сп45 = _re22.sub(r"<[^>]+>", "", lb._спал_msg(447, "2026-08-06T15:36", "2026-08-06T23:03"))
_кс45 = _re22.sub(r"<[^>]+>", "", lb._спал_msg(52, "2026-08-06T15:36", "2026-08-06T16:28"))
ck("П45 казва КОЛКО е спал, в часове и минути", "7ч 27мин" in _сп45)
ck("П45 казва ОТ КОГА ДО КОГА, по София", "18:36" in _сп45 and "02:03" in _сп45)
ck("П45 признава, че не е гледал", "не съм гледал" in _сп45)
ck("П45 е до 5 реда", len(_сп45.split(chr(10))) <= 5)
ck("П45 къса дупка се казва само в минути",
   "52 мин" in _кс45 and "ч " not in _кс45.split(chr(10))[0])
_s45 = open("live_bot.py", encoding="utf-8").read()
ck("П45 има праг с път назад", 'os.environ.get("СПАЛ_МИН", "45")' in _s45)
ck("П45 прагът е поне 3x над нормалния интервал (5 мин)", lb.СПАЛ_МИН >= 15)
ck("П45 часовникът се записва ВСЕКИ рън, не само при карта", ЧАСОВНИК45 in _s45)
ck("П45 уикендът НЕ брои за сън", "not weekend and not _market_closed(_посл)" in _s45)
ck("П45 проверката е обвита — спъне ли се, не поваля бота",
   "проверката за сън се спъна" in _s45)
# структурно: сглобява се РАНО, вкарва се СЛЕД списъка (шаблонът на спряната
# карта). Обратното — append преди списъка — държа седемте спирачки неми.
import ast as _a45
_m45 = [n for n in _a45.walk(_a45.parse(_s45))
        if isinstance(n, _a45.FunctionDef) and n.name == "main"][0]
_сгл45 = [n.lineno for n in _a45.walk(_m45) if isinstance(n, _a45.Assign)
          for t in n.targets if isinstance(t, _a45.Name) and t.id == "_спал_карта"]
_нм45 = [n.lineno for n in _a45.walk(_m45) if isinstance(n, _a45.Assign)
         for t in n.targets if isinstance(t, _a45.Name) and t.id == "new_msgs"]
_вк45 = [n.lineno for n in _a45.walk(_m45) if isinstance(n, _a45.Attribute)
         and n.attr == "append" and isinstance(n.value, _a45.Name) and n.value.id == "new_msgs"]
ck("П45 картата се сглобява ПРЕДИ списъка", bool(_сгл45) and min(_сгл45) < min(_нм45))
ck("П45 и се вкарва СЛЕД него", min(_нм45) < min(_вк45))

'''.replace("ЧАСОВНИК45", repr(_ЧАСОВНИК))

_к = "# ═══ П26 · СТОПЪТ НА КАРТАТА СЪВПАДА С НИВАТА"
assert s.count(_к) == 1
io.open(p, "wb").write(s.replace(_к, БЛОК + _к).encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("П45 добавен")
