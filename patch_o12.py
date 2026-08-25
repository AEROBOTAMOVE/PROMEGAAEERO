# -*- coding: utf-8 -*-
"""
ГЕНЕРАЛЕН ПЛАН · О12 · СТЪЛБАТА 1/3 ПОЛЗВА НИВОТО, НЕ ПОПЪЛВАНЕТО

`track_trade` ЗНАЕ реалната цена на попълване — при гап `px = round(op, 3)`
вместо `lv[k]`, точно затова е писано. Но я слага само в събитието и я
изхвърля: в сделката остава единствено `trade["hit"][k] = True`.
После `_ladder_pnl` смята прибраните трети по `lv[k2]` — по НИВОТО.

Значи при гап през целта реалният фил е ПО-ДОБЪР от нивото, а картата показва
нивото. Греши в безопасната посока (подценява печалба), но е грешно и се
трупа: три цели × всеки гап.

ПОПРАВКА: цената на попълване се пази в `trade["hit_px"]` и стълбата я
предпочита. Обратно съвместимо — сделка без `hit_px` смята точно както досега.
"""
import io, sys, ast, hashlib

ops = []


def rep(p, old, new, why, n=1):
    s = io.open(p, encoding="utf-8", newline="").read()
    c = s.count(old)
    if c != n:
        print(f"  x СПИРАМ «{why}»: {c} съвпадения, чакам {n}\n    {old[:130]!r}")
        sys.exit(1)
    io.open(p, "wb").write(s.replace(old, new).encode("utf-8"))
    ops.append(why)


LB = "live_bot.py"

# ── 1 · попълването се ПАЗИ ───────────────────────────────────────────────
rep(LB, '''                    trade["hit"][k] = True; events.append((k, px, str(ts), "бар", gap))''',
    '''                    # 🔧 О12 · ПАЗИМ И ЦЕНАТА НА ПОПЪЛВАНЕ, не само че е ударена.
                    # При гап `px` е цената на ОТВАРЯНЕТО — по-добра от нивото.
                    # Дотук се изхвърляше и стълбата смяташе по НИВОТО, тоест
                    # подценяваше печалбата при всеки гап през цел.
                    trade["hit"][k] = True
                    trade.setdefault("hit_px", {})[k] = px
                    events.append((k, px, str(ts), "бар", gap))''',
    "1 · попълването се пази")

# ── 2 · стълбата го предпочита ────────────────────────────────────────────
rep(LB, '''def _ladder_pnl(kind, hit, lv, entry, sign, dol):''',
    '''def _ladder_pnl(kind, hit, lv, entry, sign, dol, hit_px=None):''',
    "2 · стълбата приема попълванията")

rep(LB, '''    for k2 in ("tp1", "tp2"):
        if hit.get(k2) and k2 != kind:
            thirds += (lv[k2] - entry) * sign / 3.0
            n_hit += 1''',
    '''    for k2 in ("tp1", "tp2"):
        if hit.get(k2) and k2 != kind:
            # 🔧 О12: реалното попълване, ако го знаем; иначе нивото (както досега).
            # Сделка отпреди тази версия няма `hit_px` → смята се точно както преди.
            _ц = (hit_px or {}).get(k2)
            thirds += ((float(_ц) if _ц is not None else lv[k2]) - entry) * sign / 3.0
            n_hit += 1''',
    "2 · предпочита попълването")

# ── 3 · подава се от двата извикващи ──────────────────────────────────────
s = io.open(LB, encoding="utf-8", newline="").read()
n = s.count("_ladder_pnl(kind, hit, lv, e, sign, dol)")
if n:
    s = s.replace("_ladder_pnl(kind, hit, lv, e, sign, dol)",
                  '_ladder_pnl(kind, hit, lv, e, sign, dol, tr.get("hit_px"))')
    io.open(LB, "wb").write(s.encode("utf-8"))
    ops.append(f"3 · подадено на {n} места (tr)")
s = io.open(LB, encoding="utf-8", newline="").read()
n2 = s.count("_ladder_pnl(kind, hit, lv, entry, sign, dol)")
if n2:
    s = s.replace("_ladder_pnl(kind, hit, lv, entry, sign, dol)",
                  "_ladder_pnl(kind, hit, lv, entry, sign, dol, hit_px)")
    io.open(LB, "wb").write(s.encode("utf-8"))
    ops.append(f"3 · подадено на {n2} места (entry)")

# ── 4 · кумулативните попълвания в снимката ───────────────────────────────
rep(LB, '''        cum_hit = dict(trade_obj["hit"])                   # попадения от МИНАЛИ рънове
        for kind, px, when, via, gap in events:
            if kind in ("tp1", "tp2", "tp3"):              # това попадение стана ТОЗИ рън → трупай
                cum_hit[kind] = True''',
    '''        cum_hit = dict(trade_obj["hit"])                   # попадения от МИНАЛИ рънове
        cum_px = dict(trade_obj.get("hit_px") or {})       # О12: и цените им
        for kind, px, when, via, gap in events:
            if kind in ("tp1", "tp2", "tp3"):              # това попадение стана ТОЗИ рън → трупай
                cum_hit[kind] = True
                cum_px[kind] = px                          # О12: реалният фил, гап-съобразен''',
    "4 · кумулативни попълвания")

rep(LB, '''            obj = dict(trade_obj); obj["hit"] = dict(cum_hit)''',
    '''            obj = dict(trade_obj); obj["hit"] = dict(cum_hit); obj["hit_px"] = dict(cum_px)''',
    "4 · снимката ги носи")

print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
ast.parse(io.open(LB, encoding="utf-8").read())
b = io.open(LB, encoding="utf-8").read()
print(f"{LB}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
print("\nвикания на _ladder_pnl:")
for i, l in enumerate(b.splitlines(), 1):
    if "_ladder_pnl(" in l:
        print(f"  {i}: {l.strip()[:96]}")
