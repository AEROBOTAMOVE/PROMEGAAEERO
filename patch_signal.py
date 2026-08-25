# -*- coding: utf-8 -*-
"""
ОДИТ-28 · СИГНАЛНАТА КАРТА — по нея Коста влиза с пари

Старата (12 реда): заглавие с ⏰ и латиница · присъда · ПЕТ реда нива, всеки с
етикет «ТП1:» · ред «📊 СИЛЕН 6/8 · долар+лихви 2/2 ✓ подредено · УЛТРА клас:
78.2% · +2.51$/oz (n=4176)» · самотен ред «зона B» · ред за размера.

Новата (6-8 реда): КАКВО (заглавие) · ЗАЩО (един ред) · КЪДЕ (нива) ·
КОЛКО (размер). Редът «📊» пада целият — той повтаряше с числа онова, което
редът «Защо» вече казва с думи. «зона B» влиза в реда за размера.

ЕМОДЖИ-КАНОН: един знак = едно значение.
  🟢 покупка · 🔴 продажба · ⏸ не сега · 📌 бележка/тече сделка
  🎯 вход · 1️⃣2️⃣3️⃣ целите · 🛑 стопът · 💰 размерът · 👁 следя наум
Махнати: ⏰ (часът е в заглавието), 📊, 🚫, ⏳, 💵 — всяко от тях значеше
същото като нещо друго или нищо.
"""
import io, sys, hashlib, re

p = "live_bot.py"
s = io.open(p, encoding="utf-8", newline="").read()
assert "def _sig_msg(" in s

i = s.index("def _sig_msg(")
j = s.index("\ndef ", i + 10)
старо = s[i:j]
assert len(старо) > 3000, len(старо)

ново = '''def _sig_msg(direction, score, agree_n, tier_name, spot, bar_price, bar_ts, lv, entry,
             advice_txt, macro, streak_n, regime, stats, balance, risk_pct, weekly=None,
             reentry=False, open_trade=None, sym="XAUUSD", dec=2, extra_ctx=None, adv_ok=True,
             shadow_on=None, zone=None):
    """ОДИТ-28: КАКВО · ЗАЩО · КЪДЕ · КОЛКО. Нищо друго.

    Дотук картата носеше ред «📊 СИЛЕН 6/8 · долар+лихви 2/2 ✓ подредено», който
    казваше с числа точно това, което редът «Защо» казва с думи — и още два реда
    статистика от бектеста. Коста: «неразбираш нищо от тях».
    Класът, бройките и зоната остават в дневника; тук остава решението."""
    метал = "злато" if sym == "XAUUSD" else "сребро"
    ико = "🟢" if direction == "long" else "🔴"
    посока = "ПОКУПКА" if direction == "long" else "ПРОДАЖБА"
    накъде = "нагоре" if direction == "long" else "надолу"
    _вд, _, _защо = advice_txt.partition(" — ")
    _защо = _защо or advice_txt

    # ── 1 · ЗАГЛАВИЕТО: какво и кога, в един поглед ───────────────────────
    if open_trade:
        L = [f"📌 <b>Сделката тече</b> · {метал} {посока.lower()} от "
             f"<code>{_fmt(open_trade['entry'], dec)}</code> · {_sofia()} София",
             "─────────────────"]
        hit = open_trade.get("hit", {})
        ol = open_trade["levels"]
        L.append(" ".join(
            f"{n} <code>{_fmt(ol[k], dec)}</code>{' ✅' if hit.get(k) else ''}"
            for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3"))))
        if hit.get("tp1"):
            L.append(f"🛑 Стоп <code>{_fmt(ol['sl'], dec)}</code> — вече на входа, "
                     f"оттук нататък не можеш да загубиш.")
        else:
            L.append(f"🛑 Стоп <code>{_fmt(ol['sl'], dec)}</code>")
        if spot:
            L.append(f"Цена сега <code>{_fmt(spot['mid'], dec)}</code>.")
        L.append("<b>Дръж я</b> — не отваряй нова в същата посока.")
        return "\\n".join(L)

    if adv_ok:
        глава = f"{ико} <b>{посока}</b> · {метал} · {_sofia()} София"
    elif _вд.startswith("ИЗЧАКАЙ"):
        глава = f"⏸ <b>ИЗЧАКАЙ</b> · {метал} {накъде} · {_sofia()} София"
    else:
        глава = f"⏸ <b>Не влизам</b> · {метал} {накъде} · {_sofia()} София"
    L = [глава, "─────────────────"]
    if reentry:
        L.append("Предишната сделка приключи, а сигналът още стои.")

    # ── 2 · ЗАЩО: едно изречение, човешко ─────────────────────────────────
    L.append(f"<b>Защо:</b> {_защо}")

    # ── 3 · КЪДЕ: нивата ──────────────────────────────────────────────────
    цели = (f"1️⃣ <code>{_fmt(lv['tp1'], dec)}</code>   "
            f"2️⃣ <code>{_fmt(lv['tp2'], dec)}</code>   "
            f"3️⃣ <code>{_fmt(lv['tp3'], dec)}</code>")
    if adv_ok:
        L.append(f"🎯 <b>Влез на</b> <code>{_fmt(entry, dec)}</code>"
                 + ("" if spot else " <i>(по бара — живата цена мълчи)</i>"))
        L.append(цели)
        L.append(f"🛑 <b>Стоп</b> <code>{_fmt(lv['sl'], dec)}</code>")
    else:
        L.append(f"<i>Ако решиш сам:</i> вход <code>{_fmt(entry, dec)}</code> · "
                 f"стоп <code>{_fmt(lv['sl'], dec)}</code>")
        L.append(цели)

    # ── 4 · КОЛКО: размерът, само когато има смисъл ───────────────────────
    _zc, _ = (zone if zone else (None, ""))
    _zw = ZONE_W.get(_zc, 1.0) if _zc else 1.0
    риск = balance * risk_pct / 100.0 * _zw
    намален = "" if _zw >= 0.999 else " <i>(намален — зоната е по-слаба)</i>"
    if sym == "XAUUSD":
        унции = риск / SL_D
        лот = унции / 100.0
        малък = лот < 0.01
        мин_риск = 1.0 * SL_D
    else:
        унции = риск / S_SL
        лот = унции / 5000.0
        малък = унции < 50.0
        мин_риск = 50.0 * S_SL
    if adv_ok:
        if малък:
            L.append(f"💰 <b>Под най-малката позиция.</b> Най-малкото е 0.01 лот — "
                     f"рискува −${мин_риск:.0f}, тоест "
                     f"{(мин_риск / balance * 100.0 if balance else 0):.1f}% от парите ти.")
        else:
            L.append(f"💰 <b>{лот:.2f} лот</b> · по 1/3 на всяка цел · "
                     f"рискуваш ${риск:.0f}{намален}")
    else:
        if shadow_on and abs(float(shadow_on.get("entry", entry)) - entry) >= 0.01:
            L.append(f"👁 Следя наум по-ранния вход "
                     f"<code>{_fmt(float(shadow_on['entry']), dec)}</code> — "
                     f"ще ти кажа, ако проработи.")
        else:
            L.append("👁 Следя го наум — ще ти кажа, ако проработи.")
    return "\\n".join(L)

'''
s = s[:i] + ново + s[j + 1:]
io.open(p, "wb").write(s.encode("utf-8"))
import ast
ast.parse(io.open(p, encoding="utf-8").read())
print(f"_sig_msg пренаписана · {p}: {len(s.splitlines())} реда · "
      f"sha {hashlib.sha256(s.encode()).hexdigest()[:12]}")
