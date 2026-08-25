# -*- coding: utf-8 -*-
"""
ОДИТ-52 · ВСЯКО СРИВАНЕ НА БОТА Е БИЛО НЕВИДИМО

Находка на армията, ПРОВЕРЕНА ЛИЧНО с изпълнение.

Обработчикът на грешки стои на МОДУЛНО ниво (в `except` на `try: main()`), а
първото, което пипа, е `Path(args.out)`. `args` обаче се създава ВЪТРЕ в
`main()` на ред 2216 и никъде няма `global args`.

Значи при всяко сриване:
  1. traceback-ът се печата                                    ✅
  2. записът пада на `Path(args.out)` → NameError              🔴
  3. глътва се от `except Exception: pass` най-долу            🔴
  4. `err_seen.json` НЕ се записва — никога не се е записвал   🔴

Същото важи и за `now_utc` — и той е локален на `main()`.

А дневникът на GitHub Actions е недостъпен отвън (собствената ми бележка от
11.08: «черната кутия — пиши диагностиката в тефтера»). Тоест единственият
външен запис за сриване не е съществувал, а одит-роботът е чакал файл, който
никога не идва — и е светел зелено върху нищо.

ПОПРАВКА: обработчикът вече не зависи от локалните на `main()`. Пътят се чете
от sys.argv (със същия дефолт «live»), часът се смята на място. Освен това
записва и САМИЯ traceback, не само подписа — при сриване искаш да видиш КЪДЕ.
"""
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

rep('''            _sig = _hashlib_e.sha1(f"{type(e).__name__}:{str(e)[:120]}".encode()).hexdigest()[:12]
            _ef = Path(args.out) / "err_seen.json"''',
    '''            _sig = _hashlib_e.sha1(f"{type(e).__name__}:{str(e)[:120]}".encode()).hexdigest()[:12]
            # 🔴 ОДИТ-52 · ТУК ПИШЕШЕ `Path(args.out)`. `args` се създава ВЪТРЕ в
            # `main()` и няма `global args` — значи ЦЕЛИЯТ този блок падаше на
            # NameError при всяко сриване и се глътваше от `except: pass` долу.
            # `err_seen.json` НИКОГА не се е записвал; одит-роботът е чакал файл,
            # който не идва, и е светел зелено върху нищо. А логът на Actions е
            # недостъпен отвън — тоест всяко сриване беше невидимо.
            # Сега пътят се чете от sys.argv, без да зависи от локалните на main().
            _изх = "live"
            try:
                _av = sys.argv
                if "--out" in _av and _av.index("--out") + 1 < len(_av):
                    _изх = _av[_av.index("--out") + 1]
            except Exception:
                pass
            _ef = Path(_изх) / "err_seen.json"''',
    "1 · пътят не зависи от main()")

rep('''                try:
                    _fresh = (pd.Timestamp(now_utc) - pd.Timestamp(_prev)).total_seconds() > 3 * 3600
                except Exception:
                    _fresh = True''',
    '''                try:
                    # ОДИТ-52: `now_utc` също е локален на main() — смятаме го тук.
                    _fresh = (pd.Timestamp(_сега) - pd.Timestamp(_prev)).total_seconds() > 3 * 3600
                except Exception:
                    _fresh = True''',
    "2 · часът не зависи от main()")

rep('''            _seen[_sig] = str(now_utc)''',
    '''            # ОДИТ-52: пазим и КЪДЕ е гръмнало — при сриване подписът сам по себе
            # си не стига, а логът на Actions е недостъпен отвън.
            _seen[_sig] = {"utc": str(_сега), "грешка": _err[:200],
                           "къде": traceback.format_exc().strip().splitlines()[-3:]}''',
    "3 · пази и къде е гръмнало")

rep('''            import html as _html
            _err = _html.escape(f"{type(e).__name__}: {str(e)[:250]}")''',
    '''            import html as _html
            from datetime import datetime as _dt52, timezone as _tz52
            _сега = _dt52.now(_tz52.utc).replace(tzinfo=None).isoformat(timespec="seconds")
            _err = _html.escape(f"{type(e).__name__}: {str(e)[:250]}")''',
    "4 · часът се смята на място")

# старите записи са низове, новите са речници — четенето трябва да понесе двете
rep('''                _fresh = (pd.Timestamp(_сега) - pd.Timestamp(_prev)).total_seconds() > 3 * 3600''',
    '''                _пв = _prev.get("utc") if isinstance(_prev, dict) else _prev
                _fresh = (pd.Timestamp(_сега) - pd.Timestamp(_пв)).total_seconds() > 3 * 3600''',
    "5 · понася и стария формат")

io.open(p, "wb").write(s.encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
b = io.open(p, encoding="utf-8").read()
print(f"{p}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
