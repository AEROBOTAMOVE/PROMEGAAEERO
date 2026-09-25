"""П196 10 · ПЛАТФОРМАТА ЧЕТЕ НОВИТЕ КАРТИ — СЪС СОБСТВЕНИТЕ СИ ЧЕТЦИ.

🔴 24.09 · прегледът на v18.90 · ЗАЩО ТОЗИ ПАЗАЧ СЪЩЕСТВУВА
Четирите реда (ЧЕТИРИ_РЕДА) махнаха три КОТВИ, по които платформата
разпознава сделката, и нито една проба не светна:
  · ВЛЕЗ без «цели X +50 · Y +130»   → data.mjs и app.js дават цели null и
    сделка «+40, после обратно на входа» се брои −130 вместо 0;
  · «🛡 стопът на входа» без «стопа на X» → be40 не се слага (същото −130);
  · затварящата без «сделката донесе» → poziciiOtKarti: pipsove null.
Пробите бяха зелени, защото четяха картите с ЧЕТЕЦА НА БОТА
(`_запис_позиции`). Клиентът ги чете с ЧЕТЦИТЕ НА ПЛАТФОРМАТА — тук се
пускат точно те, през node (виж proba_karti.mjs до този файл).

КАКВО СЕ РЕНДИРА: истинските строители (`_ясна_карта`, `_бе_msg`,
`_exit_msg`, `_карта_без_остаряло`, `_глас`, `_канал`), сглобени както в
main(): едно събитие на рън или няколко в ЕДИН рън (тогава предишните карти
минават през `_карта_без_остаряло`). 11 сделки × ВСЕКИ от 38-те урока в реда
ЗНАНИЕ — защото урок може да носи «покупка» или стрелка, която да излъже
четеца. Картите се лепят към копие на истинския live/sent_log.jsonl.

НИЩО ТУК НЕ ПИПА РЕШЕНИЕ: само текст → четец → число.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

ТУК = Path(__file__).resolve().parent
МОСТ = ТУК / "proba_karti.mjs"
# местните резерви · в CI и двете идват от средата (PATH), а платформата я няма
NODE_МЕСТНО = "C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
КЛИЕНТ_МЕСТНО = "C:/Users/User/Downloads/ЛОЦО/AERO_КЛИЕНТ"
КЛИЕНТ_ФАЙЛОВЕ = ("netlify/functions/_lib/data.mjs", "app.js", "profil2.js")

# (име, посока, рънове, сбор по закона, видът на затварянето, hit.be)
# рън = [(вид, къде)] · къде е име на ниво («tp1», «tp2», «sl»), «вход» или
# отместване в $ ПО ПОСОКА НА СДЕЛКАТА (+ = в наша полза).
# Събития в ЕДИН списък са в ЕДИН рън — точно случаят, който v18.89 сля.
СЦЕНАРИИ = (
    ("покупка · цел 1, после цел 2", "long", [[("tp1", "tp1")], [("tp2", "tp2")]], 130, "tp2", False),
    ("покупка · стоп", "long", [[("sl", "sl")]], -130, "sl", False),
    ("покупка · +40, после обратно на входа", "long", [[("be", 4.0)], [("sl", "вход")]], 0, "sl", True),
    ("продажба · стоп с гап", "short", [[("sl", "sl")]], -130, "sl", False),
    ("продажба · цел 1, после цел 2", "short", [[("tp1", "tp1")], [("tp2", "tp2")]], 100, "tp2", False),
    ("продажба · +40, после обратно на входа", "short", [[("be", 4.0)], [("sl", "вход")]], 0, "sl", True),
    ("покупка · обрат −23", "long", [[("flip", -2.3)]], -23, "flip", False),
    ("продажба · по време +17", "short", [[("time", 1.7)]], 17, "time", False),
    ("покупка · +40 и входът в ЕДИН рън", "long", [[("be", 4.0), ("sl", "вход")]], 0, "sl", True),
    ("продажба · цел 1 и цел 2 в ЕДИН рън", "short", [[("tp1", "tp1"), ("tp2", "tp2")]], 100, "tp2", False),
    ("покупка · +40 и цел 1 в ЕДИН рън, после цел 2", "long",
     [[("be", 4.0), ("tp1", "tp1")], [("tp2", "tp2")]], 130, "tp2", False),
)
# редът «ново влизане» на затварящите — различен, за да мине всеки вид
НОВО_ВЛИЗАНЕ = ("разрешено · забрана няма", "НЕ — 2 стопа в тази посока",
                "НЕ — няма активен сигнал.", "")


def намери_node():
    """node: $AERO_NODE → PATH → местната резерва. None = НЯМА (пазачът пали червено)."""
    for _к in (os.environ.get("AERO_NODE"), shutil.which("node"), NODE_МЕСТНО):
        if _к and Path(_к).is_file():
            return str(_к)
    return None


def намери_клиент(репо="."):
    """Живата платформа на този диск: $AERO_KLIENT → ../AERO_КЛИЕНТ → местната резерва."""
    for _к in (os.environ.get("AERO_KLIENT"), str(Path(репо).resolve().parent / "AERO_КЛИЕНТ"),
               КЛИЕНТ_МЕСТНО):
        if _к and all((Path(_к) / _ф).is_file() for _ф in КЛИЕНТ_ФАЙЛОВЕ):
            return str(Path(_к))
    return None


def намери_база(репо="."):
    """Истинският запис за фон: live/sent_log.jsonl; празен ли е (ботът го
    архивира в началото на месеца) → най-новият live/archive/sent_log-*.jsonl."""
    _ж = Path(репо) / "live" / "sent_log.jsonl"
    if _ж.is_file() and _ж.stat().st_size > 0:
        return _ж
    _а = sorted((Path(репо) / "live" / "archive").glob("sent_log-*.jsonl"))
    return _а[-1] if _а else None


def _utc(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S")


def начало_след(база_текст):
    """Първият час на новите карти: два дни след последния ред на базата, 05:00 UTC,
    в делник преди петък (петъчната вечерна бележка е отделна проба)."""
    _мак = None
    for _л in база_текст.splitlines():
        try:
            _u = str(json.loads(_л).get("utc") or "")[:19]
            _t = datetime.fromisoformat(_u)
        except Exception:
            continue
        _мак = _t if _мак is None or _t > _мак else _мак
    _т = (_мак or datetime(2026, 10, 4)) + timedelta(days=2)
    _т = _т.replace(hour=5, minute=0, second=0, microsecond=0)
    while _т.weekday() > 1:             # понеделник или вторник: 42 часа без петък вечер
        _т += timedelta(days=1)
    return _т


def рендирай_урок(lb, урок, начало, цена0):
    """Картите на 11-те сделки за ЕДИН урок → (записи за sent_log, очаквани)."""
    записи, очаквани = [], []

    def _запис(таг, текст, t):
        _к = bool(lb._канал(таг, текст)[0])      # `_канал` съди ПРЕДИ `_глас`, както в пощата
        _з = {"utc": _utc(t), "tag": таг, "text": lb._глас(таг, текст, ключ=_utc(t)), "kanal": _к}
        # v18.93 · Н-08 · записът `d` на картата — както го пише пощата (`_outbox_flush`)
        _д = (lb._д_на(текст) if getattr(lb, "_д_за_таг", None) and lb._д_за_таг(таг) else None)
        if _д is not None:
            _з["d"] = _д
        записи.append(_з)

    for _j, _сц in enumerate(СЦЕНАРИИ):
        _рн, _оч = рънове_на_сделка(lb, _j, _сц, начало, цена0, урок)
        for _t, _карти in _рн:
            for _таг, _текст in _карти:
                _запис(_таг, _текст, _t)
        очаквани.append(_оч)
    return записи, очаквани


def рънове_на_сделка(lb, _j, сценарий, начало, цена0, урок=None):
    """Картите на ЕДНА сделка от СЦЕНАРИИ, сглобени дословно както в main():
    → (рънове [(час, [(таг, карта)])], очаквано). Картата е тази, която дава
    строителят (след `_карта_без_остаряло`) — ПРЕДИ пощата и `_глас` (v18.93:
    П199 я прекарва и през истинската поща)."""
    _име, _d, _рънове, _сбор, _вид, _бе = сценарий
    _t0 = начало + timedelta(minutes=6 * _j)
    _е = round(цена0 + 1.13 * _j, 2)
    _зн = 1.0 if _d == "long" else -1.0
    lv = dict(lb._levels(_е, _d))
    _сиг = lb._ясна_карта(_d, _е, dict(lv), "бърз ±$10/10мин" if _j % 3 == 0 else "", None,
                          {"mid": _е}, _t0.strftime("%Y-%m-%dT%H:%M"))
    рънове = [(_t0, [("signal", _сиг)])]
    тр = {"direction": _d, "entry": _е, "opened": _t0.strftime("%Y-%m-%dT%H:%M"),
          "checked": _t0.strftime("%Y-%m-%dT%H:%M"), "levels": dict(lv), "hit": {},
          "status": "open", "v2": True, "ledger": "spot", "tier": "strong",
          "date": _t0.strftime("%Y-%m-%d"), "sym": "XAUUSD"}
    for _р, _рън in enumerate(_рънове):
        _t = _t0 + timedelta(minutes=_р + 1)
        _кога = _t.strftime("%Y-%m-%dT%H:%M")
        _през = "бар" if (_j + _р) % 2 == 0 else "спот"
        # ── дословно main(): снимка на сделката в началото на рън-а ──
        _сн = copy.deepcopy(тр)
        _хит = dict(_сн["hit"])
        _бе_к = _сн.get("be_rano")
        _изх = []
        for _к, _къде in _рън:
            if isinstance(_къде, str):
                _px = _е if _къде == "вход" else float(lv[_къде])
            else:
                _px = round(_е + _зн * float(_къде), 2)
            _гап = bool(_име.endswith("с гап"))
            if _к == "be":
                _бе_к = _кога
                _об = dict(_сн)
                _об["hit"] = dict(_хит)
                _об["levels"] = dict(_сн["levels"])
                _об["levels"]["sl"] = _сн["entry"]
                _об["be_rano"] = _кога
                _изх.append(("exit-be", ("be", _об, _px, _кога, _през, _гап), "be", _d))
                continue
            if _к in lb._цели():
                _хит[_к] = True
            _об = dict(_сн)
            _об["hit"] = dict(_хит)
            _об["levels"] = dict(_сн["levels"])
            if _хит.get("tp1"):
                _об["levels"]["sl"] = _сн["entry"]
            if _бе_к:
                _об["levels"]["sl"] = _сн["entry"]
                _об["be_rano"] = _бе_к
            _изх.append(("exit:" + _к, (_к, _об, _px, _кога, _през, _гап), _к, _d))
        _карти = []
        for _i, (_таг, _пл, _к, _) in enumerate(_изх):
            _k, _тро, _px, _w, _via, _gap = _пл
            _сл = lb._следващ_изход(_изх, _i)
            if _k == "be":
                _текст = lb._карта_без_остаряло(lb._бе_msg(_тро, _w, _via), _сл)
            else:
                _nl = НОВО_ВЛИЗАНЕ[(_j + _р) % len(НОВО_ВЛИЗАНЕ)] if _k in lb._затваря() else ""
                _nl = lb._ред_ново_влизане(_nl, None, _тро.get("direction"))
                _текст = lb._карта_без_остаряло(
                    lb._exit_msg(_k, _тро, _px, _w, _via, _gap, spot={"mid": _px},
                                 next_line=_nl, оставащи=0), _сл)
            _карти.append((_таг, _текст))
        рънове.append((_t, _карти))
        # ── след рън-а: каквото `track_trade` оставя в сделката ──
        тр["hit"] = _хит
        if _бе_к:
            тр["be_rano"] = _бе_к
        if _хит.get("tp1") or _бе_к:
            тр["levels"]["sl"] = тр["entry"]
    очаквано = {"име": _име, "урок": урок, "dir": _d, "entry": _е,
                "tp1": round(float(lv["tp1"]), 2), "tp2": round(float(lv["tp2"]), 2),
                "sl": round(float(lv["sl"]), 2), "сбор": _сбор, "вид": _вид, "бе": _бе}
    return рънове, очаквано


def рендирай_всички(lb, начало, уроци=None):
    """Всеки урок от библиотеката ЗНАНИЕ върху всичките 11 сделки.
    Урокът се подава, като `_знание` се подменя за миг — така ВСЯКА карта
    минава с ВСЕКИ урок, а не само с онзи, който часът ѝ завърта."""
    _б = lb.ЗНАНИЕ_БИБЛИОТЕКА
    _ст = lb._знание
    записи, очаквани, по_урок = [], [], []
    try:
        for _у in (range(len(_б)) if уроци is None else уроци):
            lb._знание = (lambda _т="", _к="", _x=_б[_у]: _x)
            _з, _о = рендирай_урок(lb, _у, начало + timedelta(minutes=70 * _у),
                                   3100.0 + 17.31 * _у)
            записи += _з
            очаквани += _о
            по_урок.append((_у, _з, _о))
    finally:
        lb._знание = _ст
    return записи, очаквани, по_урок


def пиши(път, записи, база=""):
    with open(път, "w", encoding="utf-8", newline="\n") as _ф:
        if база:
            _ф.write(база.rstrip("\n") + "\n")
        for _з in записи:
            _ф.write(json.dumps(_з, ensure_ascii=False) + "\n")


def node_чете(node, извор, база_п, пълен_п, от):
    """Един рън на node · (резултат, грешка). Грешката е ТЕКСТ, никога тишина."""
    try:
        _р = subprocess.run([node, str(МОСТ), "cheti", str(извор), str(база_п), str(пълен_п), от],
                            capture_output=True, timeout=180, encoding="utf-8", errors="replace")
    except Exception as _е:
        return None, "node не тръгна: %s: %s" % (type(_е).__name__, str(_е)[:160])
    _ред = (_р.stdout or "").strip().splitlines()
    try:
        _j = json.loads(_ред[-1]) if _ред else None
    except Exception:
        _j = None
    if _р.returncode != 0 or not isinstance(_j, dict) or "greshka" in _j:
        return None, "node код %s: %s %s" % (_р.returncode, (_j or {}).get("greshka", "")[:300],
                                              (_р.stderr or "")[-300:])
    return _j, None


def node_сверка(node, клиент):
    try:
        _р = subprocess.run([node, str(МОСТ), "sverka", str(клиент)], capture_output=True,
                            timeout=120, encoding="utf-8", errors="replace")
        return json.loads(_р.stdout.strip().splitlines()[-1])
    except Exception as _е:
        return {"greshka": "%s: %s" % (type(_е).__name__, str(_е)[:160])}


def _ключ(dir_, entry):
    return ("long" if dir_ in ("long", 1) else "short", round(float(entry), 2))


def _примери(лоши, n=3):
    return ("" if not лоши else " · НАПР. " + " | ".join(str(x) for x in лоши[:n])
            + (" …(+%d)" % (len(лоши) - n) if len(лоши) > n else ""))


def съди(рез, очаквани, етикет):
    """Резултатът на node срещу очакваното → [(име на проверката, вярно ли е)]."""
    П = []
    _N = len(очаквани)
    _оч = {_ключ(о["dir"], о["entry"]): о for о in очаквани}
    _им = lambda о: "урок %d · %s" % (о["урок"], о["име"])

    # ── сървърът · data.mjs · sdelkiOtKarti ──
    _сд = {_ключ(x["direction"], x["entry"]): x for x in рез.get("sdelki", [])}
    _липса = [_им(о) for к, о in _оч.items() if к not in _сд]
    П.append(("П196 10 · %s · data.mjs sdelkiOtKarti · всяка от %d-те сделки е разпозната%s"
              % (етикет, _N, _примери(_липса)), not _липса and len(_сд) == _N))
    _нива = [_им(о) for к, о in _оч.items() if к in _сд
             and (_сд[к]["tp1"] is None or _сд[к]["tp2"] is None
                  or abs(_сд[к]["tp1"] - о["tp1"]) > 0.006 or abs(_сд[к]["tp2"] - о["tp2"]) > 0.006)]
    П.append(("П196 10 · %s · data.mjs · цел 1 и цел 2 от картата ВЛЕЗ (не null, точните нива)%s"
              % (етикет, _примери(_нива)), not _липса and not _нива))
    _сб = [(_им(о), _сд[к]["sum"], о["сбор"]) for к, о in _оч.items()
           if к in _сд and _сд[к]["sum"] != о["сбор"]]
    _общо = sum(_сд[к]["sum"] for к in _оч if к in _сд)
    П.append(("П196 10 · %s · data.mjs · сборът по закона (−130/+130/+100/0/−23/+17) · общо %+d, "
              "очаквано %+d%s" % (етикет, _общо, sum(о["сбор"] for о in очаквани), _примери(_сб)),
              not _липса and not _сб))
    _бе = [_им(о) for к, о in _оч.items() if к in _сд and bool((_сд[к]["hit"] or {}).get("be")) != о["бе"]]
    П.append(("П196 10 · %s · data.mjs · hit.be е точно при нулата след +40 (%d сделки)%s"
              % (етикет, sum(1 for о in очаквани if о["бе"]), _примери(_бе)), not _липса and not _бе))
    _вид = [(_им(о), _сд[к]["exit_kind"]) for к, о in _оч.items()
            if к in _сд and _сд[к]["exit_kind"] != о["вид"]]
    П.append(("П196 10 · %s · data.mjs · видът на затварянето%s" % (етикет, _примери(_вид)),
              not _липса and not _вид))
    _б, _п = рез.get("baza", {}), рез.get("pylen", {})
    П.append(("П196 10 · %s · data.mjs · нито една нова карта не е «непрочетена» (%d)%s"
              % (етикет, len(рез.get("neprochetni_novi") or []), _примери(рез.get("neprochetni_novi") or [])),
              not рез.get("neprochetni_novi") and _п.get("bezVhod") == _б.get("bezVhod")
              and _п.get("ostatak") == _б.get("ostatak")))
    П.append(("П196 10 · %s · data.mjs · старите сделки от истинския запис са непокътнати" % етикет,
              рез.get("stari_nepipnati") is True))

    # ── сървърът · data.mjs · poziciiOtKarti (числото, което БОТЪТ е написал) ──
    # ВСИЧКИ нови позиции, не само последната на вход: една сделка, разцепена на
    # две позиции (едната без число), иначе би се скрила зад речника
    _всп = [x for x in рез.get("pozicii", []) if x.get("slot") == 1]
    _пз = {_ключ(x["direction"], x["entry"]): x for x in _всп}
    _пл = [_им(о) for к, о in _оч.items() if к not in _пз]
    _нул = [(x["direction"], x["entry"], x["kraj"]) for x in _всп if x["pipsove"] is None]
    _пч = [(_им(о), _пз[к]["pipsove"], о["сбор"]) for к, о in _оч.items()
           if к in _пз and _пз[к]["pipsove"] is not None and _пз[к]["pipsove"] != о["сбор"]]
    _дн = [_им(о) for к, о in _оч.items() if к in _пз and not _пз[к]["daden"]]
    _dn = (_п.get("neprochetni_p", 0) - _б.get("neprochetni_p", 0))
    П.append(("П196 10 · %s · data.mjs poziciiOtKarti · 0 непрочетени от новите (%+d)%s"
              % (етикет, _dn, _примери(_пл)), _dn == 0 and not _пл
              and _п.get("otvoreni_p") == _б.get("otvoreni_p")))
    П.append(("П196 10 · %s · data.mjs poziciiOtKarti · pipsove не е null и сделката е ЕДНА позиция "
              "(%d/%d позиции с число, очаквани %d)%s"
              % (етикет, len(_всп) - len(_нул), len(_всп), _N, _примери(_нул)),
              not _пл and not _нул and len(_всп) == _N))
    П.append(("П196 10 · %s · data.mjs poziciiOtKarti · числото на картата = закона%s"
              % (етикет, _примери(_пч)), not _пл and not _пч))
    П.append(("П196 10 · %s · data.mjs poziciiOtKarti · всяка е ДАДЕН сигнал (има ВЛЕЗ)%s"
              % (етикет, _примери(_дн)), not _пл and not _дн))

    # ── екранът · app.js и profil2.js · vhodOt върху картата ВЛЕЗ ──
    for _ф, _кл in (("app.js", "vhod_app"), ("profil2.js", "vhod_profil2")):
        _вх = рез.get(_кл) or []
        _лв = [x.get("utc") for x in _вх if x.get("nishto")]
        _ц = {_ключ(x["dir"], x["entry"]): x for x in _вх if not x.get("nishto")}
        _лц = [_им(о) for к, о in _оч.items()
               if к not in _ц or len(_ц[к]["tp"]) != 2
               or abs(_ц[к]["tp"][0] - о["tp1"]) > 0.006 or abs(_ц[к]["tp"][1] - о["tp2"]) > 0.006
               or _ц[к]["sl"] is None or abs(_ц[к]["sl"] - о["sl"]) > 0.006]
        П.append(("П196 10 · %s · %s vhodOt · %d/%d карти ВЛЕЗ дават вход, стоп, цел 1 и цел 2%s"
                  % (етикет, _ф, _N - len(_лц), _N, _примери(_лц)),
                  len(_вх) == _N and not _лв and not _лц))

    # ── екранът · app.js · ledgerOt върху сделките на сървъра ──
    _лг = {_ключ(x["dir"], x["entry"]): x for x in рез.get("ledger", [])}
    _лл = [(_им(о), (_лг.get(к) or {}).get("sbor"), о["сбор"]) for к, о in _оч.items()
           if к not in _лг or _лг[к]["sbor"] != о["сбор"]]
    П.append(("П196 10 · %s · app.js ledgerOt · сборът на екрана = закона (%d/%d)%s"
              % (етикет, _N - len(_лл), _N, _примери(_лл)), not _лл))

    # ── екранът · app.js и profil2.js · пътят на картите (там живее «стопа на X») ──
    for _ф, _кл in (("app.js", "app_karti"), ("profil2.js", "profil2_karti")):
        _к = {_ключ(x["dir"], x["entry"]): x for x in рез.get(_кл, [])}
        _кл_ = [(_им(о), (_к.get(к) or {}).get("zatv"), (_к.get(к) or {}).get("ch"), о["сбор"])
                for к, о in _оч.items()
                if к not in _к or not _к[к]["zatv"] or not _к[к]["ch"] or _к[к]["ch"][0] != о["сбор"]
                or (о["бе"] and not _к[к]["be40"])]
        П.append(("П196 10 · %s · %s sglobiSdelki · затворени, с «стопа на X» и точния сбор (%d/%d)%s"
                  % (етикет, _ф, _N - len(_кл_), _N, _примери(_кл_)), not _кл_))
    return П


def запис_на_бота(lb, по_урок, пълен_п, от_ден, очаквани):
    """`_запис_позиции` (четецът на бота) · по урок и върху целия запис."""
    П = []
    _лоши = []
    _д = Path(tempfile.mkdtemp(prefix="p196_10z_"))
    try:
        for _у, _з, _о in по_урок:
            пиши(_д / "sent_log.jsonl", _з)
            _гл, _ = lb._запис_позиции(_д, от_ден="2000-01-01")
            if not _гл or _гл.get("n") != len(_о) or _гл.get("пипса") != sum(x["сбор"] for x in _о):
                _лоши.append("урок %d → %s" % (_у, _гл))
        _дд = Path(tempfile.mkdtemp(prefix="p196_10p_"))
        try:
            shutil.copy(пълен_п, _дд / "sent_log.jsonl")
            _гл2, _ = lb._запис_позиции(_дд, от_ден=от_ден)
        finally:
            shutil.rmtree(_дд, ignore_errors=True)
    finally:
        shutil.rmtree(_д, ignore_errors=True)
    П.append(("П196 10 · записът на бота (`_запис_позиции`) · всеки урок · 11 сделки и "
              "точните пипса%s" % _примери(_лоши), not _лоши))
    _оч_n, _оч_п = len(очаквани), sum(x["сбор"] for x in очаквани)
    П.append(("П196 10 · записът на бота · върху истинския запис + новите: %s (очаквано n=%d, %+d)"
              % (_гл2, _оч_n, _оч_п),
              bool(_гл2) and _гл2.get("n") == _оч_n and _гл2.get("пипса") == _оч_п))
    return П


def мутанти(node, lb, начало):
    """Пазачът не бива да е празен: връщат се ТРИТЕ счупвания в самия текст
    (без котвата) и всяко трябва да светне. Един урок стига — котвите не зависят от него."""
    _з, _о, _ = рендирай_всички(lb, начало, уроци=[0])
    _мут = {
        "без «цели» във ВЛЕЗ": lambda z: dict(z, text=z["text"].replace("цели ", "нива "))
        if z["tag"] == "signal" else z,
        "без «стопа на» в щита": lambda z: dict(z, text=z["text"].replace("стопа на", "стопът е на"))
        if z["tag"] == "exit-be" else z,
        "без «сделката донесе» в изхода": lambda z: dict(z, text=z["text"].replace("сделката донесе ", ""))
        if z["tag"].startswith("exit:") else z,
    }
    П = []
    _д = Path(tempfile.mkdtemp(prefix="p196_10m_"))
    try:
        for _име, _ф in _мут.items():
            пиши(_д / "baza.jsonl", [])
            # 25.09 · Н-08 · от v18.93 платформата брои от `d`, а не от думите. Мутантите
            # пазят ПЪТЯ ПО ДУМИТЕ (старите карти, RECORD_DATA=0) — затова без `d`.
            пиши(_д / "pylen.jsonl", [_ф({_к: _в for _к, _в in x.items() if _к != "d"}) for x in _з])
            _р, _гр = node_чете(node, "snimka", _д / "baza.jsonl", _д / "pylen.jsonl", _utc(начало))
            _черв = [и.split(" · НАПР.")[0].replace("П196 10 · мутант · ", "")[:90]
                     for и, ок in (съди(_р, _о, "мутант") if _р else []) if not ок]
            П.append(("П196 10 · пазачът лови мутанта «%s» (%d червени: %s)"
                      % (_име, len(_черв), " | ".join(_черв)),
                      bool(_р) and not _гр and len(_черв) > 0))
    finally:
        shutil.rmtree(_д, ignore_errors=True)
    return П


def провери(lb, репо=".", node=None, клиент=None, база_п=None):
    """Целият пазач · → ([(име, вярно)], обобщение). Нищо не хвърля навън."""
    П = []
    node = node or намери_node()
    П.append(("П196 10 · node го има (%s) — без него платформата НЕ Е проверена: червено, не тихо зелено"
              % (node or "НЯМА: сложи node в PATH или AERO_NODE"), bool(node)))
    if not node:
        return П, {"node": None}
    клиент = клиент if клиент is not None else намери_клиент(репо)
    база_п = Path(база_п) if база_п else намери_база(репо)
    база = база_п.read_text(encoding="utf-8") if база_п and база_п.is_file() else ""
    начало = начало_след(база)
    от = _utc(начало)
    записи, очаквани, по_урок = рендирай_всички(lb, начало)
    # базата е само фон (старите карти да не пречат, новите да не бутат старите):
    # празна база (напр. часове след месечния архив) НЕ е грешка и не спира бота
    П.append(("П196 10 · рендирани %d карти: %d урока × %d сделки = %d (база: %s, %d реда)"
              % (len(записи), len(lb.ЗНАНИЕ_БИБЛИОТЕКА), len(СЦЕНАРИИ), len(очаквани),
                 база_п.as_posix() if база_п else "няма", len(база.splitlines())),
              len(очаквани) == len(lb.ЗНАНИЕ_БИБЛИОТЕКА) * len(СЦЕНАРИИ) and len(очаквани) > 0))
    обоб = {"node": node, "клиент": клиент, "от": от, "карти": len(записи), "сделки": len(очаквани),
            "очакван_сбор": sum(о["сбор"] for о in очаквани)}
    _д = Path(tempfile.mkdtemp(prefix="p196_10_"))
    try:
        пиши(_д / "baza.jsonl", [], база)
        пиши(_д / "pylen.jsonl", записи, база)
        извори = [("снимка", "snimka")] + ([("живо", клиент)] if клиент else [])
        for _ет, _изв in извори:
            _р, _гр = node_чете(node, _изв, _д / "baza.jsonl", _д / "pylen.jsonl", от)
            П.append(("П196 10 · %s · node чете (%s)%s" % (_ет, (_р or {}).get("otkade", ""),
                                                          (" · " + _гр) if _гр else ""), bool(_р)))
            if _р:
                П += съди(_р, очаквани, _ет)
                обоб[_ет] = _р
        if клиент:
            _св = node_сверка(node, клиент)
            П.append(("П196 10 · снимката в platforma/ = живите четци на платформата %s · ако е червено: "
                      "node platforma/proba_karti.mjs snimka <AERO_КЛИЕНТ>" % json.dumps(_св, ensure_ascii=False),
                      isinstance(_св, dict) and all(_св.get(_к) is True for _к in ("data", "app", "profil2"))))
        else:
            # в CI платформата я няма: проверена е СНИМКАТА, и това се КАЗВА
            print("П196 10 · платформата я няма на този диск — проверени са СНИМКИТЕ в platforma/")
        П += запис_на_бота(lb, по_урок, _д / "pylen.jsonl",
                           (начало + timedelta(hours=3)).strftime("%Y-%m-%d"), очаквани)
        П += мутанти(node, lb, начало)
    finally:
        shutil.rmtree(_д, ignore_errors=True)
    return П, обоб
