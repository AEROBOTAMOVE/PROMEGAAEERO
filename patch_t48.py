# -*- coding: utf-8 -*-
"""О8/О11 (тестове) · П46 пази резерва на макрото и чистенето на архива."""
import io, ast

p = "selftest.py"
s = io.open(p, encoding="utf-8", newline="").read()
assert "П46" not in s, "П46 вече съществува"

БЛОК = '''# ═══ П46 · РЕЗЕРВ ЗА МАКРОТО + ХИГИЕНА (О8/О11) ══════════════════════════
# О8: един хълцук на Yahoo сваляше цялото макро-краче, а О1 при мъртво краче
# СПИРА новите входове — тоест едно мигване = час без входове. Лихвите имаха
# резерв (FRED пази), Yahoo нямаше. Сега последната ДОБРА стойност се пази.
_s46 = open("live_bot.py", encoding="utf-8").read()
ck("П46 има праг за възрастта на резерва", 'os.environ.get("СТАР_МАКРО_Ч", "36")' in _s46)
ck("П46 резервът се ЗАПИСВА при успех", 'macro_backup.json' in _s46
   and '_бек[_име] = {"utc": now_utc' in _s46)
ck("П46 резервът се ЧЕТЕ при провал", '_рез = (_load_state(out / "macro_backup.json"' in _s46)
ck("П46 стар резерв НЕ се ползва — казва «не виждам»", "_въз <= СТАР_МАКРО_Ч" in _s46)
ck("П46 ползването на резерв се КАЗВА в дневника", "карам на резерва" in _s46)
ck("П46 провалът пак спира входовете, ако няма резерв",
   "if not _взет:" in _s46 and "_макро_мъртво.append(_име)" in _s46)

# ── ИЗПЪЛНЕНО, не грепнато: оцелява ли рамката през запис/четене ─────────
import io as _io46
_idx46 = _pd22.date_range("2026-06-01", periods=120, freq="D")
_df46 = _pd22.DataFrame({"Open": _np22.linspace(40, 50, 120),
                         "High": _np22.linspace(41, 51, 120),
                         "Low": _np22.linspace(39, 49, 120),
                         "Close": _np22.linspace(40.5, 50.5, 120)}, index=_idx46)
_кръг46 = _pd22.read_json(_io46.StringIO(_df46.tail(120).to_json(orient="split")), orient="split")
_кръг46.index = _pd22.to_datetime(_кръг46.index)
ck("П46 рамката (GDX/DXY) оцелява през резерва",
   _кръг46.shape == _df46.shape
   and abs(float(_кръг46["Close"].iloc[-1]) - float(_df46["Close"].iloc[-1])) < 1e-6)
_с46 = _pd22.Series(_np22.linspace(1.9, 2.1, 120), index=_idx46)
_кр46 = _pd22.read_json(_io46.StringIO(_с46.tail(120).to_frame("rate").to_json(orient="split")),
                        orient="split")
_кр46.index = _pd22.to_datetime(_кр46.index)
_rr46 = _кр46["rate"] if "rate" in _кр46 else _кр46.iloc[:, 0]
ck("П46 серията (лихви) оцелява през резерва",
   abs(float(_rr46.iloc[-1]) - float(_с46.iloc[-1])) < 1e-6)
_g46 = _pd22.DataFrame({"Close": _np22.linspace(4300, 4400, 120),
                        "High": _np22.linspace(4310, 4410, 120),
                        "Low": _np22.linspace(4290, 4390, 120)}, index=_idx46)
try:
    _m46 = lb._macro(_g46, _кръг46, _кръг46, _rr46)
    _st46 = lb._streaks(_g46, _кръг46, _кръг46, _rr46)
    _ок46 = isinstance(_m46, dict) and set(_m46) == {"миньори", "долар", "лихви"} \\
        and isinstance(_st46, dict)
except Exception:
    _ок46 = False
ck("П46 макрото и стрийкът РАБОТЯТ с възстановените данни", _ок46)

# ── О11 · хигиена ────────────────────────────────────────────────────────
# Мерено: POISON_ATTEMPTS вече го няма ✅ · outbox 0 реда ✅ · archive 3352 KB
# за ЕДИН месец в git repo → ~40 MB/година.
ck("П46 POISON_ATTEMPTS е махнат (коментарът лъжеше)", "POISON_ATTEMPTS" not in _s46)
ck("П46 архивът има таван в месеци", 'os.environ.get("АРХИВ_МЕСЕЦИ", "3")' in _s46)
ck("П46 чистенето пази ПОСЛЕДНИТЕ месеци, не първите",
   "sorted(_по_месец)[:-АРХИВ_МЕСЕЦИ]" in _s46)
ck("П46 чистенето се КАЗВА в дневника", "архивът от" in _s46)
ck("П46 чистенето е обвито", "чистенето на архива се спъна" in _s46)
ck("П46 АРХИВ_МЕСЕЦИ=0 изключва чистенето", "if АРХИВ_МЕСЕЦИ > 0:" in _s46)
ck("П46 опашката има таван", 'os.environ.get("ОПАШКА_ТАВАН", "200")' in _s46)

'''

_к = "# ═══ П26 · СТОПЪТ НА КАРТАТА СЪВПАДА С НИВАТА"
assert s.count(_к) == 1
io.open(p, "wb").write(s.replace(_к, БЛОК + _к).encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("П46 добавен")
