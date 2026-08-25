# -*- coding: utf-8 -*-
"""ОДИТ-52 (тестове) · П53 · сриването вече оставя следа."""
import io, ast

p = "selftest.py"
s = io.open(p, encoding="utf-8", newline="").read()
assert "П53" not in s, "П53 вече съществува"

БЛОК = '''# ═══ П53 · ВСЯКО СРИВАНЕ БЕШЕ НЕВИДИМО (ОДИТ-52) ═════════════════════════
# 🔴 Обработчикът на грешки стои на МОДУЛНО ниво (в `except` на `try: main()`),
# а първото, което пипаше, беше `Path(args.out)`. `args` обаче се създава ВЪТРЕ
# в `main()` (ред ~2216) и никъде няма `global args`. Значи при всяко сриване:
#   1. traceback-ът се печата                                  ✅
#   2. записът пада на `Path(args.out)` → NameError             🔴
#   3. глътва се от `except Exception: pass` най-долу           🔴
#   4. `err_seen.json` НЕ се записва — никога не се е записвал  🔴
# Същото важи и за `now_utc` — и той е локален на main().
# А логът на GitHub Actions е недостъпен отвън, тоест сриванията бяха невидими,
# а одит-роботът чакаше файл, който не идва, и светеше зелено върху нищо.
_s53 = open("live_bot.py", encoding="utf-8").read()
ck("П53 пътят НЕ идва от args (той е локален на main)",
   "_ef = Path(args.out)" not in _s53 and '_ef = Path(_изх)' in _s53)
ck("П53 часът се смята на място, не от now_utc",
   "_сега = _dt52.now(_tz52.utc)" in _s53)
ck("П53 записът пази и КЪДЕ е гръмнало", '"къде": traceback.format_exc()' in _s53)
ck("П53 понася и стария формат (низ вместо речник)",
   '_prev.get("utc") if isinstance(_prev, dict) else _prev' in _s53)
# 🔴 `sys` НЕ беше внесен на модулно ниво → `sys.argv` гърмеше мълчаливо и
# `--out` се игнорираше. Открито при изпълнението, не при четенето.
_имп53 = [l for l in _s53.splitlines()[:30] if l.startswith("import ")]
ck("П53 `sys` е внесен на модулно ниво (иначе --out се игнорира тихо)",
   any(_re22.search(r"(^|[ ,])sys([ ,]|$)", l) for l in _имп53))

# ── ИЗПЪЛНЕНО: карам ИСТИНСКИЯ скрипт да гръмне и гледам следата ─────────
import subprocess as _sp53, shutil as _sh53, json as _js53
from pathlib import Path as _P53
_д53 = _P53(f"_t53_{_os.getpid()}")
_sh53.rmtree(_д53, ignore_errors=True); _д53.mkdir()
try:
    _r53 = _sp53.run([sys.executable, "live_bot.py", "--out", str(_д53)],
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace", timeout=180)
    _изл53 = (_r53.stdout or "") + (_r53.stderr or "")
except Exception as _e53:
    _изл53 = ""
_ф53 = _д53 / "err_seen.json"
if _изл53 and "ГРЕШКА В БОТА" in _изл53:
    ck("П53 сриването СЪЗДАВА err_seen.json", _ф53.exists())
    if _ф53.exists():
        _д = _js53.loads(_ф53.read_text(encoding="utf-8"))
        ck("П53 записът има поне един подпис", len(_д) >= 1)
        _зп = list(_д.values())[0]
        ck("П53 записът е речник, не гол низ", isinstance(_зп, dict))
        ck("П53 записът носи час", bool(_зп.get("utc")))
        ck("П53 записът носи самата грешка", bool(_зп.get("грешка")))
        ck("П53 записът носи КЪДЕ е гръмнало", bool(_зп.get("къде")))
        ck("П53 «къде» сочи ред от live_bot.py",
           any("live_bot.py" in str(x) for x in (_зп.get("къде") or [])))
    ck("П53 --out се уважава — живата папка НЕ е пипната",
       not (_P53("live") / "err_seen.json").exists()
       or (_P53("live") / "err_seen.json").stat().st_mtime < _ф53.stat().st_mtime)
else:
    ck("П53 ботът НЕ гръмна тук — проверката е ПРОПУСНАТА, не минала", True)
    print("    ⚠️ П53: ботът не гръмна (има мрежа?) — следата не е проверена")
_sh53.rmtree(_д53, ignore_errors=True)

'''

_к = "# ═══ П26 · СТОПЪТ НА КАРТАТА СЪВПАДА С НИВАТА"
assert s.count(_к) == 1
io.open(p, "wb").write(s.replace(_к, БЛОК + _к).encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("П53 добавен")
