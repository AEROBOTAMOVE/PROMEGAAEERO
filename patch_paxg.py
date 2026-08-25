# -*- coding: utf-8 -*-
"""
ОДИТ-53 · КРИПТО-ЦЕНА, ПРЕДСТАВЕНА ЗА ЗЛАТО

Находка на армията, проверена лично.

🔴 №1 · РЕЗЕРВАТА РАБОТИ И В CME ПАУЗАТА
   `_spot("XAU/USD", market_closed=weekend)` — единственият пазач е УИКЕНДЪТ.
   Но CME Globex има и ДНЕВНА пауза (17:00 Ню Йорк, всеки делник, един час):
   фючърсът спира, а PAXG е крипто и върви 24/7. В този час резервата дава
   цена, която никой не арбитрира срещу затворен фючърс — и тя се показва като
   злато. Кодът СЪЩЕСТВУВА (`_cme_pause`) и вече се ползва в `_basis_update`
   точно по тази причина; на спот-резервата просто не е подаден.

🔴 №2 · НИТО ЕДНА КАРТА НЕ КАЗВА, ЧЕ ЦЕНАТА Е ОТ РЕЗЕРВА
   `spot_src` влиза в дневника, но собственикът вижда число и мисли, че е
   златният фийд. А PAXG търгува с ~$1-4 премия — самият код го знае и го
   изключва от базис-EMA-то по същата причина (НАХОДКА-B, ред 674).
   Числото на карта, за което не се казва откъде идва, е точно това, което
   този бот не бива да прави.
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

# ═══ №1 · резервата мълчи и в CME паузата ════════════════════════════════
rep('def _spot(instr="XAU/USD", market_closed=False):',
    'def _spot(instr="XAU/USD", market_closed=False, cme_pause=False):',
    "1 · подписът приема паузата")

rep('''    if market_closed:                                     # T5: не ползвай крипто-прокси при затворен пазар
        return None''',
    '''    # 🔴 ОДИТ-53 · И В ДНЕВНАТА CME ПАУЗА. Дотук пазачът беше само уикендът, а
    # CME Globex спира и всеки делник по един час (17:00 Ню Йорк). Тогава
    # фючърсът е затворен, а PAXG е крипто и върви 24/7 — цена, която никой не
    # арбитрира срещу затворен фючърс, показвана като злато.
    # `_cme_pause` вече съществува и се ползва в `_basis_update` по СЪЩАТА
    # причина; на спот-резервата просто не беше подаден.
    if market_closed or cme_pause:                        # T5: без крипто-прокси при спрял фючърс
        return None''',
    "1 · резервата мълчи в паузата")

rep('    raw_g = _spot("XAU/USD", market_closed=weekend)',
    '    raw_g = _spot("XAU/USD", market_closed=weekend, cme_pause=_cme_pause(now_utc))',
    "1 · златото я подава")

rep('        raw_s = _spot("XAG/USD", market_closed=weekend)',
    '        raw_s = _spot("XAG/USD", market_closed=weekend, cme_pause=_cme_pause(now_utc))',
    "1 · среброто я подава")

# ═══ №2 · картите казват, когато цената е от резерва ═════════════════════
rep('def _sofia(iso_utc=None):',
    '''def _от_резерва(spot):
    """🔴 ОДИТ-53 · КАЗВА ЛИ СЕ, ЧЕ ЦЕНАТА НЕ Е ОТ ЗЛАТНИЯ ФИЙД.
    `spot_src` влизаше само в дневника; собственикът виждаше число и мислеше, че
    е златният фийд. А PAXG търгува с ~$1-4 премия — самият код го знае и го
    изключва от базис-EMA-то по същата причина. Число на карта, за което не се
    казва откъде идва, е точно това, което този бот не бива да прави."""
    return str((spot or {}).get("src") or "").startswith("paxg")


def _sofia(iso_utc=None):''',
    "2 · разпознаване")

# пулсът
rep('''        L.append(f"🥇 <code>{spot_g['mid']:,.2f}</code>"
                 + (f" · 🥈 <code>{spot_s['mid']:,.3f}</code>" if spot_s else ""))''',
    '''        L.append(f"🥇 <code>{spot_g['mid']:,.2f}</code>"
                 + (" ⚠️резерва" if _от_резерва(spot_g) else "")
                 + (f" · 🥈 <code>{spot_s['mid']:,.3f}</code>"
                    + (" ⚠️резерва" if _от_резерва(spot_s) else "") if spot_s else ""))''',
    "2 · пулсът го казва")

# сигналната карта («сега»)
rep('''        if spot:
            L.append(f"💵 сега <code>{_fmt(spot['mid'], dec)}</code>")''',
    '''        if spot:
            L.append(f"💵 сега <code>{_fmt(spot['mid'], dec)}</code>"
                     + (" ⚠️ от крипто-резерва, не от златния фийд"
                        if _от_резерва(spot) else ""))''',
    "2 · сделката го казва")

io.open(p, "wb").write(s.encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
b = io.open(p, encoding="utf-8").read()
print(f"{p}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
