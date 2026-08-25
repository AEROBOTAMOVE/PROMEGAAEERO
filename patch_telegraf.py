# -*- coding: utf-8 -*-
"""
ОДИТ-29 · ТЕЛЕГРАФ, НЕ ПИСМО

Коста, 11.08 втори път: «пишеш нещата много тегаво и дълго. Трябва точно ясно
с емотикон и какво трябва да става и какво трябва да значи и къде да се влиза.
Мега ясно и точно и кратко и просто обяснено — какво, кога, къде.»

ГРЕШКАТА МИ: направих изреченията човешки, но си останаха ИЗРЕЧЕНИЯ.
«Сложи поръчката и стопа веднага. Излизаш на три части — по една трета на
всяка цел.» е добър български и лоша карта. На телефон се чете РЕД, не абзац.

НОВОТО ПРАВИЛО — един ред, едно нещо, едно емоджи отпред:
    🟢 КУПИ ЗЛАТО · 15:54
    🎯 вход 4365.20
    🛑 стоп 4345.20
    1️⃣ 4372.70 · 2️⃣ 4377.20 · 3️⃣ 4385.20
    💰 0.03 лот · риск 67$
    📌 доларът и лихвите нагоре от днес

Няма разделител (яде ред и не носи нищо на телефон). Няма изречения с точка
в средата. Няма подчинени изречения. Максимум 6 реда.
"""
import io, sys, hashlib

p = "live_bot.py"
s = io.open(p, encoding="utf-8", newline="").read()


def функция(име, нов_код):
    global s
    i = s.index(f"def {име}(")
    j = s.index("\ndef ", i + 10)
    s = s[:i] + нов_код + s[j + 1:]
    print(f"  + {име}")


def rep(old, new, why, n=1):
    global s
    c = s.count(old)
    if c != n:
        print(f"  x СПИРАМ «{why}»: {c} съвпадения, чакам {n}\n    {old[:110]!r}")
        sys.exit(1)
    s = s.replace(old, new)
    print(f"  + {why}")


# ═══ 1 · ПРИСЪДАТА: от изречение на откъс ═════════════════════════════════
for старо, ново, име in [
    ('''        return ("НЕ — днес стопът вече ме изхвърли два пъти в тази посока. "
                "Спирам дотук и пробвам утре."), False''',
     '''        return "НЕ — два стопа днес, спирам до утре", False''', "стоп-пазач"),
    ('''        return (f"НЕ СЕГА — американските данни излизат в {_shield_sofia_label()}. "
                f"Продажба точно в този прозорец се обръща срещу теб. "
                f"Ще се обадя, ако сетъпът се задържи след тях."), False''',
     '''        return f"НЕ — американски данни {_shield_sofia_label()}, чакам ги", False''', "US-щит"),
    ('''        return ("ИЗЧАКАЙ — живата цена не идва. Тази отгоре е отпреди 10-15 минути, "
                "затова влизай само с лимитна поръчка точно на нивото."), False''',
     '''        return "ИЗЧАКАЙ — живата цена мълчи, само лимитна поръчка", False''', "стара цена"),
    ('''            return ("ДА — златото опря в най-високото си от 20 дни и се обръща надолу. "
                    "Точно този случай работи." + _fast(fast)), True''',
     '''            return "ДА — злато на върха си от 20 дни, обръща се" + _fast(fast), True''', "връх-шорт"),
    ('''            return ("ИЗЧАКАЙ — подреждането е прясно, но точно такива случаи досега "
                    "не са носили нищо. Чакам следващото потвърждение." + _fast(fast)), False''',
     '''            return ("ИЗЧАКАЙ — прясно е, но такива случаи не носят нищо"
                    + _fast(fast)), False''', "прясно, но празно"),
    ('''        return (f"ДА — доларът и лихвите дърпат {_накъде} {_откога}. Това е моментът."
                + _fast(fast)), True''',
     '''        return f"ДА — доларът и лихвите {_накъде} {_откога}" + _fast(fast), True''', "пресен"),
    ('''            return ("НЕ — доларът и лихвите не сочат в една посока днес. "
                    "В такива дни този сигнал не носи нищо." + _fast(fast)), False''',
     '''            return "НЕ — доларът и лихвите се карат днес" + _fast(fast), False''', "смесено"),
    ('''        return (f"НЕ — подреждането е {_откога} и се е изхабило." + _fast(fast)), False''',
     '''        return f"НЕ — подреждането е {_откога}, изхабило се е" + _fast(fast), False''', "застояло"),
    ('''        return ("ДА, но с малък размер — макрото не помага днес, сигналът стъпва "
                "само на цената." + _fast(fast)), True''',
     '''        return "ДА (малък размер) — макрото мълчи, само по цена" + _fast(fast), True''', "тънко смесено"),
    ('''    return (f"ДА, но с малък размер — подреждането е {_откога}, ръбът е по-тънък."
            + _fast(fast)), True''',
     '''    return f"ДА (малък размер) — подреждането е {_откога}" + _fast(fast), True''', "тънко застояло"),
    ('''    return (f" Пазарът лети — по ${fast:.0f} за десет минути; влизай само с "
            f"лимитна поръчка." if fast else "")''',
     '''    return f" · бърз пазар ±${fast:.0f}/10мин, само лимитна" if fast else ""''', "бърз пазар"),
]:
    rep(старо, ново, име)

# ═══ 2 · СИГНАЛНАТА КАРТА ═════════════════════════════════════════════════
функция("_sig_msg", '''def _sig_msg(direction, score, agree_n, tier_name, spot, bar_price, bar_ts, lv, entry,
             advice_txt, macro, streak_n, regime, stats, balance, risk_pct, weekly=None,
             reentry=False, open_trade=None, sym="XAUUSD", dec=2, extra_ctx=None, adv_ok=True,
             shadow_on=None, zone=None):
    """ОДИТ-29 · един ред, едно нещо, едно емоджи отпред.
    Дотук картата беше добър български и лоша карта: изречения с подчинени
    и точка в средата. На телефон се чете РЕД, не абзац."""
    метал = "ЗЛАТО" if sym == "XAUUSD" else "СРЕБРО"
    _, _, защо = advice_txt.partition(" — ")
    защо = защо or advice_txt

    if open_trade:
        hit = open_trade.get("hit", {}); ol = open_trade["levels"]
        L = [f"📌 СДЕЛКАТА ТЕЧЕ · {метал} "
             f"{'покупка' if open_trade['direction'] == 'long' else 'продажба'} · {_sofia()}",
             f"🎯 вход <code>{_fmt(open_trade['entry'], dec)}</code>",
             "🛑 стоп <code>%s</code>%s" % (_fmt(ol["sl"], dec),
                                            " (на входа — без риск)" if hit.get("tp1") else ""),
             " · ".join(f"{n} <code>{_fmt(ol[k], dec)}</code>{' ✅' if hit.get(k) else ''}"
                        for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3")))]
        if spot:
            L.append(f"💵 сега <code>{_fmt(spot['mid'], dec)}</code>")
        L.append("👁 дръж я · не отваряй нова")
        return "\\n".join(L)

    if not adv_ok:
        L = [f"⏸ БЕЗ ВХОД · {метал} "
             f"{'нагоре' if direction == 'long' else 'надолу'} · {_sofia()}",
             f"📌 {защо}",
             f"🎯 ако решиш сам: <code>{_fmt(entry, dec)}</code> · "
             f"🛑 <code>{_fmt(lv['sl'], dec)}</code>",
             " · ".join(f"{n} <code>{_fmt(lv[k], dec)}</code>"
                        for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3")))]
        if shadow_on and abs(float(shadow_on.get("entry", entry)) - entry) >= 0.01:
            L.append(f"👁 следя наум от <code>{_fmt(float(shadow_on['entry']), dec)}</code>")
        else:
            L.append("👁 следя го наум")
        return "\\n".join(L)

    ико = "🟢" if direction == "long" else "🔴"
    глагол = "КУПИ" if direction == "long" else "ПРОДАЙ"
    _zc, _ = (zone if zone else (None, ""))
    _zw = ZONE_W.get(_zc, 1.0) if _zc else 1.0
    риск = balance * risk_pct / 100.0 * _zw
    ед = SL_D if sym == "XAUUSD" else S_SL
    дел = 100.0 if sym == "XAUUSD" else 5000.0
    лот = риск / ед / дел
    L = [f"{ико} {глагол} {метал} · {_sofia()}",
         f"🎯 вход <code>{_fmt(entry, dec)}</code>"
         + ("" if spot else " <i>(по бара — живата цена мълчи)</i>"),
         f"🛑 стоп <code>{_fmt(lv['sl'], dec)}</code>",
         " · ".join(f"{n} <code>{_fmt(lv[k], dec)}</code>"
                    for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3")))]
    if лот < 0.01:
        L.append(f"💰 под мин. лот · 0.01 лот = риск ${ед * (1.0 if sym == 'XAUUSD' else 50.0):.0f}")
    else:
        L.append(f"💰 {лот:.2f} лот · риск ${риск:.0f}"
                 + ("" if _zw >= 0.999 else " (намален)") + " · по 1/3 на цел")
    L.append(f"📌 {защо}")
    if reentry:
        L.append("♻️ ре-влизане · предишната приключи")
    return "\\n".join(L)

''')

# ═══ 3 · ИЗХОДИТЕ ═════════════════════════════════════════════════════════
функция("_exit_msg", '''def _exit_msg(kind, tr, price_hit, when, via, gap, spot=None, next_line="", dec=2):
    """ОДИТ-29 · КОЯ цел · КОЛКО пари · КАКВО правиш. По един ред всяко."""
    метал = "ЗЛАТО" if tr.get("sym", "XAUUSD") == "XAUUSD" else "СРЕБРО"
    посока = "покупка" if tr["direction"] == "long" else "продажба"
    e = tr["entry"]; lv = tr["levels"]; hit = tr.get("hit", {})
    знак = 1 if tr["direction"] == "long" else -1
    дол = (price_hit - e) * знак
    if abs(дол) < 0.005:
        дол = 0.0
    стълба, взети = _ladder_pnl(kind, hit, lv, e, знак, дол)
    час = _sofia(when) if via in ("бар", "спот") else _sofia()
    гап = " · с гап" if gap else ""
    глави = {"tp1": ("✅", "ЦЕЛ 1"), "tp2": ("✅", "ЦЕЛ 2"), "tp3": ("🏆", "ВСИЧКО ПРИБРАНО"),
             "sl": ("🛑", "СТОП"), "flip": ("⏸", "ЗАТВОРЕНА · посоката се обърна"),
             "time": ("⏸", "ЗАТВОРЕНА · по време")}
    ико, дума = глави.get(kind, ("📌", kind))
    if kind == "sl" and взети > 0:
        ико, дума = ("✅", "НУЛА") if стълба >= 0 else ("🛑", "СТОП")
        дума += " · стопът беше на входа"
    L = [f"{ико} {дума} · {метал} {посока} · {час}",
         f"💵 <code>{_fmt(e, dec)}</code> → <code>{_fmt(price_hit, dec)}</code> · "
         f"<b>{дол:+.2f}$</b>/унция{гап}"]
    if kind == "tp1":
        L.append(f"🛑 премести стопа на <code>{_fmt(e, dec)}</code> · оттук нататък без риск")
        L.append(f"🎯 остават 2️⃣ <code>{_fmt(lv['tp2'], dec)}</code> · "
                 f"3️⃣ <code>{_fmt(lv['tp3'], dec)}</code>")
    elif kind == "tp2":
        L.append(f"🎯 остава 3️⃣ <code>{_fmt(lv['tp3'], dec)}</code> · 2/3 са прибрани")
    else:
        L.append(f"💰 сделката донесе <b>{стълба:+.2f}$</b>/унция общо")
        L.append("👁 затворена · чакам нов сигнал")
    if next_line:
        L.append(f"♻️ ново влизане: {next_line}")
    return "\\n".join(L)

''')

функция("_shadow_exit_msg", '''def _shadow_exit_msg(kind, tr, price_hit, when, via, gap, spot=None, dec=2):
    """ОДИТ-29 · «онова, което ти казах да не пипаш, стигна дотук». Три реда."""
    метал = "ЗЛАТО" if tr.get("sym", "XAUUSD") == "XAUUSD" else "СРЕБРО"
    посока = "покупка" if tr["direction"] == "long" else "продажба"
    e = tr["entry"]; lv = tr["levels"]; hit = tr.get("hit", {})
    знак = 1 if tr["direction"] == "long" else -1
    дол = (price_hit - e) * знак
    if abs(дол) < 0.005:
        дол = 0.0
    стълба, взети = _ladder_pnl(kind, hit, lv, e, знак, дол)
    час = _sofia(when) if via in ("бар", "спот") else _sofia()
    какво = {"tp1": "щеше да хване ЦЕЛ 1", "tp2": "щеше да хване ЦЕЛ 2",
             "tp3": "щеше да мине докрай", "sl": "щеше да удари стоп",
             "flip": "посоката се обърна", "time": "щеше да излезе по време"}.get(kind, kind)
    if kind == "sl" and взети > 0:
        какво = "щеше да излезе на нула"
    return "\\n".join([
        f"👁 НАУМ · {какво} · {метал} {посока} · {час}",
        f"💵 <code>{_fmt(e, dec)}</code> → <code>{_fmt(price_hit, dec)}</code> · "
        f"<b>{стълба:+.2f}$</b>/унция",
        "📌 не съм влизал · само да знаеш"])

''')

# ═══ 4 · ЧАКАЩИТЕ ═════════════════════════════════════════════════════════
функция("_standing_msg", '''def _standing_msg(direction, best, age_h, spot, bar_price, price_user, board, macro, health, now_utc):
    """ОДИТ-29 · сетъпът стои, но не е пресен. Четири реда."""
    ико = "🟢" if direction == "long" else "🔴"
    посока = "покупка" if direction == "long" else "продажба"
    съгл = sum(1 for b in board if b[1] == direction and b[3] != "weak")
    lv = _levels(round(price_user, 2), direction)
    L = [f"⏸ СТОИ · {посока} злато · {_sofia(now_utc)}",
         f"{ико} {съгл}/7 мащаба натам · вече {age_h:.0f}ч",
         f"🎯 <code>{_fmt(price_user, 2)}</code> · 🛑 <code>{_fmt(lv['sl'], 2)}</code>",
         " · ".join(f"{n} <code>{_fmt(lv[k], 2)}</code>"
                    for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3")))]
    if health and health.get("мъртви"):
        L.append(f"⚠️ мълчи: {', '.join(health['мъртви'])}")
    L.append("👁 не влизам · не е пресен")
    return "\\n".join(L)

''')

функция("_спряна_msg", '''def _спряна_msg(direction, best, price_user, причина, обяснение, now_utc, board):
    """ОДИТ-26/29 · виждам сетъп, спирачка го спира. Четири реда, без нива."""
    ико = "🟢" if direction == "long" else "🔴"
    посока = "покупка" if direction == "long" else "продажба"
    съгл = sum(1 for b in board if b[1] == direction and b[3] != "weak") if board else 0
    return "\\n".join([
        f"⏸ ВИЖДАМ {посока.upper()} · но не я давам · {_sofia(now_utc)}",
        f"{ико} {съгл}/7 мащаба натам · <code>{_fmt(price_user, 2)}</code>",
        f"📌 {причина}",
        "👁 нищо сега · пиша щом падне спирачката"])

''')

# ═══ 5 · ДЕЖУРНИТЕ ════════════════════════════════════════════════════════
функция("_ma_alert_msg", '''def _ma_alert_msg(direction, ma_name, price, mb, macro):
    """ОДИТ-28/29 · знак за ниво, НЕ сделка. Нивата паднаха — картата даваше
    вход, по който сама казваше да не влизаш."""
    ико = "🟢" if direction == "long" else "🔴"
    накъде = "нагоре" if direction == "long" else "надолу"
    return "\\n".join([
        f"📌 НИВО · цената се обърна {накъде} от {ma_name.upper()} · {_sofia()}",
        f"{ико} злато <code>{_fmt(price)}</code>",
        "👁 само знак · не влизам, сметката е на минус"])

''')

функция("_pulse_msg", '''def _pulse_msg(part, board, best, new_dir, advice_txt, adv_ok, trade, s_trade,
               spot_g, spot_s, macro, shield, weekend):
    """ОДИТ-29 · 3× на ден: жив съм, това гледам, това чакам."""
    ико, кога = {"09": ("☀️", "добро утро"), "14": ("🌤️", "докъде сме"),
                 "22": ("🌙", "как мина денят")}.get(part, ("📌", "какво гледам"))
    L = [f"{ико} Коста, {кога} · {_sofia()}"]
    if weekend:
        L.append("😴 борсата спи · отваря неделя вечер")
        return "\\n".join(L)
    if spot_g:
        L.append(f"🥇 <code>{spot_g['mid']:,.2f}</code>"
                 + (f" · 🥈 <code>{spot_s['mid']:,.3f}</code>" if spot_s else ""))
    else:
        L.append("⚠️ живата цена мълчи · карам по бара")
    if new_dir:
        съгл = sum(1 for b in board if b[1] == new_dir and b[3] != "weak") if board else 0
        L.append(f"{'🟢' if new_dir == 'long' else '🔴'} очертава се "
                 f"{'нагоре' if new_dir == 'long' else 'надолу'} · {съгл}/7 мащаба")
    else:
        L.append("📌 посоката е разбъркана")
    има = False
    for нм, tr, sp, dec in (("🥇", trade, spot_g, 2), ("🥈", s_trade, spot_s, 3)):
        if tr:
            има = True
            прибр = [n for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3"))
                     if tr.get("hit", {}).get(k)]
            пл = ((sp["mid"] - tr["entry"]) if tr["direction"] == "long"
                  else (tr["entry"] - sp["mid"])) if sp else None
            L.append(f"{нм} държим от <code>{tr['entry']:,.{dec}f}</code>"
                     + (f" · {' '.join(прибр)} ✅" if прибр else "")
                     + (f" · <b>{пл:+.2f}$</b>" if пл is not None else ""))
    if shield and new_dir == "short":
        L.append("👁 чакам американските данни")
    elif има:
        L.append("👁 следя до целите · ти не пипай")
    elif new_dir and adv_ok:
        L.append("👁 чакам потвърждение · пращам вход")
    elif new_dir:
        L.append("👁 не влизам · не е пресен")
    else:
        L.append("👁 нищо сега")
    return "\\n".join(L)

''')

функция("_status_msg", '''def _status_msg(board, new_dir, trade, s_trade, spot_g, spot_s, basis_g, basis_s,
                guard, shield, date, macro):
    """ОДИТ-29 · снимка на момента, четири реда."""
    L = [f"📌 КЪДЕ СМЕ · {_sofia()}"]
    for нм, tr, sp, dec in (("🥇", trade, spot_g, 2), ("🥈", s_trade, spot_s, 3)):
        if tr:
            прибр = [n for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3"))
                     if tr.get("hit", {}).get(k)]
            пл = ((sp["mid"] - tr["entry"]) if tr["direction"] == "long"
                  else (tr["entry"] - sp["mid"])) if sp else None
            L.append(f"{нм} {'покупка' if tr['direction'] == 'long' else 'продажба'} от "
                     f"<code>{tr['entry']:,.{dec}f}</code>"
                     + (f" · {' '.join(прибр)} ✅" if прибр else "")
                     + f" · 🛑 <code>{tr['levels']['sl']:,.{dec}f}</code>"
                     + (f" · <b>{пл:+.2f}$</b>" if пл is not None else ""))
        else:
            L.append(f"{нм} няма сделка")
    if spot_g:
        L.append(f"💵 злато <code>{spot_g['mid']:,.2f}</code>"
                 + (f" · сребро <code>{spot_s['mid']:,.3f}</code>" if spot_s else ""))
    L.append("👁 само снимка · нищо не се прави")
    return "\\n".join(L)

''')

# ═══ 6 · ДНЕВНИТЕ ═════════════════════════════════════════════════════════
функция("_digest_msg", '''def _digest_msg(out, date, trade, s_trade, spot_g, spot_s, guard, weekly_part=False):
    """ОДИТ-29 · какво стана с парите днес. Пет реда."""
    def _редове(файл, условие):
        f = out / файл
        if not f.exists():
            return []
        r = []
        for ln in f.read_text(encoding="utf-8").splitlines():
            try:
                j = json.loads(ln)
                if условие(j):
                    r.append(j)
            except Exception:
                pass
        return r
    рънове = _редове("live_journal.jsonl", lambda r: r.get("date") == date)
    пратени = _редове("sent_log.jsonl", lambda r: str(r.get("utc", ""))[:10] == date)
    L = [f"🌙 Коста, как мина денят · {_sofia()}"]
    for нм, tr, sp, dec in (("🥇", trade, spot_g, 2), ("🥈", s_trade, spot_s, 3)):
        if tr:
            прибр = [n for n, k in (("1️⃣", "tp1"), ("2️⃣", "tp2"), ("3️⃣", "tp3"))
                     if tr.get("hit", {}).get(k)]
            пл = ((sp["mid"] - tr["entry"]) if tr["direction"] == "long"
                  else (tr["entry"] - sp["mid"])) if sp else None
            L.append(f"{нм} държим от <code>{tr['entry']:,.{dec}f}</code>"
                     + (f" · {' '.join(прибр)} ✅" if прибр else "")
                     + (f" · <b>{пл:+.2f}$</b>" if пл is not None else ""))
        else:
            L.append(f"{нм} няма сделка")
    if trade and s_trade and trade["direction"] == s_trade["direction"]:
        L.append("⚠️ и двете в една посока · рискът е един голям, не два малки")
    стопове = sum(guard.get(k, 0) for k in ("long", "short", "s_long", "s_short"))
    if стопове:
        L.append(f"🛑 стопът ме изхвърли {стопове}×")
    L.append(f"✅ буден цял ден · {len(рънове)} проверки · {len(пратени)} съобщения")
    L.append("👁 " + ("в понеделник пак съм тук" if weekly_part else "утре пак съм тук"))
    return "\\n".join(L)

''')

функция("_cq_msg", '''def _cq_msg(cq, now_utc, fng_live=None):
    """ОДИТ-28/29 · от 12 реда за биткойн до три реда за онова, което мени
    поведението на бота: следващото голямо макро събитие."""
    съб = _cq_next_event(cq, now_utc)
    L = []
    if съб:
        L.append(f"📅 ИДВА · {съб}")
        L.append("⚠️ около такива новини цената скача на празно")
        L.append("👁 не отварям нов вход в този прозорец")
    else:
        L.append(f"📌 ПАЗАРЕН ФОН · {_sofia()}")
        L.append("✅ няма голямо макро събитие пред нас")
    зона = str(cq.get("zone", "")).strip()
    точки = cq.get("score")
    if зона and точки is not None:
        L.append(f"🌡 крипто настроение: {зона} ({точки:.0f}/100) · само за фон")
    return "\\n".join(L)

''')

функция("_weekend_msg", '''def _weekend_msg(slot, date):
    """ОДИТ-29 · картичка за уикенда. Три реда, без обяснения."""
    pool = WEEKEND_MSGS[slot]
    try:
        idx = int(str(date).replace("-", "")) % len(pool)
    except Exception:
        idx = 0
    ико = {"сутрин": "☀️", "следобед": "🌤️", "вечер": "🌙"}[slot]
    кога = {"сутрин": "добро утро", "следобед": "приятен следобед",
            "вечер": "лека вечер"}[slot]
    return (f"{ико} Коста, {кога} · {_sofia()}\\n"
            f"📌 {pool[idx]}\\n"
            f"😴 борсата спи до неделя вечер")

''')

io.open(p, "wb").write(s.encode("utf-8"))
import ast
ast.parse(io.open(p, encoding="utf-8").read())
print(f"\n{p}: {len(s.splitlines())} реда · sha {hashlib.sha256(s.encode()).hexdigest()[:12]}")
