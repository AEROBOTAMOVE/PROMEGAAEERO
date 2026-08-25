# -*- coding: utf-8 -*-
"""
ОДИТ-36 · О1 · ИЗХОД-ПЪТЯТ ВЕЧЕ НЕ ВИСИ ЗАД МАКРО-ДЪРПАНЕТО

От генералния план, приоритет 🟠, отбелязан като «твоят на време»:

    Ако GDX/DXY/лихвите гръмнат, целият рън пропада ПРЕДИ track_trade →
    отворена сделка не получава изход, докато Yahoo се оправи. А следенето
    иска само 5м + спот + базис, не GDX/DXY/лихви.

Това е дефект С ПАРИ: сделка стои отворена, цената удря ТП или СТОП, а ботът
е паднал на дърпането на индекса на миньорите и не праща нищо.

РЕШЕНИЕТО (както го иска планът — «обвий макрото в try»):
 · ЗЛАТОТО остава твърдо — без него няма нищо
 · GDX / DXY / лихвите влизат в try. Гръмнат ли → None
 · при мъртво макро: `macro` е празно, `streaks` са нули (кофа «mixed»)
   → ГЕЙТЪТ ОТКАЗВА нови входове (това е безопасната посока)
 · но `track_trade`, изходите, стоп-пазачът и сянката ВЪРВЯТ нормално

Тоест: не виждам ли макрото, не отварям нищо ново — но довеждам докрай
това, което вече е отворено. Точно обратното на досегашното поведение.
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

rep(LB, '''    gold_d = _yf("GC=F", "3y", "1d"); time.sleep(1.2)
    gdx_d = _yf("GDX", "2y", "1d"); time.sleep(1.2)
    dxy_d = _yf("DX-Y.NYB", "2y", "1d"); time.sleep(1.2); rr = _rates()
    for d in (gold_d, gdx_d, dxy_d):
        d.index = d.index.normalize()''',
    '''    # 🔴 О1 · ЗЛАТОТО е твърдо — без него няма нищо. МАКРОТО е в try.
    # Дотук едно гръмнало дърпане на GDX убиваше ЦЕЛИЯ рън ПРЕДИ track_trade:
    # отворена сделка не получаваше изход, докато Yahoo се оправи. Следенето
    # иска само 5м + спот + базис — няма причина да виси зад индекса на миньорите.
    gold_d = _yf("GC=F", "3y", "1d"); time.sleep(1.2)
    gdx_d = dxy_d = rr = None
    _макро_мъртво = []
    for _име, _взем in (("миньори (GDX)", lambda: _yf("GDX", "2y", "1d")),
                        ("долар (DXY)", lambda: _yf("DX-Y.NYB", "2y", "1d")),
                        ("лихви (FRED)", _rates)):
        try:
            _р = _взем()
            if _име.startswith("миньори"):
                gdx_d = _р
            elif _име.startswith("долар"):
                dxy_d = _р
            else:
                rr = _р
        except Exception as _e:
            _макро_мъртво.append(_име)
            print(f"  ⚠ {_име} не се дърпа ({type(_e).__name__}) — новите входове спират, "
                  f"следенето продължава")
        time.sleep(1.2)
    for d in (gold_d, gdx_d, dxy_d):
        if d is not None:
            d.index = d.index.normalize()''',
    "О1 · макрото в try, златото твърдо")

rep(LB, '''    macro = _macro(gold_h, gdx_h, dxy_h, rr, health=macro_health); refs = _refs(gold_h)''',
    '''    # О1: мъртво макро → празно макро и нулев стрийк (кофа «mixed») → гейтът
    # ОТКАЗВА нови входове. Безопасната посока: не виждам ли, не отварям.
    if _макро_мъртво:
        macro = {k: False for k in MACRO_LBL}
        macro_health["мъртви"] = list(_макро_мъртво)
        refs = _refs(gold_h)
    else:
        macro = _macro(gold_h, gdx_h, dxy_h, rr, health=macro_health); refs = _refs(gold_h)''',
    "О1 · макрото пада безопасно")

rep(LB, '''    regime["streaks"] = _streaks(gold_h, gdx_h, dxy_h, rr)''',
    '''    regime["streaks"] = ({"long": 0, "short": 0} if _макро_мъртво
                         else _streaks(gold_h, gdx_h, dxy_h, rr))''',
    "О1 · стрийковете падат безопасно")

rep(LB, '''    if macro_health.get("мъртви"):
        notes.append("🔴 МЪРТВО МАКРО-КРАЧЕ: " + ", ".join(macro_health["мъртви"])''',
    '''    if _макро_мъртво:
        notes.append("🔴 О1: " + ", ".join(_макро_мъртво) + " не се дърпат — НОВИ ВХОДОВЕ "
                     "СПРЕНИ, но следенето на отворената сделка и изходите вървят")
    if macro_health.get("мъртви"):
        notes.append("🔴 МЪРТВО МАКРО-КРАЧЕ: " + ", ".join(macro_health["мъртви"])''',
    "О1 · бележката го казва")

print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
import ast
ast.parse(io.open(LB, encoding="utf-8").read())
b = io.open(LB, encoding="utf-8").read()
print(f"{LB}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
