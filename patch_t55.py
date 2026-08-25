# -*- coding: utf-8 -*-
"""ОДИТ-50 (тестове) · П52 · пощата не яде мълчаливо."""
import io, ast

p = "selftest.py"
s = io.open(p, encoding="utf-8", newline="").read()
assert "П52" not in s, "П52 вече съществува"

БЛОК = '''# ═══ П52 · ПОЩАТА НЕ ЯДЕ ПОВРЕДЕН РЕД МЪЛЧАЛИВО (ОДИТ-50) ════════════════
# 🔴 ДОТУК ТАМ СТОЕШЕ `except Exception: pass` — повреден ред изчезваше БЕЗ
# СЛЕД. А редът може да е изходна карта («🛑 СТОПЪТ удари»), тоест пари вече на
# риск — точно класът, който целият останал код пази изрично (EXIT_TAGS не се
# трият дори при 3 твърди провала от Телеграм).
# И начинът на запис го прави ВЕРОЯТНО: `"\\n".join(...)` — умре ли процесът по
# средата (Actions има таймаут 8 мин), последният ред остава отрязан.
_s52 = open("live_bot.py", encoding="utf-8").read()
ck("П52 повредените редове се БРОЯТ", "_счуп.append(ln)" in _s52)
ck("П52 суровият текст се ПАЗИ", "outbox_broken.jsonl" in _s52)
ck("П52 изходна карта вдига ЧЕРВЕНО, не бележка",
   "приличат на " in _s52 and "ИЗХОДНА карта" in _s52)
ck("П52 празните редове не се броят за счупени", 'if not ln.strip():' in _s52)

# ── ИЗПЪЛНЕНО: опашка с два ОТРЯЗАНИ реда, както при убит процес ─────────
import shutil as _sh52, json as _js52
from pathlib import Path as _P52
_д52 = _P52(f"_t52_{_os.getpid()}")
_sh52.rmtree(_д52, ignore_errors=True); _д52.mkdir()
(_д52 / "outbox.jsonl").write_text(
    _js52.dumps({"tag": "pulse", "text": "здрав", "first_ts": "2026-08-12T09:00",
                 "attempts": 0}, ensure_ascii=False) + chr(10)
    + '{"tag": "exit:sl", "text": "СТОПЪТ уд' + chr(10)
    + '{"tag": "pulse", "text": "отря', encoding="utf-8")
_ст52 = []
lb._outbox_flush(_д52, [], _ст52, dry=True)
_т52 = chr(10).join(_ст52)
ck("П52 отрязаната ИЗХОДНА карта вдига червено", "🔴" in _т52 and "ИЗХОДНА карта" in _т52)
ck("П52 счупеното е запазено на диска", (_д52 / "outbox_broken.jsonl").exists())
_бр52 = sum(1 for _ in io.open(_д52 / "outbox_broken.jsonl", encoding="utf-8"))
ck(f"П52 и ДВАТА счупени реда са запазени ({_бр52})", _бр52 == 2)
_ост52 = sum(1 for l in io.open(_д52 / "outbox.jsonl", encoding="utf-8") if l.strip())
ck(f"П52 здравият ред ОЦЕЛЯВА ({_ост52})", _ост52 == 1)
# и обратната посока: чиста опашка не вика вълк
(_д52 / "outbox.jsonl").write_text(
    _js52.dumps({"tag": "pulse", "text": "здрав", "first_ts": "2026-08-12T09:00",
                 "attempts": 0}, ensure_ascii=False), encoding="utf-8")
(_д52 / "outbox_broken.jsonl").unlink(missing_ok=True)
_ст52б = []
lb._outbox_flush(_д52, [], _ст52б, dry=True)
ck("П52 чиста опашка НЕ вдига тревога",
   not any("повредени" in x or "ИЗХОДНА карта" in x for x in _ст52б))
_sh52.rmtree(_д52, ignore_errors=True)

'''

_к = "# ═══ П26 · СТОПЪТ НА КАРТАТА СЪВПАДА С НИВАТА"
assert s.count(_к) == 1
io.open(p, "wb").write(s.replace(_к, БЛОК + _к).encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("П52 добавен")
