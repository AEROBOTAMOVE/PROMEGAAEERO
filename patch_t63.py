# -*- coding: utf-8 -*-
"""ОДИТ-68 (тестове) · П63 · мъртъв код не се трупа + паричният път не мълчи."""
import io, ast
p = "selftest.py"
s = io.open(p, encoding="utf-8", newline="").read()
assert "П63" not in s

БЛОК = '''# ═══ П63 · МЪРТЪВ КОД И ТИХИ ПАРИЧНИ ПЪТИЩА (ОДИТ-68) ════════════════════
# Днес намерих ЧЕТИРИ мъртви неща (`_pct`, `_ci`, `_cq_clusters_line`,
# `МОЗЪК_РИСК_W`) и една константа-призрак преди тях (`ОПАШКА_ТАВАН`, v9.8).
# Това е ШАБЛОН, не случайност: пипам нещо, старото остава, никой не забелязва.
# Този тест брои мъртвите по AST и пада, ако станат повече от днешния брой.
import ast as _a63
_д63 = _a63.parse(open("live_bot.py", encoding="utf-8").read())
_вик63 = set()
for _n63 in _a63.walk(_д63):
    if isinstance(_n63, _a63.Call):
        _f63 = _n63.func
        if isinstance(_f63, _a63.Name):
            _вик63.add(_f63.id)
        elif isinstance(_f63, _a63.Attribute):
            _вик63.add(_f63.attr)
# име, подадено като СТОЙНОСТ (напр. `("лихви", _rates)`), също се брои за ползвано
for _n63 in _a63.walk(_д63):
    if isinstance(_n63, _a63.Name) and isinstance(_n63.ctx, _a63.Load):
        _вик63.add(_n63.id)
_деф63 = {n.name for n in _a63.walk(_д63) if isinstance(n, _a63.FunctionDef)}
_мърт63 = sorted(_деф63 - _вик63 - {"main"})
ck(f"П63 няма мъртви функции {_мърт63}", not _мърт63)

_имена63 = {n.id for n in _a63.walk(_д63)
            if isinstance(n, _a63.Name) and isinstance(n.ctx, _a63.Load)}
_нас63 = _re22.findall(r"^([А-Я_A-Z0-9]+)\s*=\s*.*os\.environ\.get", _s22, _re22.M) \
    if False else _re22.findall(r"(?m)^([А-Я_A-Z0-9]+)\s*=\s*.*os\.environ\.get",
                                open("live_bot.py", encoding="utf-8").read())
_мъртн63 = sorted(set(_нас63) - _имена63)
ck(f"П63 няма настройки-призраци {_мъртн63}", not _мъртн63)
ck(f"П63 настройките са поне 20 (не са изтрити наведнъж)", len(_нас63) >= 20)

# 🔴 ЕДИНСТВЕНИЯТ ИСТИНСКИ ТИХ ПАРИЧЕН ПЪТ, намерен днес — и той беше мой (v11.7)
_н63 = []
ck("П63 счупена сделка ОСТАВЯ следа, не мълчи",
   lb._отворена_стълба({"direction": "long"}, {"mid": 4400}, _н63) == (None, 0)
   and any("стълбата гръмна" in str(x) for x in _н63))
_н63б = []
_tr63 = {"direction": "long", "entry": 4400.0, "hit": {"tp1": True},
         "levels": {"tp1": 4407.5, "tp2": 4412.0, "tp3": 4420.0, "sl": 4400.0}}
ck("П63 здрава сделка НЕ вдига фалшива тревога",
   lb._отворена_стълба(_tr63, {"mid": 4404.0}, _н63б)[0] is not None and not _н63б)
ck("П63 и без тефтер не гърми", lb._отворена_стълба(_tr63, {"mid": 4404.0})[0] is not None)
ck("П63 трите карти подават тефтера",
   open("live_bot.py", encoding="utf-8").read().count("_отворена_стълба(tr, sp,") == 3)

# 🟢 ЗАПИСАНО ЗА ИСТОРИЯТА: `CHART_BRAIN_ON` НЕ Е мъртъв — моята находка беше
# грешна. Ред 169 го ползва реално; ИЗПЪЛНЕНО: CHART_BRAIN=0 → CB=None.
ck("П63 изключвателят на мозъка Е вързан", "if CHART_BRAIN_ON:" in
   open("live_bot.py", encoding="utf-8").read())

'''
_к = "# ═══ П26 · СТОПЪТ НА КАРТАТА СЪВПАДА С НИВАТА"
assert s.count(_к) == 1
io.open(p, "wb").write(s.replace(_к, БЛОК + _к).encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("П63 добавен")
