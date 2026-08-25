# -*- coding: utf-8 -*-
"""
ОДИТ-50 · ПОЩАТА ИЗЯЖДАШЕ ПОВРЕДЕН РЕД МЪЛЧАЛИВО

    for ln in ob_f.read_text(...).splitlines():
        try:
            pending.append(json.loads(ln))
        except Exception:
            pass                      ← ето тук

Повреден ред изчезва БЕЗ СЛЕД. А редът може да е изходна карта («🛑 СТОПЪТ
удари»), тоест пари, които вече са на риск — точно класът съобщения, за които
целият останал код прави изключения (EXIT_TAGS не се трият дори при 3 твърди
провала от Телеграм).

И начинът, по който файлът се пише, ГО ПРАВИ ВЕРОЯТНО:
    ob_f.write_text("\\n".join(json.dumps(m) for m in remaining))
Умре ли процесът по средата на записа (Actions има таймаут от 8 минути),
последният ред остава отрязан → на следващия рън се яде мълчаливо.

ПОПРАВКА, три неща:
 1 · повредените редове се БРОЯТ и се казват в дневника
 2 · суровият текст отива в `outbox_broken.jsonl` — нищо не се губи безвъзвратно
 3 · съдържа ли повреденият ред дума от изходна карта, това е ЧЕРВЕНО, не бележка
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

rep('''    if ob_f.exists():
        for ln in ob_f.read_text(encoding="utf-8").splitlines():
            try:
                pending.append(json.loads(ln))
            except Exception:
                pass''',
    '''    if ob_f.exists():
        # 🔴 ОДИТ-50 · ДОТУК ТУК СТОЕШЕ `except Exception: pass` — повреден ред
        # изчезваше БЕЗ СЛЕД. А редът може да е изходна карта («🛑 СТОПЪТ удари»),
        # тоест пари вече на риск — класът, който целият останал код пази изрично.
        # И записът с `"\\n".join(...)` го прави вероятно: умре ли процесът по
        # средата (Actions има таймаут 8 мин), последният ред остава отрязан.
        _счуп = []
        for ln in ob_f.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                pending.append(json.loads(ln))
            except Exception:
                _счуп.append(ln)
        if _счуп:
            # нищо не се губи безвъзвратно — суровият текст отива настрана
            try:
                with (out_dir / "outbox_broken.jsonl").open("a", encoding="utf-8") as _bf:
                    for _l in _счуп:
                        _bf.write(json.dumps({"utc": now_iso, "raw": _l[:4000]},
                                             ensure_ascii=False) + "\\n")
            except Exception:
                pass
            _пари = [l for l in _счуп
                     if any(t in l for t in EXIT_TAGS) or "СТОПЪТ" in l or "ТП" in l]
            if _пари:
                statuses.append(f"🔴 {len(_пари)} ПОВРЕДЕНИ реда в пощата приличат на "
                                f"ИЗХОДНА карта — виж outbox_broken.jsonl")
            else:
                statuses.append(f"⚠️ {len(_счуп)} повредени реда в пощата — "
                                f"запазени в outbox_broken.jsonl")''',
    "пощата брои и пази повреденото")

io.open(p, "wb").write(s.encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
b = io.open(p, encoding="utf-8").read()
print(f"{p}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
