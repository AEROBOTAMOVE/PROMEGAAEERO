# -*- coding: utf-8 -*-
"""
ОДИТ-37 · О3 и О4 от генералния план — двата останали 🟠

О3 · КОРЕЛАЦИОННОТО ПРЕДУПРЕЖДЕНИЕ ЗАКЪСНЯВА С ЧАСОВЕ
    «Двете сделки в една посока = ~2× риск» се появява само в 21:00
    равносметката, не на сигналната карта в момента на решението.
    Златото и среброто вървят заедно (корелация ~0.8): две сделки в една
    посока не са два независими залога, а един двоен. Той научава това
    ВЕЧЕРТА, а решава СУТРИНТА.
    → другият метал влиза в `_sig_msg`; съвпадне ли посоката — предупреждение
      на самата карта, над реда за размера.

О4 · РЕ-ВЛИЗАНЕ-ЩИТЪТ Е ЕДНОКРАТЕН
    `_reentry_verdict` пази само рънa на затварянето. Следващият рън го
    заобикаля и отваря пресен шорт, за който същото правило казва, че губи
    (−2.75$/сделка, мерено). Тоест щитът важи пет минути.
    → забраната се записва в meta с ПОСОКА и СТРИЙК и важи, докато същият
      пресен стрийк е жив. Смени ли се стрийкът — забраната пада сама.
"""
import io, sys, hashlib

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

# ═══ О3 · корелацията влиза в самата карта ════════════════════════════════
rep(LB, '''             reentry=False, open_trade=None, sym="XAUUSD", dec=2, extra_ctx=None, adv_ok=True,
             shadow_on=None, zone=None):''',
    '''             reentry=False, open_trade=None, sym="XAUUSD", dec=2, extra_ctx=None, adv_ok=True,
             shadow_on=None, zone=None, other_trade=None):''',
    "О3 · подписът приема другия метал")

rep(LB, '''    L.append(f"📌 {защо}")
    if reentry:
        L.append("♻️ ре-влизане · предишната приключи")
    return "\\n".join(L)''',
    '''    L.append(f"📌 {защо}")
    # О3 · златото и среброто вървят заедно (корелация ~0.8). Две сделки в
    # една посока не са два независими залога, а един двоен. Дотук това се
    # казваше само във вечерната равносметка — часове след решението.
    if other_trade and other_trade.get("direction") == direction:
        _друг = "среброто" if sym == "XAUUSD" else "златото"
        L.append(f"⚠️ вече държиш {_друг} в същата посока · рискът е един голям, "
                 f"не два малки")
    if reentry:
        L.append("♻️ ре-влизане · предишната приключи")
    return "\\n".join(L)''',
    "О3 · предупреждението на картата")

rep(LB, '''                                            adv_ok=_adv_ok, shadow_on=sh_now,
                                            zone=_zones(frames.get("1час"), new_dir))))''',
    '''                                            adv_ok=_adv_ok, shadow_on=sh_now,
                                            zone=_zones(frames.get("1час"), new_dir),
                                            other_trade=s_trade)))''',
    "О3 · златото вижда среброто")

rep(LB, '''                adv_ok=s_adv_ok, shadow_on=sh_s_now)))''',
    '''                adv_ok=s_adv_ok, shadow_on=sh_s_now, other_trade=trade)))''',
    "О3 · среброто вижда златото")

# ═══ О4 · забраната за ре-влизане ЖИВЕЕ, докато стрийкът е жив ═══════════
rep(LB, '''def _reentry_verdict(direction, streak_n, shield, guard_n):''',
    '''def _reentry_ban(meta, direction, streak_n, why=None, set_it=False):
    """О4 · забраната за ре-влизане ПЕРСИСТИРА, докато същият пресен стрийк е жив.

    Дотук `_reentry_verdict` пазеше САМО рънa на затварянето — следващият рън,
    пет минути по-късно, минаваше покрай нея и отваряше точно шорта, за който
    същото правило казва, че губи −2.75$/сделка (мерено на 19.7 години).

    Ключът носи ПОСОКАТА и СТРИЙКА. Смени ли се стрийкът (макрото се преподреди
    или изтече), забраната пада САМА — не се трие на ръка и не увисва.
    """
    ключ = "reentry_ban"
    ст = meta.get(ключ) or {}
    if set_it and why:
        meta[ключ] = {"dir": direction, "streak": int(streak_n), "why": why}
        return True, why
    if (ст.get("dir") == direction and int(ст.get("streak", -1)) == int(streak_n)
            and 1 <= int(streak_n) <= 3):
        return True, ст.get("why") or "ре-влизането е спряно за този сигнал"
    if ст and (ст.get("dir") != direction or int(ст.get("streak", -1)) != int(streak_n)):
        meta.pop(ключ, None)          # стрийкът се смени → забраната пада сама
    return False, ""


def _reentry_verdict(direction, streak_n, shield, guard_n):''',
    "О4 · персистиращата забрана")

print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
import ast
ast.parse(io.open(LB, encoding="utf-8").read())
b = io.open(LB, encoding="utf-8").read()
print(f"{LB}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
