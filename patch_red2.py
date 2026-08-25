# -*- coding: utf-8 -*-
"""
ОДИТ-68 · РЕД 2 ОТ ПЛАНА — след като проверих всяко твърдение

🟢 ОТПАДА · `CHART_BRAIN_ON` РАБОТИ. Моята находка беше ГРЕШНА.
   Скенерът броеше срещания на името и намери 2, реши че е само декларация.
   Ред 169 обаче го ползва реално: `if CHART_BRAIN_ON:` пази вноса на мозъка.
   ИЗПЪЛНЕНО: CHART_BRAIN=0 → CB=None → мозъкът СПРЯН. Изключвателят работи.
   Добре че проверих с изпълнение — иначе щях да «поправям» работещо.

🟢 ОТПАДАТ 5 от 8 · ТИХИТЕ ГЪЛТАЧИ ПО ПЪТЯ НА ПАРИТЕ.
   Проверих всеки поотделно: `_send_raw` (2092, 2114) и `_outbox_flush` (2236,
   2153) НЕ мълчат — те докладват през ВРЪЩАНА СТОЙНОСТ (`last`, `st`, `_счуп`),
   а скенерът ми търсеше само `notes`/`statuses`/`print`. Лъжливи находки.

🔴 ОСТАВА 1 · `_отворена_стълба` МЪЛЧИ НАИСТИНА — и е моя от v11.7
   `except Exception: return None, 0` → счупи ли се сметката по стълбата,
   картата просто НЕ показва пари и никой не разбира. Три карти зависят от
   нея: равносметката, «КЪДЕ СМЕ» и пулсът.

🔴 ОСТАВАТ 4 МЪРТВИ · `_pct`, `_ci`, `_cq_clusters_line`, `МОЗЪК_РИСК_W`
   Проверено по AST (не по броене): нито едно не се вика/чете никъде.
   `_pct` и `_ci` са форматиращи за проценти и интервали по картите — картите
   вече не цитират статистика по изрично указание («ФАКТ да, ОБЯСНЕНИЕ не»).
   `_cq_clusters_line` е ред за крипто-клъстери, махнат при телеграфа.
   `МОЗЪК_РИСК_W` остана след махането на лотовете.
   ВАЖНО: `_noise()`, който ползва СЪЩИТЕ lo/hi, ОСТАВА — той е пазачът срещу
   шум и се вика. Маха се само текстовият формат, не логиката.
"""
import io, sys, ast, hashlib

ops = []
p = "live_bot.py"
s = io.open(p, encoding="utf-8", newline="").read()


def rep(old, new, why, n=1):
    global s
    c = s.count(old)
    if c != n:
        print(f"  x «{why}»: {c} съвпадения, чакам {n}\n    {old[:130]!r}")
        sys.exit(1)
    s = s.replace(old, new)
    ops.append(why)


# ═══ 1 · единственият истински тих гълтач ════════════════════════════════
rep('''def _отворена_стълба(tr, spot):''',
    '''def _отворена_стълба(tr, spot, notes=None):''',
    "1 · приема тефтер")

rep('''        return _ladder_pnl("отворена", tr.get("hit", {}) or {}, tr["levels"],
                           float(tr["entry"]), зн, ост, tr.get("hit_px"))
    except Exception:
        return None, 0''',
    '''        return _ladder_pnl("отворена", tr.get("hit", {}) or {}, tr["levels"],
                           float(tr["entry"]), зн, ост, tr.get("hit_px"))
    except Exception as _e:
        # 🔴 ОДИТ-68 · ДОТУК ТУК СТОЕШЕ ГОЛО `return None, 0`. Счупи ли се
        # сметката по стълбата, трите карти (равносметка, «КЪДЕ СМЕ», пулс)
        # просто НЕ показваха пари и никой не разбираше. Мълчание на паричен
        # път — точно класът, който днес ме ухапа три пъти.
        if notes is not None:
            notes.append(f"🔴 сметката по стълбата гръмна ({type(_e).__name__}: "
                         f"{str(_e)[:60]}) — картата е без число")
        return None, 0''',
    "1 · оставя следа")

# ═══ 2 · мъртвият код ════════════════════════════════════════════════════
rep('''def _pct(seg, label):
    """В4/В6: цитирай процент САМО ако има n≥MIN_N; иначе — без число."""
    if seg.get("n") and seg["n"] >= MIN_N and seg.get("win") is not None:
        return f": {label} {seg['win']}% · {seg['net']:+}$/oz (n={seg['n']})"
    return " (историята е малка — без число)"


''', "", "2 · махнат _pct")

rep('''def _ci(seg):
    """Интервалът в текста — за да е проверимо число, не мнение."""
    lo, hi = seg.get("lo"), seg.get("hi")
    return f" (95%: {lo:+.2f}..{hi:+.2f}$)" if lo is not None and hi is not None else ""


''', "", "2 · махнат _ci")

rep('''def _cq_clusters_line(cq):
    """Четирите клъстера като един ред. Празен низ, ако ги няма (стар кеш / провал)."""
    cl = cq.get("clusters") or {}
    parts = [f"{nm} {int(round(float(cl[k])))}" for k, nm in CQ_CLUSTERS.items()
             if cl.get(k) is not None]
    return " · ".join(parts)


''', "", "2 · махнат _cq_clusters_line")

rep('МОЗЪК_РИСК_W = float(os.environ.get("МОЗЪК_РИСК_W", "0.4"))\n', "",
    "2 · махнат МОЗЪК_РИСК_W")

io.open(p, "wb").write(s.encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
b = io.open(p, encoding="utf-8").read()
print(f"{p}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
