# -*- coding: utf-8 -*-
"""
ОДИТ-55 · САНИТИТО ОТРЯЗВА 12.4% ОТ ЖИВИТЕ ЦЕНИ — И НЕ КАЗВА ЗАЩО

ИЗМЕРЕНО на 2158 живи ръна:
    267 (12.4%) имат `spot_rejected: True` — суровата цена Е БИЛА жива и
    санитито я е отрязало. В същите 267 `spot_src` е None, тоест ботът е карал
    БЕЗ жива цена, а тогава `_advice_entry(stale_price=True)` връща ok=False и
    входовете спират.
    Спотът е на 0.2 секунди (медиана), барът — на 10 минути (медиана).

Армията твърди, че причината е сравнението на 0.2-секундна котировка срещу
10-минутен бар. ПРОВЕРИХ И НЕ ГО ПОТВЪРЖДАВАМ: медианата на възрастта на бара
е ЕДНАКВА при отхвърлени и приети (10.0 срещу 10.0 мин). Значи механизмът е
друг или е по-фин.

НЕ ПИПАМ ПРАГ, КОЙТО ПАЗИ ПАРИ, ПО ДОГАДКА. Този праг съществува, защото един
$100 глич минаваше сам (виж коментара F2 в кода). Разхлабя ли го наслуки, може
да пусна точно него.

ЗАТОВА: инструментирам. `_spot_sane` вече записва КОЛКО е бил разминат и
КАКЪВ е бил допускът, при всяко отхвърляне. След ден-два числата ще кажат
точно дали допускът е тесен, и с колко — вместо аз да гадая сега.

Това е стъпката, която липсваше: 267 отхвърляния за девет дни, и НИТО ЕДНО
не остави следа защо.
"""
import io, sys, ast, hashlib

ops = []


def rep(old, new, why, n=1):
    global s
    c = s.count(old)
    if c != n:
        print(f"  x СПИРАМ «{why}»: {c} съвпадения, чакам {n}\n    {old[:150]!r}")
        sys.exit(1)
    s = s.replace(old, new)
    ops.append(why)


p = "live_bot.py"
s = io.open(p, encoding="utf-8", newline="").read()

rep('''def _spot_sane(spot, reference, base_diff, bar_rng=None, spot_jump=None):''',
    '''def _spot_sane(spot, reference, base_diff, bar_rng=None, spot_jump=None, следа=None):''',
    "1 · приема следа")

rep('''    return spot if abs(reference - spot["mid"]) <= tol else None''',
    '''    # 🔴 ОДИТ-55 · КОГА И С КОЛКО Е ОТРЯЗАНО. Измерено: 267 от 2158 ръна (12.4%)
    # губят живата цена ТУК, и нито едно не оставя следа защо. Без това число
    # не може да се каже дали допускът е тесен — а прагът пази пари (един $100
    # глич минаваше сам, виж F2), значи не се пипа по догадка. Първо мерим.
    _разлика = abs(reference - spot["mid"])
    if следа is not None:
        следа.update({"разлика": round(float(_разлика), 3), "допуск": round(float(tol), 3),
                      "база": round(float(base_diff), 3),
                      "диапазон": (round(float(bar_rng), 3) if bar_rng else None),
                      "скок": (round(float(spot_jump), 3) if spot_jump else None),
                      "мина": bool(_разлика <= tol)})
    return spot if _разлика <= tol else None''',
    "2 · записва разликата и допуска")

rep('''    spot_g = _spot_sane(raw_g, bar_price - basis_g, 8.0, bar_rng=rng_g, spot_jump=jump_g)
    spot_rejected_g = bool(raw_g is not None and spot_g is None)   # A2: суровият беше жив, санитито го отряза''',
    '''    _сан_g = {}
    spot_g = _spot_sane(raw_g, bar_price - basis_g, 8.0, bar_rng=rng_g, spot_jump=jump_g,
                        следа=_сан_g)
    spot_rejected_g = bool(raw_g is not None and spot_g is None)   # A2: суровият беше жив, санитито го отряза
    if spot_rejected_g and _сан_g:
        # ОДИТ-55: казваме КОЛКО е разминато и КАКЪВ е бил допускът — за да може
        # после да се измери дали прагът е тесен, вместо да се гадае.
        notes.append(f"🟡 живата цена отрязана: разминава с {_сан_g['разлика']:.2f}$ "
                     f"при допуск {_сан_g['допуск']:.2f}$ "
                     f"(база {_сан_g['база']:.0f} · диапазон {_сан_g['диапазон']} "
                     f"· скок {_сан_g['скок']})")''',
    "3 · златото го казва")

rep('''                             "spot_src": (spot_g or {}).get("src"), "spot_rejected": spot_rejected_g,''',
    '''                             "spot_src": (spot_g or {}).get("src"), "spot_rejected": spot_rejected_g,
                             "saniti": (_сан_g or None),   # ОДИТ-55: разлика/допуск за после''',
    "4 · влиза в дневника")

io.open(p, "wb").write(s.encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
b = io.open(p, encoding="utf-8").read()
print(f"{p}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
