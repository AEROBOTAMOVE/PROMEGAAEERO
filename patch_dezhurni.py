# -*- coding: utf-8 -*-
"""
ОДИТ-28 · ЧАКАЩИТЕ И ДЕЖУРНИТЕ КАРТИ

СТОЯЩ и СПРЯНА нямаха ред «какво да правя» — казваха «виждам нещо» и спираха.
ПУЛСЪТ ползваше «най-силен клас СИЛЕН 6/8 · макро 3/3 ✓ подредено».
СТАТУСЪТ показваше «базис +57.70» — дума, която няма работа при Коста.

MA-АЛАРМАТА беше най-объркващата карта в целия бот: даваше «Ориентир при вход:
ТП1 … СТОП …» и веднага под тях «⚠ с тази геометрия сметката е отрицателна».
Тоест подаваше нива за вход, по който сама казва да не влизаш.
Решението: нивата ПАДАТ. Ако сметката е отрицателна, картата е знак за нивото,
не покана за сделка — и го казва с думи.
"""
import io, sys, hashlib

p = "live_bot.py"
s = io.open(p, encoding="utf-8", newline="").read()


def замени_функция(име, нов_код):
    global s
    i = s.index(f"def {име}(")
    j = s.index("\ndef ", i + 10)
    s = s[:i] + нов_код + s[j + 1:]
    print(f"  + {име}")


замени_функция("_standing_msg", '''def _standing_msg(direction, best, age_h, spot, bar_price, price_user, board, macro, health, now_utc):
    """ОДИТ-28: «сетъпът още стои». Нивата ги има (Коста ги иска, за да гледа),
    но картата вече казва И какво прави ботът — дотук свършваше с числата."""
    ико = "🟢" if direction == "long" else "🔴"
    посока = "покупка" if direction == "long" else "продажба"
    съгласни = sum(1 for b in board if b[1] == direction and b[3] != "weak")
    lv = _levels(round(price_user, 2), direction)
    L = [f"⏸ <b>Сетъпът за {посока} още стои</b> · злато · {_sofia(now_utc)} София",
         "─────────────────",
         f"{ико} Посоката се държи вече <b>{age_h:.0f} часа</b> · "
         f"{съгласни} от 7 времеви мащаба гледат натам.",
         f"Цена сега <code>{_fmt(price_user, 2)}</code> · стоп щеше да е "
         f"<code>{_fmt(lv['sl'], 2)}</code>",
         f"1️⃣ <code>{_fmt(lv['tp1'], 2)}</code>   "
         f"2️⃣ <code>{_fmt(lv['tp2'], 2)}</code>   "
         f"3️⃣ <code>{_fmt(lv['tp3'], 2)}</code>"]
    if health and health.get("мъртви"):
        L.append(f"⚠️ Един от източниците мълчи ({', '.join(health['мъртви'])}) — "
                 f"броя го предпазливо.")
    L.append("Аз не отварям — сетъпът вече не е пресен. Ако се поднови, ще ти пиша.")
    return "\\n".join(L)

''')

замени_функция("_спряна_msg", '''def _спряна_msg(direction, best, price_user, причина, обяснение, now_utc, board):
    """ОДИТ-26/28: ботът ВИЖДА сетъп, но правило му спира картата.
    Дотук това беше ред в дневника, който Коста никога не вижда.
    БЕЗ нива — за да не се чете като покана. Решението не се променя:
    сделка не се отваря, стоп-пазачът и бордът не се пипат."""
    ико = "🟢" if direction == "long" else "🔴"
    посока = "покупка" if direction == "long" else "продажба"
    съгласни = sum(1 for b in board if b[1] == direction and b[3] != "weak") if board else 0
    return "\\n".join([
        f"⏸ <b>Виждам {посока}, но не я предлагам</b> · злато · {_sofia(now_utc)} София",
        "─────────────────",
        f"{ико} {съгласни} от 7 времеви мащаба гледат натам · цена "
        f"<code>{_fmt(price_user, 2)}</code>",
        f"<b>Защо не:</b> {причина}",
        "Сега не се прави нищо. Ще ти пиша веднага щом спирачката падне."])

''')

замени_функция("_ma_alert_msg", '''def _ma_alert_msg(direction, ma_name, price, mb, macro):
    """ОДИТ-28: дотук картата даваше нива за вход и веднага под тях казваше, че
    сметката е отрицателна — подаваше покана и отказ в едно съобщение.
    Нивата паднаха. Това е ЗНАК ЗА НИВО, не сделка, и картата го казва."""
    ико = "🟢" if direction == "long" else "🔴"
    какво = "отскочи от" if direction == "long" else "се отби от"
    накъде = "нагоре" if direction == "long" else "надолу"
    return "\\n".join([
        f"📌 <b>Цената {какво} {ma_name.upper()}</b> · злато · {_sofia()} София",
        "─────────────────",
        f"{ико} <code>{_fmt(price)}</code> докосна линията, която целият пазар гледа, "
        f"и се обърна {накъде}.",
        "Аз не влизам по това — с нашия стоп сметката излиза на минус.",
        "Гледай го само като знак, че нивото държи."])

''')

замени_функция("_pulse_msg", '''def _pulse_msg(part, board, best, new_dir, advice_txt, adv_ok, trade, s_trade,
               spot_g, spot_s, macro, shield, weekend):
    """ОДИТ-28: три пъти на ден — «жив съм, ето какво гледам и какво чакам».
    Дотук казваше «най-силен клас СИЛЕН 6/8 · макро 3/3 ✓ подредено»."""
    ико, кога = {"09": ("☀️", "Добро утро"), "14": ("🌤️", "Ето докъде сме"),
                 "22": ("🌙", "Ето как мина денят")}.get(part, ("📌", "Ето какво гледам"))
    L = [f"{ико} <b>Коста, {кога}</b> · {_sofia()} София", "─────────────────"]
    if weekend:
        L += ["Борсата за злато е затворена — почивам с теб.",
              "Отваря неделя вечер. Ще се обадя, щом има какво."]
        return "\\n".join(L)
    if spot_g:
        L.append(f"🥇 злато <code>{spot_g['mid']:,.2f}</code>"
                 + (f" · 🥈 сребро <code>{spot_s['mid']:,.3f}</code>" if spot_s else ""))
    else:
        L.append("Живата цена не идва в момента — ползвам последния бар.")
    if new_dir:
        накъде = "нагоре" if new_dir == "long" else "надолу"
        съгл = sum(1 for b in board if b[1] == new_dir and b[3] != "weak") if board else 0
        L.append(f"Очертава се движение <b>{накъде}</b> — {съгл} от 7 времеви мащаба "
                 f"гледат натам.")
    else:
        L.append("Посоката е разбъркана — мащабите не се разбират помежду си.")
    има = False
    for нм, tr, sp, dec in (("🥇 злато", trade, spot_g, 2), ("🥈 сребро", s_trade, spot_s, 3)):
        if tr:
            има = True
            прибр = [n for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3"))
                     if tr.get("hit", {}).get(k)]
            пл = ((sp["mid"] - tr["entry"]) if tr["direction"] == "long"
                  else (tr["entry"] - sp["mid"])) if sp else None
            L.append(f"{нм}: държим {'покупка' if tr['direction'] == 'long' else 'продажба'} "
                     f"от <code>{tr['entry']:,.{dec}f}</code>"
                     + (f" · прибрани {' '.join(прибр)}" if прибр else "")
                     + (f" · сега <b>{пл:+.2f}$</b>" if пл is not None else ""))
    if not има:
        L.append("Няма отворена сделка.")
    if shield and new_dir == "short":
        L.append("Чакам американските данни да минат — после гледам пак.")
    elif има:
        L.append("Следя сделката до целите. Ти не пипай нищо.")
    elif new_dir and adv_ok:
        L.append("Чакам потвърждение и ти пращам вход.")
    elif new_dir:
        L.append("Чакам сетъпът да се поднови — сега не влизам.")
    else:
        L.append("Чакам пазарът да се реши. Нищо не се прави.")
    return "\\n".join(L)

''')

замени_функция("_status_msg", '''def _status_msg(board, new_dir, trade, s_trade, spot_g, spot_s, basis_g, basis_s,
                guard, shield, date, macro):
    """ОДИТ-28: снимка на момента. Дотук показваше «базис +57.70» и «съгласие:
    long:medium» — думи от машинното отделение."""
    L = [f"📌 <b>Къде сме в момента</b> · {_sofia()} София", "─────────────────"]
    for нм, tr, sp, dec in (("🥇 злато", trade, spot_g, 2), ("🥈 сребро", s_trade, spot_s, 3)):
        if tr:
            прибр = [n for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3"))
                     if tr.get("hit", {}).get(k)]
            пл = ((sp["mid"] - tr["entry"]) if tr["direction"] == "long"
                  else (tr["entry"] - sp["mid"])) if sp else None
            L.append(f"{нм}: {'покупка' if tr['direction'] == 'long' else 'продажба'} от "
                     f"<code>{tr['entry']:,.{dec}f}</code>"
                     + (f" · прибрани {' '.join(прибр)}" if прибр else "")
                     + f" · стоп <code>{tr['levels']['sl']:,.{dec}f}</code>"
                     + (f" · сега <b>{пл:+.2f}$</b>" if пл is not None else ""))
        else:
            L.append(f"{нм}: няма отворена сделка")
    if spot_g:
        L.append(f"Цени: злато <code>{spot_g['mid']:,.2f}</code>"
                 + (f" · сребро <code>{spot_s['mid']:,.3f}</code>" if spot_s else ""))
    L.append("Това е само снимка на момента — не се прави нищо.")
    return "\\n".join(L)

''')

io.open(p, "wb").write(s.encode("utf-8"))
import ast
ast.parse(io.open(p, encoding="utf-8").read())
print(f"\n{p}: {len(s.splitlines())} реда · sha {hashlib.sha256(s.encode()).hexdigest()[:12]}")
