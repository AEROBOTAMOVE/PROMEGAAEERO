# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════
 AERO · БЪЛГАРСКИЯТ РЕД НА НОВИНИТЕ · по правила, без модел · 29.09.2026
───────────────────────────────────────────────────────────────────────────
 ЗАЩО
 Заглавията идват на английски: в live/novini.json на 29.09 — 0 от 200 с
 кирилица. Клиентът е българин и нов в търговията. Модел няма и няма да има,
 затова редът се строи от ПРАВИЛА: по заглавието и по емисията се разпознава
 събитието и се пише едно кратко изречение от готови български думи.

 ЗАКОНЪТ НА РЕДА
   · правило, което не е сигурно, НЕ пише → "bg": null. Празен ред е по-добър
     от грешен. Платформата тогава показва само оригинала с източника;
   · никакви числа от заглавието (седем седмици, 2-month, 4%, $4,300) —
     числото се копира грешно и тогава е измислено. Периодът става дума:
     «от седмици», «от месеци», «от години»;
   · никакво «ще», никаква причина, която заглавието не казва. Връзката е
     «на фона на» — заглавието казва «as/amid», не «because»;
   · човек се назовава САМО ако е в списъка с хората на Фед (_FED_UNIKALNI,
     _FED_DVUSMISLENI) и е ПОДЛОГЪТ на заглавието (_podlog: в началото, след
     етикет, или «…, Fed's X says» в края). Двусмислените имена (Cook, Barr,
     Williams…) искат «Fed» точно пред името; уникалните (Warsh, Kashkari…) —
     «Fed» някъде в заглавието. Или е в емисията на речите на самия Фед;
   · мирът и войната: отхвърлено/рухнало примирие е напрежение; и напрежение,
     и успокояване в едно заглавие → без фон; геополитиката никога не е «преди»;
   · държава се казва само ако заглавието я казва (US, U.S., Fed…) или ако
     данните по природа са само американски (PCE, JOLTS, NFP, ISM);
   · оригиналното заглавие остава непипнато — редът е ДО него, не вместо него.

 ЕЗИКЪТ НА ИЗТОЧНИКА · ezik_ok()
   Пускат се английски и български. Друга писменост в заглавието или в името
   на изданието (корейска, китайска, арабска…), руски/украински букви в
   кирилицата, виетнамски знаци или ясни думи на друг латински език → новината
   не влиза. Мерено 29.09 в live/novini.json: 6 от 200 бяха от 매일경제 (×2),
   조선일보, 富途牛牛, 深潮TechFlow и صوت الإمارات; при живото пускане се хвана и «Межа. Новини України.».

 ПРОВЕРКА: python -X utf8 novini_bg.py --proveri [път/до/novini.json]
 ПЪТ НАЗАД: BG_RED = 0 в novini_sbirach.py → полето "bg" не се пише и
 езиковото сито не маха нищо (дословно поведението до 29.09).
═══════════════════════════════════════════════════════════════════════════
"""

import re
import sys
import unicodedata
from datetime import datetime, timezone

_I = re.IGNORECASE


def _r(p, fl=_I):
    return re.compile(p, fl)


# ══════════════════════════════════════════════════════════════════════════
#  1 · ЕЗИКЪТ
# ══════════════════════════════════════════════════════════════════════════

_KIRILICA = re.compile(r"[А-Яа-я]")
# букви, които българският няма: руски, украински, сръбски, македонски, беларуски
_CHUZHDA_KIRILICA = re.compile(r"[ыЫэЭёЁіІїЇєЄґҐђЂћЋџЏљЉњЊјЈўЎѓЃќЌѕЅ]")
_RUSKI_DUMI = frozenset("что это для будет также году золото нефть цены после сегодня".split())
_VIETNAMSKI = re.compile(r"[ơƠưƯđĐăĂạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]")
_OSOBENI = re.compile(r"[ąćęłńśźżĄĆĘŁŃŚŹŻřěůňťďŘĚŮŇŤĎığşİĞŞțșȚȘ]")
_EN = frozenset(("the a an of to in on for as and is are at by with from after amid near over its how "
                 "what why be has have says will this that could may into up down new you your it not "
                 "than more but or just all can about").split())
# Без думите, които се срещат и в английско заглавие: au (Au — златото), per (per ounce),
# est (EST), em (EM — развиващите се пазари), mit (MIT), von/van (имена), yang/dan (имена),
# es/se/os/dos/del/mas/y/do (съкращения и английски думи).
_CHUZHDI = frozenset((
    "el los las que por para con una lo su sus pero más como sobre entre "                    # испански
    "das não nao uma ao pelo pela "                                                             # португалски
    "le les des du et pour sur dans aux une pas qui avec "                                      # френски
    "der und für fur ist zu dem auf ein eine nicht im bei auch "                               # немски
    "il della di che dei delle nel sul gli "                                                    # италиански
    "het een voor niet zijn "                                                                   # нидерландски
    "dari untuk dengan harga emas naik turun").split())                                         # индонезийски
_DOPUSTIMI_ZNACI = ("MICRO SIGN", "FEMININE ORDINAL INDICATOR", "MASCULINE ORDINAL INDICATOR")


def _pismo_ok(s):
    """Всяка буква да е латиница или кирилица. Хангъл, йероглифи, арабски,
       иврит, тайландски, деванагари… → не."""
    for ch in str(s or ""):
        if ch.isalpha():
            ime = unicodedata.name(ch, "")
            if not (ime.startswith("LATIN") or ime.startswith("CYRILLIC") or ime in _DOPUSTIMI_ZNACI):
                return False
    return True


def ezik_ok(zaglavie, izvor=None):
    """True → заглавието е на английски или на български и изданието е с
       латинско или кирилско име. Всичко друго → False (новината не влиза)."""
    z = str(zaglavie or "")
    if not z.strip():
        return False
    if not _pismo_ok(z) or not _pismo_ok(izvor):
        return False
    # изданието на кирилица, но не на български: «Межа. Новини України.» (живо, 29.09)
    if _CHUZHDA_KIRILICA.search(str(izvor or "")) or any(
            d in _RUSKI_DUMI for d in re.findall(r"[а-я]+", str(izvor or "").lower())):
        return False
    if _KIRILICA.search(z):
        if _CHUZHDA_KIRILICA.search(z):
            return False
        return not any(d in _RUSKI_DUMI for d in re.findall(r"[а-я]+", z.lower()))
    if _VIETNAMSKI.search(z):
        return False
    dumi = re.findall(r"[^\W\d_]+", z.lower())
    en = sum(1 for d in dumi if d in _EN)
    chuzhdi = sum(1 for d in dumi if d in _CHUZHDI)
    if chuzhdi >= 2 and chuzhdi > en:
        return False
    if len(_OSOBENI.findall(z)) >= 2 and en < 2:
        return False
    return True


# ══════════════════════════════════════════════════════════════════════════
#  2 · ОБЩИТЕ ПАРЧЕТА
# ══════════════════════════════════════════════════════════════════════════

def _norm(z):
    """Кавички, интервали, отрязана опашка. Google реже заглавия с «…» или «..»
       по средата на дума («…possible Fed rat...») — последната дума преди
       многоточието не се чете, за да не се хване половин дума."""
    t = str(z or "")
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), (" ", " "), ("—", " - "), ("–", " - ")):
        t = t.replace(a, b)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^[^\w\"'(]+", "", t)     # «🟡Gold gains…» — знакът отпред не е част от заглавието
    if re.search(r"(?:\.\.\.?|…)$", t):
        t = re.sub(r"\s*\S*(?:\.\.\.?|…)$", "", t).strip()
    return t


# ── държавата ─────────────────────────────────────────────────────────────
# САЩ по белезите в заглавието. «US» е с ГЛАВНИ букви (без флаг I), иначе
# местоимението «us» щеше да прави всяко заглавие американско.
_SASHT = re.compile(r"\bUS\b|\bU\.S\.|\bUSA\b|\bAmerica(?:n|ns)?\b|\bFed\b|\bFederal Reserve\b|\bFOMC\b|"
                    r"\bWall St(?:reet|\.)?\b|\bMichigan\b|\bConference Board\b")
_DRZHAVI = (
    (r"\b(?:UK|U\.K\.|Britain|British|England|BoE|Bank of England)\b", "във Великобритания"),
    (r"\b(?:euro ?zone|euro area|Eurozone|ECB)\b", "в еврозоната"),
    (r"\b(?:Germany|German)\b", "в Германия"),
    (r"\b(?:Japan|Japanese|BoJ|BOJ|Bank of Japan)\b", "в Япония"),
    (r"\b(?:China|Chinese|PBOC|PBoC)\b", "в Китай"),
    (r"\b(?:Canada|Canadian|BoC|Bank of Canada)\b", "в Канада"),
    (r"\b(?:Australia|Australian|Aussie|RBA)\b", "в Австралия"),
    (r"\b(?:India|Indian|RBI)\b", "в Индия"),
    (r"\b(?:France|French)\b", "във Франция"),
    (r"\b(?:Mexico|Mexican|Banxico)\b", "в Мексико"),
    (r"\b(?:Brazil|Brazilian)\b", "в Бразилия"),
    (r"\b(?:Turkey|Turkish|Türkiye)\b", "в Турция"),
    (r"\b(?:South Korea|Korea|Korean)\b", "в Южна Корея"),
    (r"\b(?:Switzerland|Swiss|SNB)\b", "в Швейцария"),
    (r"\b(?:New Zealand|RBNZ)\b", "в Нова Зеландия"),
    (r"\b(?:Italy|Italian)\b", "в Италия"),
    (r"\b(?:Spain|Spanish)\b", "в Испания"),
    (r"\b(?:Russia|Russian)\b", "в Русия"),
    (r"\b(?:Sweden|Swedish|Riksbank)\b", "в Швеция"),
    (r"\b(?:Norway|Norwegian|Norges)\b", "в Норвегия"),
    (r"\b(?:Poland|Polish)\b", "в Полша"),
    (r"\bSouth Africa(?:n)?\b", "в Южна Африка"),
    (r"\b(?:Singapore)\b", "в Сингапур"),
)
_DRZHAVI_RE = tuple((re.compile(p), bg) for p, bg in _DRZHAVI)
# други държави, за които няма дума тук: щом ги има, «в САЩ» НЕ се казва
_DRUGI_DRZHAVI = re.compile(r"\b(?:Argentina|Chile|Peru|Colombia|Indonesia|Malaysia|Thailand|Vietnam|Philippines|"
                            r"Pakistan|Egypt|Nigeria|Kenya|Ghana|Saudi|UAE|Emirates|Israel|Iran|Ukraine|Taiwan|"
                            r"Hong Kong|Netherlands|Dutch|Ireland|Irish|Austria|Belgium|Denmark|Finland|Greece|"
                            r"Hungary|Czech|Romania|Bulgaria|Vietnam|Qatar|Kuwait|Oman|Jordan|Kazakhstan|Uzbekistan)\b")


def _drzhava(t, samo_sasht=False):
    """« в САЩ» / « в еврозоната» / "" — само когато е ясно. Две и повече
       държави в заглавието → нищо (не се знае за коя са данните)."""
    drugi = [bg for rx, bg in _DRZHAVI_RE if rx.search(t)]
    ima_drugi = bool(drugi) or bool(_DRUGI_DRZHAVI.search(t))
    sasht = bool(_SASHT.search(t))
    if sasht and not ima_drugi:
        return " в САЩ"
    if not sasht and len(drugi) == 1 and not _DRUGI_DRZHAVI.search(t):
        return " " + drugi[0]
    if not sasht and not ima_drugi and samo_sasht:
        return " в САЩ"
    return ""


# ── условното: «ако», «може», «очаква се» — тогава събитието НЕ е станало ──
_USLOVNO = _r(r"\b(?:if|when|whether|unless|until|before|could|would|should|may|might|will|won't|"
              r"expected|expects?|expecting|likely|unlikely|set to|poised|on track|odds|bets?|betting|"
              r"chances?|probability|fears?|hopes?|forecasts?|predicts?|seen|await\w*|ahead|next|"
              r"wants?|urges?|pushes|pressure|demands?|calls? for|case for|to (?:hike|raise|cut|lower))\b|\?")


# ══════════════════════════════════════════════════════════════════════════
#  3 · ФЕД
# ══════════════════════════════════════════════════════════════════════════

FED_EMISII = ("Fed всички", "Fed политика", "Fed речи")

# Хората на Фед: управителите и шефовете на 12-те регионални банки (към 09.2026).
# Имената, които се срещат и извън Фед (Cook — Apple, Barr — бивш министър,
# Williams, Collins, Daly, Logan, Paulson — бивш министър на финансите…), се
# приемат САМО с «Fed» точно пред тях. Уникалните — и с «Fed» другаде в заглавието.
_FED_UNIKALNI = ("Powell", "Warsh", "Jefferson", "Bowman", "Waller", "Kugler", "Miran", "Musalem",
                 "Hammack", "Goolsbee", "Kashkari", "Schmid", "Bostic", "Barkin")
_FED_DVUSMISLENI = ("Cook", "Barr", "Williams", "Collins", "Daly", "Logan", "Paulson", "Harker")
_FED_IMENA = {"Lisa": "Cook", "Michael": "Barr", "John": "Williams", "Susan": "Collins", "Mary": "Daly",
              "Lorie": "Logan", "Anna": "Paulson", "Kevin": "Warsh", "Jerome": "Powell", "Jay": "Powell",
              "Philip": "Jefferson", "Michelle": "Bowman", "Christopher": "Waller", "Chris": "Waller",
              "Adriana": "Kugler", "Stephen": "Miran", "Alberto": "Musalem", "Beth": "Hammack",
              "Austan": "Goolsbee", "Neel": "Kashkari", "Jeffrey": "Schmid", "Jeff": "Schmid",
              "Raphael": "Bostic", "Tom": "Barkin", "Thomas": "Barkin", "Patrick": "Harker"}
_VSICHKI_FED = _FED_UNIKALNI + _FED_DVUSMISLENI
_IME = r"(?:(?:%s) )?(?P<ime>%s)" % ("|".join(_FED_IMENA), "|".join(_VSICHKI_FED))
# «Fed's Barr», «Fed Governor Lisa Cook», «Philadelphia Fed President Paulson»,
# «New York Fed's Williams», «Fed Vice Chair for Supervision Bowman», «Fed Chair Kevin Warsh»
_FED_PRED_IMETO = (r"(?:(?:New York|NY|Philadelphia|Philly|Cleveland|Richmond|Atlanta|Chicago|St\.? Louis|"
                   r"Minneapolis|Kansas City|Dallas|San Francisco|Boston) )?Fed(?:eral Reserve)?(?:'s)?"
                   r"(?: (?P<rolya>Chair(?:man|woman)?|Vice Chair(?: for Supervision)?|Governor|President|"
                   r"Board Member|Board Governor|official|chief|policymaker|"
                   # малките букви («Fed chair Jerome Powell») — само за разпознаването; «председател»
                   # се пише само при «Chair» с главна (виж kyde)
                   r"chair(?:man|woman)?|vice chair|governor|president))?(?:'s)?")
_FED_CHOVEK = re.compile(r"\b" + _FED_PRED_IMETO + r" " + _IME + r"\b")
_FED_IME_SAMO = re.compile(r"(?<![\w'])" + _IME + r"\b")
_KAZVA = _r(r"^(?:'s)?,?\s*(?:reportedly |also |again |still |now )?(?:says?|said|signals?|signaled|signalled|warns?|warned|sees|saw|"
            r"expects?|backs?|backed|flags?|flagged|urges?|urged|favou?rs?|calls?|argues?|argued|notes?|noted|"
            r"rejects?|rejected|allows?|allowed|pushes back|called|speaks?|spoke|remarks|comments|testif\w*|hints?|hinted|"
            r"repeats?|reiterates?|defends?|lays out|supports?|supported|opposes?|dissents?|dissented|stresses|emphasi[sz]es|"
            r"cautions?|cautioned|predicts?|open to|is open|sounds?|voices?|downplays?|dismisses?|"
            r"in (?:an )?interview|interview|speech|:)\b", _I)
# «pick» само като съществително за избран човек: «Trump's pick», НЕ «Growth Picks Up»
_NE_CHLEN = _r(r"\b(?:former|ex-|ex |retired|nominee|nominated|candidate|contender|hopeful|"
               r"would-be|frontrunner|front-runner|replace|successor|shortlist)\b|"
               r"\b(?:Trump's|his|a|the|new|surprise|top) pick\b|\bpicked (?:to|as|by)\b")

# теми на изказване/реч · от английския към кратко «за …» · най-много две
_TEMI_RECH = (
    (_r(r"\b(?:rate hikes?|hike|hikes|hiking|raise rates|raising rates|tightening|higher rates|rates higher|"
        r"rate increases?|rate rises?)\b"), "за вдигане на лихвата"),
    (_r(r"\b(?:rate cuts?|cut rates|cutting rates|cuts|lower rates|lowering rates|easing)\b"), "за намаляване на лихвата"),
    (_r(r"\binflation\w*"), "за инфлацията"),
    (_r(r"\b(?:labou?r market|jobs|employment|unemployment|workers)\b"), "за пазара на труда"),
    (_r(r"\bAI\b|(?i:\bartificial intelligence\b)", 0), "за изкуствения интелект"),
    (_r(r"\b(?:housing|shelter|mortgage)\b"), "за жилищата"),
    (_r(r"\b(?:yields?|treasury market|bond market)\b"), "за пазара на облигации"),
    (_r(r"\b(?:bank regulat\w*|stress test\w*|supervision|capital requirements?|discount window|banking)\b"), "за банките"),
    (_r(r"\b(?:stablecoins?|payments?|digital)\b"), "за плащанията"),
    (_r(r"\b(?:monetary policy|policy communication|policymaker)\b"), "за паричната политика"),
    (_r(r"\b(?:economic outlook|economic conditions|the economy|economy|economies|outlook)\b"), "за икономиката"),
)


def _temi(t, naj=2):
    out = []
    for rx, bg in _TEMI_RECH:
        if rx.search(t) and bg not in out:
            out.append(bg)
    # и двете посоки в едно заглавие → без посока: «Musalem Warns Excessive Cut in Fed
    # Communications Could Raise Rates and Inflation» не е реч «за вдигане на лихвата» (30.09)
    if "за вдигане на лихвата" in out and ("за намаляване на лихвата" in out or re.search(r"\bcut\b", t, _I)):
        out = [x for x in out if x not in ("за вдигане на лихвата", "за намаляване на лихвата")]
    return out[:naj]


def _s_temi(osnova, t):
    tm = _temi(t)
    if not tm:
        return osnova
    return osnova + " " + (tm[0] if len(tm) == 1 else tm[0] + " и " + tm[1][3:])


def _fed_emisiya(t, emisiya):
    """Самите емисии на Фед. Речите идват като «Barr, Economic Conditions and
       Monetary Policy» — името е преди запетаята и е от самия Фед."""
    if emisiya == "Fed речи":
        m = re.match(r"^([A-Z][a-z]+(?:[ -][A-Z][a-z]+)?),\s+(.+)$", t)
        if m:
            ime, tema = m.group(1), m.group(2)
            if re.search(r"\b(?:opening|welcoming|introductory|closing) remarks\b", tema, _I):
                return "Встъпително слово на член на Фед (%s)" % ime
            return _s_temi("Реч на член на Фед (%s)" % ime, tema)
        return "Реч на член на Фед"
    if re.search(r"\bFOMC statement\b", t, _I):
        return "Решението на Фед за лихвата (изявлението на FOMC)"
    if re.search(r"\beconomic projections\b", t, _I):
        return "Прогнозите на Фед за икономиката и лихвата (FOMC)"
    if re.search(r"^Minutes of the Federal Open Market Committee\b|\bFOMC minutes\b", t, _I):
        return "Протоколът от заседанието на Фед за лихвата (FOMC)"
    if re.search(r"\bdiscount rate\b", t, _I) and re.search(r"\bminutes\b", t, _I):
        return "Протокол на Фед за сконтовия процент (лихвата по заемите за банките)"
    if re.search(r"\bmonetary policy\b", t, _I):
        return "Съобщение на Фед за паричната политика"
    return "Съобщение на Фед — централната банка на САЩ"


# Човекът от Фед трябва да е ПОДЛОГЪТ на заглавието. Втората проверка (80 нови заглавия,
# 29.09) хвана «UBS Expects Two Fed Rate Hikes by End of 2026 After Warsh Speech and Jobs
# Data» → «Изказване на член на Фед (Warsh)…»: очакването е на UBS, не на Warsh. Затова пред
# човека може да стои само: нищо · етикет с двоеточие («US Market:») · «Exclusive-»/«Watch:» ·
# член/«US» · «In CT visit,». Или обърнатият ред на Reuters: «…, Fed Governor Barr says».
_PRED_PODLOG = _r(r"^(?:[\w&.' ]{2,30}\s+\|\s+|[\w&.']{2,20} - )?"         # «News | …», «Weeeknd - …»
                  r"(?:(?:EXCLUSIVE|Exclusive|BREAKING|Breaking|UPDATE|Update|WATCH|Watch|VIDEO|Video|LIVE|Live)\s*[-:|]\s*)?"
                  r"(?:(?:In|At|During) [^,]{1,40}, )?(?:the |a |an )?(?:US |U\.S\. )?"
                  r"(?:(?:more|two|three|several|some|top|other|key|many|most|few|senior) )?$")
_SLED_OBARNATO = _r(r"^\s*(?:says|said|warns|warned|tells \w+)\b\s*(?:\([^)]*\))?\s*(?:[-|].*)?$")


def _podlog(t, nachalo, kraj):
    """Човекът (t[nachalo:kraj]) ли е подлогът на заглавието."""
    pred = t[:nachalo]
    m = _ETIKET.match(pred)
    if m:
        pred = pred[m.end():]
    if _PRED_PODLOG.match(pred):
        return True
    # «The Fed shouldn't 'look through' some supply shocks, Chicago Fed's Goolsbee says»
    return bool(re.search(r",\s*$", pred) and _SLED_OBARNATO.match(t[kraj:]))


def _fed_chovek(t):
    """Изказване на човек от Фед в чуждо заглавие. None, ако не е сигурно."""
    if _NE_CHLEN.search(t):
        return None
    ime = rolya = None
    kraj = None
    m = _FED_CHOVEK.search(t)
    if m:
        ime, rolya, kraj = m.group("ime"), (m.group("rolya") or ""), m.end()
    else:
        m = _FED_IME_SAMO.search(t)
        if m and m.group("ime") in _FED_UNIKALNI and re.search(r"\bFed\b|\bFederal Reserve\b|\bFOMC\b", t):
            ime, rolya, kraj = m.group("ime"), "", m.end()
    if ime and not _podlog(t, m.start(), kraj):
        return None                       # човекът не е подлогът — новината е на някой друг
    if not ime:
        # «Fed official(s) …» без име
        m = re.search(r"\bFed(?:eral Reserve)? (?P<mn>officials?|policymakers?|speakers?|members?)\b", t, _I)
        if not m or not _KAZVA.search(t[m.end():m.end() + 40].lstrip()):
            return None
        if not _podlog(t, m.start(), m.end()):
            return None
        mn = m.group("mn").lower().endswith("s")
        return _s_temi("Изказвания на членове на Фед" if mn else "Изказване на член на Фед", t[m.end():])
    # глаголът «казва» трябва да е ТОЧНО след името (до две думи между тях)
    sled = t[kraj:kraj + 60]
    if not (_KAZVA.search(sled.lstrip()) or re.match(r"^\s*(?:\w+\s+){0,2}(?:says?|said|signals?|warns?|sees|expects?)\b", sled, _I)):
        # «Warsh: …» / «Kashkari: …» — двоеточие точно след името
        if not re.match(r"^\s*:", sled):
            return None
    kyde = "председателя на Фед" if re.fullmatch(r"Chair(?:man|woman)?", rolya or "") else "член на Фед"
    # темите — от заглавието без името и без изреченията-въпроси на изданието
    # («…Jackson Hole Speech. Does That Signal a Rate Hike Is Coming?» — въпросът не е негов)
    tekst = t[:m.start()] + " " + t[kraj:]
    tekst = " ".join(x for x in re.split(r"(?<=[.?!])\s+", tekst) if not x.rstrip().endswith("?"))
    return _s_temi("Изказване на %s (%s)" % (kyde, ime), tekst)


# ── решенията и очакванията за лихвата ─────────────────────────────────────
# Едно разпознаване (_lihva_vid), две употреби: цял ред (_fed_red) и фон (_fed_kontekst).
# Урокът от проверката на 220 случайни заглавия (29.09): «Will the Fed Raise Rates?
# No, Says One Expert» беше станало «Очаквания за по-висока лихва» — отрицанието и
# въпросът вече правят реда неутрален; «price hikes», «job cuts», «Cuts Guidance» не
# са лихва — вдигане/намаляване се брои само вързано за лихвата или за Фед.
# Второто четене (230 заглавия, 29.09) добави: «SC Sees Two More Fed Hikes» не е «Фед
# вдигна» (сегашното време иска лихвата след глагола); «easing dollar» не е по-мека
# политика; «…Dow falls 600 points. Expect more swings» не е очакване за лихвата —
# думата за очакване трябва да е ДО вдигането; «New York Fed's Empire State survey» и
# «Kansas City Fed meeting» не са решенията на Фед.
_FED = r"(?:the )?(?:US |U\.S\. )?(?:Fed|Federal Reserve|FOMC)"
_FED_VDIGNA = _r(r"\b" + _FED + r"(?:'s)?(?: Chair(?:man)?(?: [A-Z][a-z]+){1,2})?(?: just| officially| finally| unanimously)?"
                 r" (?:(?:raises|hikes|lifts|increases)(?= (?:interest |its |key |benchmark |policy |the )*(?:rates?|by|a quarter|\d))|"
                 r"raised|hiked|lifted|increased|votes to (?:raise|hike)|delivers? (?:a |its )?(?:first )?(?:rate )?hike|"
                 r"(?:starts?|started|begins?|began) (?:tightening|hiking|raising rates)|approves? (?:an? |its )?(?:interest )?rate (?:hike|increase))\b")
_FED_NAMALI = _r(r"\b" + _FED + r"(?:'s)?(?: just| officially| finally)? (?:cuts|cut|lowers|lowered|slashes|slashed|reduces|reduced|votes to cut)"
                 r"(?= (?:interest |its |key |benchmark |the )*(?:rates?|by))")
_FED_ZAPAZI = _r(r"\b" + _FED + r"(?:'s)?(?: just)? (?:holds|held|keeps|kept|leaves|left|maintains|maintained|pauses|paused)"
                 r"(?: (?:interest )?rates?| (?:its )?(?:key |benchmark )?(?:interest )?rate)(?: steady| unchanged| on hold)?\b")
# пред «Fed hikes» стои дума, която го прави съществително: «more Fed hikes», «on Fed hikes»
_NE_GLAGOL = _r(r"\b(?:more|further|another|additional|two|three|four|several|multiple|sees?|expects?|of|on|for|by|about|"
                r"over|amid|despite|to|with|bets?)\s+$")
_SLED_FED = _r(r"\b(?:after|following|post)[- ](?:the |a |its )?(?:hawkish |dovish |surprise |latest |first |big |jumbo |unanimous )?"
               # «Gold faces critical technical test after hawkish Fed rate hike» (третата проба, 29.09)
               r"(?:Fed|FOMC|Federal Reserve)(?:'s)?(?: (?:first |latest |recent )?(?:rate |interest rate |policy )?"
               r"(?:decision|meeting|hike|increase|move|announcement|statement|verdict))|\bpost-FOMC\b|\b(?:after|following) (?:the )?FOMC\b|"
               r"\b(?:after|following) (?:the )?Fed(?:'s)?(?=\s*(?:[,.;:!?]|$))|"
               # «Bitcoin Price Wobbles Before Settling After Fed Raises Rates» — решението е СТАНАЛО
               r"\b(?:after|following) (?:the )?(?:US |U\.S\. )?(?:Fed|FOMC|Federal Reserve) (?:raises|raised|hikes|hiked|lifts|lifted|"
               r"cuts|cut|lowers|lowered|holds|held|keeps|kept|leaves|left|decides|decided|announces|announced|delivers|delivered)\b|"
               r"\b(?:after|following) (?:the |a |its )?(?:first )?(?:rate )?(?:hike|decision|increase)\b")
_MESECI = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Monday's|Tuesday's|Wednesday's|Thursday's|Friday's|This Week's|Next Week's)"
_FED_RESHENIE = _r(r"\b(?:Fed|FOMC|Federal Reserve)(?:'s)?(?: (?:rate|interest rate|policy|monetary policy|" + _MESECI + r"))?"
                   r"(?: rates?| hike| interest rates?| interest-rates?)? (?:decision|meeting|announcement|verdict)s?\b|\bFOMC\b|\b(?:Fed|FOMC) (?:decides|to decide)\b|"
                   # «Stocks edge higher ahead of US Fed rate call» (30.09)
                   r"\b(?:Fed|FOMC)(?:'s)? (?:interest[- ])?rates? call\b|"
                   r"\b" + _MESECI + r" (?:Fed|FOMC) (?:rate |policy )?(?:decision|meeting)\b")
# вдигане/намаляване ВЪРЗАНО с лихвата («price hikes» и «job cuts» не са)
_VDIGANE = _r(r"\b(?:rate[- ]hikes?|rate[- ]hiking|interest[- ]rate (?:hikes?|increases?|rises?)|rate[- ]rises?|rate[- ]increases?|"
              r"hikes? (?:interest )?rates?|hiking (?:interest )?rates|raise[sd]? (?:interest |its |key |benchmark )*rates?|raising (?:interest )?rates|"
              r"(?:Fed|Fed's|FOMC)[- ]hikes?|(?:another|more|further|first|next|second|third|one|two|october|september|december|november) (?:rate )?hikes?|"
              r"hiking cycle)\b")
_NAMALYAVANE = _r(r"\b(?:rate[- ]cuts?|interest[- ]rate cuts?|cuts? (?:interest )?rates?|cutting (?:interest )?rates?|lower (?:interest )?rates|"
                  r"lowering (?:interest )?rates|reduce (?:interest )?rates|(?:Fed|Fed's|FOMC)[- ]cuts?|(?:another|more|further|first|next) (?:rate )?cuts?)\b")
# позиция на Фед, не действие: «hawkish», «tightening» → очаквания за по-висока лихва.
# «easing» само вързано за политиката: «easing dollar» е по-слаб долар, не по-мек Фед.
_STROGO = _r(r"\b(?:hawkish|hawks|tightening|tighter|higher[- ]for[- ]longer)\b")
_MEKO = _r(r"\bdovish\b|\b(?:monetary|policy|Fed) easing\b|\beasing (?:cycle|bias)\b|\blooser (?:policy|monetary)\b")
_OCHAKVANE = _r(r"\b(?:bets?|betting|odds|expectations?|expected|expects?|expect|pricing(?! out)|priced in|chances?|probability|"
                r"prospects?|likely|forecasts?|forecasting|predicts?|predicted|sees|set to (?:hike|raise|cut|lower)|poised|on track|"
                r"looms?|looming|anticipat\w*|braces? for|bracing for|prepares? for|preparing for|certain|survey|poll|consensus|"
                # страх/риск — само вързани за лихвата: «AI Safety Fears Collide with Fed Rate Hikes» и
                # «Yield Curve Becomes New Risk as Fed Hikes» НЕ са очаквания за вдигане (третата проверка, 29.09)
                r"calls? for|signals? more|points? to (?:another|more)|fears? (?:of|over|about|that|for)|worries (?:of|over|about|that)|"
                r"(?:fears?|feared|fearing|worries|worried about) (?:more|further|another|additional|a|an|potential|possible)|"
                r"concerns? (?:of|over|about|that)|risks? of|(?:hike|hiking|tightening|rate|policy) (?:fears?|worries|concerns?|risks?)|"
                r"looking to|looks to|plans? to|"
                r"(?:hike|hiking|tightening) pressures?|pressure to (?:raise|hike|tighten)|likelihood|speculations?|seen|"
                r"prices? in|imminent)\b")
_OCHAKV_DUMI = _r(r"\b(?:await\w*|outlook|path|signals?|view|uncertain\w*|guidance|stance|hawkish|dovish|concern\w*|jitters|"
                  r"nerves|worr\w*|watch\w*|focus|question|debate|what's next|where next|repric\w*|pricing out|priced out|"
                  r"unlikely|doubts?)\b|\?")
# при отрицание — по-тесният списък: «"Hawkish winds" sweep through the Federal Reserve! … no need
# for rate hikes» е за спора, не за очакванията
_OCHAKV_NE = _r(r"\b(?:repric\w*|pricing out|priced out|unlikely|doubts?|overestimat\w*|overpric\w*|too hot|trail\w*|"
                r"(?:defy|defies|defying|defied) (?:the )?expectations)\b|\?")
_OTRICANIE_PREDI = _r(r"\b(?:no|not|unlikely|won't|doubts?|without|never|skip|rules? out|ruled out|pricing out|priced out|"
                      r"holds? off|pause|(?:defy|defies|defying|defied) (?:the )?(?:expectations|forecasts|bets|odds|markets?)|"
                      r"overestimat\w*|overpric\w*|against)\b|n't\b")
_OTRICANIE_SLED = _r(r"^\S*\s*\?\s*No\b|^\s+(?:no|not|unlikely)\b|^\S*\s+(?:unlikely|off the table|ruled out|priced out)\b|"
                     # «Fed Rate Cut Delayed as Strong Jobs Data Tests Bitcoin» (30.09)
                     r"^\s+(?:(?:is|was|gets?|got) )?(?:delayed|postponed|pushed back|shelved)\b|"
                     r"^\s+(?:trail|lag)\w*\b|^(?:\s+\S+){0,4}\s+(?:too hot|overdone|overblown|overestimat\w*|overpric\w*|too far|too aggressive|excessive)\b")
# очакванията спадат: глагол ПРЕД тях («cools … hike bets») или СЛЕД тях («Hike Odds Fall») (30.09)
# («Bitcoin Breakout Cools as Fed Rate-Hike Bets Climb» — «cools» е за биткойна: съюзът «as» пречи)
_OCHAKV_SPAD = _r(r"\b(?:cool\w*|pare[sd]?|paring|trim\w*|dampen\w*|reduc\w*|curb\w*|scal\w* back|pull\w* back|unwind\w*|"
                  # «Gold rises as oil slide eases Fed hike fears» (30.09)
                  r"temper\w*|dash\w*|eases|eased|easing|calms?|calmed|soothe[sd]?|allay\w*|quell\w*)"
                  r"(?:\s+(?!(?:as|on|amid|after|while|despite|and|but)\b)[\w'-]+){0,3}\s*$")
_OCHAKV_SPAD_SLED = _r(r"^[\w\s'-]{0,16}?\b(?:fade[sd]?|fading|ease[sd]?|easing|dwindl\w*|fall|falls|fell|drop\w*|slip\w*|"
                       r"recede\w*|wane[sd]?|waning|diminish\w*|cool\w*|retreat\w*|decline[sd]?|shrink\w*|evaporat\w*|"
                       # «Fed rate hike odds tumble to coin flip», «…Rate-Hike Expectations Ease» (30.09)
                       r"tumbl\w*|plung\w*|sink\w*|sank|slid\w*|slump\w*|collaps\w*|dive[sd]?|diving|crater\w*|pared|trimmed)\b")
# прогнозата е обърната или е двусмислена: «Goldman flips on Fed rate hike, then backtracks on forecast»,
# «Goldman Sachs drops surprise call for next Fed interest-rate hike» (drops = пусна или отказа?)
_OBRAT_PROGNOZA = _r(r"\b(?:backtrack\w*|walks? back|walked back|u-turn\w*|scraps?|scrapped|abandon\w*|drops? (?:\w+ )?(?:call|forecast)|"
                     r"dropped (?:\w+ )?(?:call|forecast)|flips? on)\b")
# последицата на вдигането, не очакване за него: «Fed's rate hike likely means more expensive credit cards»,
# «Federal Reserve Rate Hikes Would Likely Put the Trump Bull Market on Thin Ice», «Fed rate hikes may not end the bull market»
_SLED_EFEKT = _r(r"^\s+(?:(?P<dum>\w+)\s+)?(?:would|could|might|may|will|likely|to)\s+(?:\w+\s+)?(?:not\s+)?(?:means?|hit|hurt|affect|impact|push|put|"
                 r"squeeze|cost|weigh|slam|pressure|crush|help|boost|spell|make|send|drive|end|derail|kill|sink|lift|change)\b")
# «hawkish» за самия Фед или за очакванията, не «Warsh's Hawkish Background»
_STROGO_SLED = _r(r"^(?:[\s-]+[\w'-]+){0,2}?[\s-]+(?:Fed|FOMC|Federal Reserve|policy|bets?|expectations?|outlook|stance|signals?|shift|"
                  r"tilt|pivot|tone|remarks?|comments?|repricing|pricing|path|cycle|mood|message|minutes|hold|pause|surprise|bias|"
                  r"officials?|rates?)\b")
_STROGO_PREDI = _r(r"\b(?:Fed|FOMC|Federal Reserve|Fed's|Federal Reserve's|policymakers?|officials?|policy)\b[\w\s']*$")
_FED_LIHVA = _r(r"\b(?:Fed|Federal Reserve|FOMC)(?:'s)?\b.*\b(?:rates?|hikes?|cuts?|policy|decision|meeting|tightening|easing|"
                r"hawkish|dovish|outlook|signals?|path|minutes)\b|\b(?:rates?|hikes?|cuts?|policy)\b.*\b(?:Fed|Federal Reserve|FOMC)\b")
_KAKVO_ZNACHI = _r(r"\bwhat\b.*\b(?:means?|mean)\b|\bhere's what\b|\bwhat it means\b|\bwhat to know\b|\beverything to know\b|"
                   r"\bhow (?:will|would|could|does|do|did|the|a|fed|fed's|to)\b.*\b(?:affect|impact|hit|mean|change|help|hurt|weigh|react|prepare)\w*")
# вдигането като станало: «the Fed's rate hike», «latest hike», «first rate hike in 3 years»
_STANALO = _r(r"\b(?:(?:the )?(?:Fed's|Federal Reserve's) (?:first |latest |recent |surprise )?(?:interest[- ])?rate (?:hike|increase)|"
              r"latest|recent|surprise|last week's|this week's|first (?:rate )?hike in|"
              r"first interest rate (?:hike|increase) in)\b")
_STANALO_POS = _r(r"\b(?:the )?(?:Fed's|Federal Reserve's|FOMC's) (?:first |latest |recent |surprise |last )?(?:interest[- ])?rate (?:hike|increase)\b")
_SLEDVASHTO = _r(r"\b(?:expected|likely|possible|potential|probable|next|another|more|further|upcoming|coming|planned|looming|"
                 r"would|could|will|may|might|if|odds|bets?|chances?)\b|\?")
# регионалните банки на Фед и техните проучвания/срещи не са решенията на Фед
_REGIONALEN_FED = _r(r"\b(?:New York|NY|Philadelphia|Philly|Cleveland|Richmond|Atlanta|Chicago|St\.? Louis|Minneapolis|Kansas City|"
                     r"Dallas|San Francisco|Boston) Fed(?:'s)?(?: (?:Empire State|manufacturing|services|business|consumer|nonmanufacturing))?"
                     r" (?:survey|index|GDPNow|meeting|symposium|conference|report|study|research|data|poll|outlook|"
                     r"manufacturing|nonmanufacturing|services|business)\b|"
                     # «Corporate finance chiefs lift inflation outlook, cite rates as concern - Fed survey» —
                     # анкетата на Фед не е лихвата на Фед (30.09)
                     r"[-|–—:]\s*Fed (?:survey|poll)\s*$")


def _blizo(rx, t, m, pred=45, sled=30):
    """Има ли `rx` около съвпадението `m` (думата за очакване да е ДО вдигането) —
       и в СЪЩОТО изречение: «…Supported The Latest Rate Hike. She Says Chances Of
       Elevated Inflation…» — шансовете са за инфлацията, не за лихвата."""
    predi = t[max(0, m.start() - pred):m.start()]
    k = max(predi.rfind(". "), predi.rfind("? "), predi.rfind("! "))
    if k >= 0:
        predi = predi[k + 2:]
    sled_t = t[m.start():m.end() + sled]
    k = min([x for x in (sled_t.find(". ", m.end() - m.start()), sled_t.find("! ", m.end() - m.start())) if x >= 0] or [len(sled_t)])
    return bool(rx.search(predi + sled_t[:k]))


def _lihva_vid(t):
    """Какво казва заглавието за лихвата на Фед · един от ключовете долу, или None."""
    t = _REGIONALEN_FED.sub(" ", t)
    ima_fed = bool(re.search(r"\bFed\b|\bFederal Reserve\b|\bFOMC\b", t, _I))
    if not ima_fed:
        return None
    # изказванията — само когато те са новината: «Hawkish Fed Comments», «comments from Fed
    # officials», «Fed officials say…»; НЕ «Hassett Voices Concern Against Fed Officials' Call»
    # «…Dovish Fed Speech» — речта е новината, не «очаквания за по-ниска лихва» (30.09)
    if re.search(r"\bFed (?:speakers?|speech(?:es)?|comments|remarks|appearances)\b|\b(?:comments|remarks|speeches) (?:from|by) Fed\b|"
                 r"\bFed officials? (?:says?|said|signals?|warns?|sees?|expects?|backs?|flags?|urges?|repeats?)\b", t, _I):
        return "rechi"
    for vid, rx in (("vdigna", _FED_VDIGNA), ("namali", _FED_NAMALI), ("zapazi", _FED_ZAPAZI)):
        m = rx.search(t)
        if m and not _USLOVNO.search(t[:m.start()][-25:]) and not _NE_GLAGOL.search(t[:m.start()]) \
                and not re.search(r"\?", t):
            return vid
    # «Fed to hold rates steady in rest of 2026; rising number of analysts see at least one
    # hike: Reuters poll» — главното е задържане; посока «по-висока» би било грешно
    if re.search(r"\b(?:Fed|FOMC|Federal Reserve)\b[^.;:]{0,25}?\b(?:to|will|seen|expected to|likely to|set to) "
                 r"(?:(?:hold|keep|leave) (?:interest |its |key |benchmark )*rates?|pause)\b", t, _I):
        return "ochakv"
    mv, mn_ = _VDIGANE.search(t), _NAMALYAVANE.search(t)
    vd, nm = bool(mv), bool(mn_)
    # «What makes the Federal Reserve decide to raise or lower interest rates?» — и двете посоки
    if re.search(r"\b(?:raise|hike|lift|increase)s? or (?:lower|cut|reduce)\b|\b(?:lower|cut|reduce)s? or (?:raise|hike|lift)\b|"
                 r"\bhikes? or cuts?\b|\bcuts? or hikes?\b", t, _I):
        vd = nm = True
    # «Experts Predict No Fed Rate Cut Next Week: What It Means» — «какво значи» без отрицание до
    # вдигането/намаляването; с отрицание редът пада към неутралното по-долу (30.09)
    if (vd or nm) and _KAKVO_ZNACHI.search(t) and not (vd and nm) \
            and not _blizo(_OTRICANIE_PREDI, t, mv or mn_, 40, 0):
        return "znachi_gore" if vd else "znachi_dolu"
    if re.search(r"\bminutes\b", t, _I):
        return "protokol"
    if re.search(r"\bBeige Book\b", t):
        return "bezhova"
    if _SLED_FED.search(t):
        return "sled"
    # «Federal Reserve hawkish hike sent Gold price lower» — вдигането (с остър тон) е станало
    if re.search(r"\bhawkish (?:Fed |FOMC |Federal Reserve |Fed's )?(?:rate |interest[- ]rate )?(?:hike|increase)\b", t, _I):
        return "vdigane_stanalo"
    strogi = [x for x in _STROGO.finditer(t)
              if _STROGO_SLED.match(t[x.end():]) or _STROGO_PREDI.search(t[max(0, x.start() - 35):x.start()])]
    strogo = bool(strogi)
    # «tightening» само по себе си е действието, не очакване: «Where will Fed tightening hit hardest
    # in Asia?» е за вдигането. Очакване е острият тон («hawkish») или дума за очакване до него (30.09)
    strogo_ochakv = any(re.match(r"hawk|higher", x.group(0), _I) or _blizo(_OCHAKVANE, t, x)
                        or _blizo(_r(r"\b(?:view|outlook|stance|signals?|pricing)\b"), t, x, 10, 25) for x in strogi)
    meko = bool(_MEKO.search(t))
    # прогнозата е обърната / двусмислена → неутрално
    if (mv or mn_ or strogo) and _OBRAT_PROGNOZA.search(t):
        return "ochakv"
    # Отрицанието — ПРЕДИ вдигането в същото изречение, или «? No» точно след него → неутрално
    # («There Will Be No Fed Rate Hikes», «Will the Fed Raise Rates? No, Says One Expert»).
    # Въпросът сам не отрича — само маха посоката: «How Stocks Performed After Initial Fed Rate
    # Hikes?» остава темата. «A Fed Rate Hike Wouldn't Hit Every Portfolio» — «n't» е за «hit».
    m_ = mv or mn_ or (_STROGO.search(t) if strogo else None) or _MEKO.search(t)
    if m_ and (_blizo(_OTRICANIE_PREDI, t, m_, 40, 0) or _OTRICANIE_SLED.match(t[m_.end():])):
        # «очакванията» само ако заглавието пита или очаква; «The Fed Hasn't Cut Rates Once
        # This Year. Car Loans Got Cheaper Anyway.» не е за очакванията (втората проверка, 29.09)
        return "ochakv" if (_OCHAKVANE.search(t) or _OCHAKV_NE.search(t)) else "ne"
    # «the Federal Reserve's rate hike» — конкретното вдигане. «The implementation of the Federal
    # Reserve's rate hike has improved liquidity expectations» НЕ е очакване за по-висока лихва
    if vd and not nm and _STANALO_POS.search(t) and not _SLEDVASHTO.search(t):
        return "vdigane_stanalo"
    # последицата на вдигането («…likely means more expensive credit cards») — темата, не очакване;
    # освен ако очакването стои точно пред него («How the expected Fed rate hike could squeeze…»)
    me = _SLED_EFEKT.match(t[mv.end():]) if (vd and not nm) else None
    # («Fed Rate-Hike Prospects Could Weigh» — «prospects» е очакването, то остава)
    if me and not _OCHAKVANE.search(t[max(0, mv.start() - 15):mv.start()] + " " + (me.group("dum") or "")):
        return "vdigane_stanalo" if _STANALO_POS.search(t) else "vdigane"
    # «Treasury Curve Narrows: Fed Hike Risks Growth» — «risks» е глаголът (вдигането застрашава
    # растежа), не «рисковете от вдигане» (30.09)
    # («Fed rate hike risks linger», «…Hike Risks Cloud the Rally» — там «risks» е съществително)
    if vd and not nm and re.match(r"^\s+(?:risks (?:growth|recession|a|an|the|economy|jobs|stocks|markets?|slowdown|housing|"
                                  r"damage|hurting|derailing|choking|tipping)|threatens|hurts|squeezes|slams|crushes)\b",
                                  t[mv.end():], _I) \
            and not _OCHAKVANE.search(t[max(0, mv.start() - 15):mv.start()]):
        return "vdigane_stanalo" if _STANALO_POS.search(t) else "vdigane"
    vypros =bool(m_ and re.search(r"\?", t[m_.start():m_.end() + 15]))
    # «soft data cools October Fed hike bets», «October Rate Hike Odds Fall» — очакванията СПАДАТ;
    # «на фона на очакванията за по-висока лихва» би казало обратното → неутрално (30.09)
    m_sp = mv if (vd and not nm) else (mn_ if (nm and not vd) else None)
    if m_sp and not vypros and _blizo(_OCHAKVANE, t, m_sp) and (
            _OCHAKV_SPAD.search(t[max(0, m_sp.start() - 30):m_sp.start()]) or _OCHAKV_SPAD_SLED.match(t[m_sp.end():])):
        return "ochakv"
    if not vypros:
        if (vd and not nm and _blizo(_OCHAKVANE, t, mv)) or (strogo_ochakv and not nm and not meko):
            return "ochakv_gore"
        if (nm and not vd and _blizo(_OCHAKVANE, t, mn_)) or (meko and not vd and not strogo):
            return "ochakv_dolu"
    if _FED_RESHENIE.search(t):
        return "reshenie"
    if vd and not nm:
        return "vdigane_stanalo" if _STANALO.search(t) else "vdigane"
    if nm and not vd:
        return "namalyavane_stanalo" if _STANALO.search(t) else "namalyavane"
    # «Federal Reserve Inflation Outlook Signals a Critical Warning for Investors» — прогнозата е за
    # инфлацията, в заглавието няма дума за лихвата (30.09)
    if not re.search(r"\b(?:rates?|hikes?|cuts?|hiking|policy|decision|meeting|tightening|easing|hawkish|dovish|minutes)\b", t, _I) \
            and re.search(r"\b(?:inflation|growth|economic|economy|jobs|labou?r(?: market)?) (?:outlook|forecasts?|projections?)\b", t, _I):
        return "fed"
    if _FED_LIHVA.search(t):
        # фонът «очакванията…» само с дума за очакване/посока; иначе голото «лихвата на Фед»
        # («Interest Rates and Gold: Why the Fed Didn't Move the Price»)
        # «U.S. Treasury Yields Fall as Fed Regains Trust, BOE Leaves Rates Unchanged» — лихвата
        # е на Английската банка: друга централна банка между Фед и лихвата → не е лихвата на Фед
        mf = re.search(r"\b(?:Fed|Federal Reserve|FOMC)\b", t, _I)
        mr = re.search(r"\b(?:rates?|hikes?|cuts?)\b", t[mf.end():], _I) if mf else None
        if mf and mr and _DRUG_CB_IMA.search(t[mf.end():mf.end() + mr.start()]):
            return "fed"
        return "obshto" if (_OCHAKVANE.search(t) or _OCHAKV_DUMI.search(t)) else "obshto_goli"
    # «Oil-Driven Fed Bets Sink Gold Nearly 4%» — залозите за Фед са очакванията за лихвата (30.09)
    if re.search(r"\b(?:Fed|FOMC)(?:'s)?[- ](?:rate[- ])?(?:bets|pricing|expectations)\b", t, _I):
        return "obshto"
    return "fed"


_RED_OT_VID = {
    "vdigna": "Фед вдигна лихвата", "namali": "Фед намали лихвата", "zapazi": "Фед запази лихвата",
    "znachi_gore": "Какво значи вдигане на лихвата от Фед", "znachi_dolu": "Какво значи намаляване на лихвата от Фед",
    "protokol": "Протоколът от заседанието на Фед за лихвата (FOMC)",
    "bezhova": "Бежовата книга на Фед — преглед на икономиката на САЩ",
    "ochakv": "Очакванията за лихвата на Фед",
    "ochakv_gore": "Очаквания за по-висока лихва от Фед", "ochakv_dolu": "Очаквания за по-ниска лихва от Фед",
    "reshenie": "Решението на Фед за лихвата", "sled": "След решението на Фед за лихвата",
    # «За …» — темата, не събитие: «A Fed Rate Hike Is A Massive Mistake» не казва, че е станало
    "vdigane": "За вдигане на лихвата от Фед", "vdigane_stanalo": "За вдигането на лихвата от Фед",
    "namalyavane": "За намаляване на лихвата от Фед", "namalyavane_stanalo": "За намаляването на лихвата от Фед",
    "obshto": "За лихвата на Фед", "obshto_goli": "За лихвата на Фед", "ne": "За лихвата на Фед",
    "rechi": "Изказвания на членове на Фед",
}
_FON_OT_VID = {
    "vdigna": "вдигането на лихвата от Фед", "namali": "намаляването на лихвата от Фед",
    "zapazi": "решението на Фед за лихвата", "reshenie": "решението на Фед за лихвата", "sled": "решението на Фед за лихвата",
    "znachi_gore": "решенията на Фед за лихвата", "znachi_dolu": "решенията на Фед за лихвата",
    "protokol": "протокола от заседанието на Фед", "bezhova": "Бежовата книга на Фед",
    "ochakv": "очакванията за лихвата на Фед",
    "ochakv_gore": "очакванията за по-висока лихва от Фед", "ochakv_dolu": "очакванията за по-ниска лихва от Фед",
    "vdigane": "решенията на Фед за лихвата", "vdigane_stanalo": "вдигането на лихвата от Фед",
    "namalyavane": "решенията на Фед за лихвата", "namalyavane_stanalo": "намаляването на лихвата от Фед",
    "obshto": "очакванията за лихвата на Фед", "obshto_goli": "лихвата на Фед", "ne": "решенията на Фед за лихвата",
    "rechi": "изказванията на членове на Фед",
    "fed": "Фед",
}
# «преди …» може само предстоящото: решението, изказванията, решенията изобщо. Станалото
# («sled», «vdigna»…), очакванията и отрицанието — никога.
_FON_MOJE_PREDI = frozenset(("reshenie", "rechi", "vdigane", "namalyavane", "znachi_gore", "znachi_dolu"))


def _fed_kontekst(t, s_vid=False):
    """Лихвата на Фед като ФОН на друга новина · фраза или None (с s_vid → (фраза, вид))."""
    vid = _lihva_vid(t)
    return (_FON_OT_VID.get(vid), vid) if s_vid else _FON_OT_VID.get(vid)


def _fed_red(t, nachalo=True):
    """Цял ред, когато Фед Е новината. `nachalo=False` → Фед е споменат по-назад:
       тогава «Фед вдигна лихвата» НЕ се пише (новината е за друго — «Bill
       financing costs rise with Fed hikes» е за цената на заемите)."""
    if _NE_CHLEN.search(t) and re.search(r"\bchair\b", t, _I):
        return None                       # кой ще е председател — не е решение за лихвата
    vid = _lihva_vid(t)
    if not nachalo and vid in ("vdigna", "namali", "zapazi"):
        vid = {"vdigna": "vdigane_stanalo", "namali": "namalyavane_stanalo", "zapazi": "reshenie"}[vid]
    if not nachalo and vid == "reshenie":
        m = _FED_RESHENIE.search(t)
        if m and _predstoi(t, m.start(), m.end()):
            return "Преди решението на Фед за лихвата"   # новината е друга, случва се преди решението
    # седмичният календар: «Fed Meeting, Dreamforce, Retail Sales: Key Events for the Week of Sept. 15»
    if vid == "reshenie" and re.search(r"\b(?:week ahead|key events|events for the week|what to watch|what to expect|calendar|"
                                       r"the week of|this week|next week|preview)\b", t, _I):
        return "Преди решението на Фед за лихвата"
    return _RED_OT_VID.get(vid)


# ══════════════════════════════════════════════════════════════════════════
#  4 · ДАННИТЕ
# ══════════════════════════════════════════════════════════════════════════
# (израз, «данни за …», код в скоби, само_САЩ, пълен ред вместо «Данни за …»)
_DANNI = (
    (_r(r"(?-i:\bJOLTS\b)|\bjob openings\b"), "свободните работни места", "JOLTS", True, None),
    (_r(r"(?-i:\bADP\b)"), "работните места в частния сектор", "ADP", True, None),
    (_r(r"\bnon-?farm payrolls?\b|(?-i:\bNFP\b)|\bpayrolls\b"), "работните места", "NFP", True, None),
    (_r(r"\b(?:initial |weekly |continuing )?jobless claims\b|\bunemployment claims\b|\binitial claims\b"),
     "молбите за помощ при безработица", None, True, "Молби за помощ при безработица"),
    (_r(r"\bjobs? (?:report|data|numbers?|figures?|day)\b|\bemployment (?:report|data)\b|\blabou?r (?:market )?(?:report|data)\b"),
     "заетостта", None, False, None),
    (_r(r"\bunemployment rate\b"), "безработицата", None, False, None),
    (_r(r"\b(?:core )?(?-i:PCE)\b|\bpersonal consumption expenditures?\b"), "инфлацията", "PCE", True, None),
    (_r(r"\b(?:core )?(?-i:CPI)\b|\bconsumer price(?:s| index)\b|\bconsumer inflation\b"), "инфлацията", "CPI", False, None),
    (_r(r"(?-i:\bPPI\b)|\bproducer prices?(?: index)?\b|\bwholesale (?:prices|inflation)\b"), "цените на производител", "PPI", False, None),
    (_r(r"\binflation (?:data|report|reading|figures?|numbers?|print|release)\b|\breport on inflation\b|"
        r"\binflation (?:rises?|rose|falls?|fell|eases?|eased|cools?|cooled|slows?|slowed|accelerates?|accelerated|"
        r"jumps?|jumped|picks? up|picked up|ticks? (?:up|down)|ticked (?:up|down)|hits?|stays?|stayed|remains?|remained|holds?|held|climbs?|climbed|surges?|surged|quickens?|quickened|heats? up|heated up|continues to)\b"),
     "инфлацията", None, False, None),
    (_r(r"(?-i:\bGDP\b)|\bgross domestic product\b"), "растежа на икономиката", "БВП", False, None),
    (_r(r"\bretail sales\b"), "продажбите на дребно", None, False, None),
    (_r(r"(?-i:\bISM\b)"), "бизнес активността", "ISM", True, None),
    # PMI само с думите на индекса: «VC PMI» е индикатор за графика, а «PMI» в
    # статия за ипотеки е застраховката (private mortgage insurance)
    (_r(r"(?<!VC )(?-i:\bPMIs?\b)(?=.*\b(?:manufacturing|services|composite|factory|factories|business activity|purchasing managers|"
        r"Caixin|flash|data|survey|contraction|expansion|activity)\b)|\b(?:manufacturing|services|composite|factory|Caixin|flash)\b.{0,30}(?-i:\bPMIs?\b)"),
     "бизнес активността", "PMI", False, None),
    (_r(r"\bconsumer (?:confidence|sentiment)\b|\bMichigan (?:sentiment|survey|index)\b"), "доверието на потребителите", None, False, None),
    (_r(r"\bdurable goods\b"), "поръчките на дълготрайни стоки", None, False, None),
    # регионалните проучвания на Фед · държавата е в самото име (None = без « в САЩ»)
    (_r(r"\bEmpire State (?:survey|index|manufacturing)\b|\bNew York Fed(?:'s)? (?:manufacturing )?(?:survey|index)\b"),
     "производството в щата Ню Йорк (Empire State)", None, None, None),
    (_r(r"\b(?:Philly|Philadelphia) Fed(?:'s)? (?:manufacturing |business )?(?:survey|index)\b"),
     "производството около Филаделфия (Philly Fed)", None, None, None),
    (_r(r"\bhousing starts\b|\b(?:existing|new|pending)[- ]home sales\b|\bbuilding permits\b"), "жилищния пазар", None, False, None),
)


_FON_CYAL = {"Молби за помощ при безработица": "молбите за помощ при безработица"}


def _danni(t):
    """Първите (по място в заглавието) данни · (пълен ред, фраза за фон, позиция) или None."""
    # общото «inflation …» — само ако няма назован показател: «Inflation stayed hot, as CPI
    # rose…» е CPI
    nai = None
    for rx, ime, kod, samo_sasht, cyal in _DANNI:
        m = rx.search(t)
        if m and (nai is None or m.start() < nai[0]) and not (kod is None and ime == "инфлацията" and nai):
            nai = (m.start(), ime, kod, samo_sasht, cyal)
    if nai and nai[2] is None and nai[1] == "инфлацията":
        for rx, ime, kod, samo_sasht, cyal in _DANNI:
            if kod in ("CPI", "PCE", "PPI") and rx.search(t):
                nai = (rx.search(t).start(), ime, kod, samo_sasht, cyal)
                break
    if not nai:
        return None
    poz, ime, kod, samo_sasht, cyal = nai
    d = "" if samo_sasht is None else _drzhava(t, samo_sasht)
    # кодовете JOLTS/ADP/NFP/PCE/ISM са само американски: «UK payrolls drop» НЕ е NFP
    if samo_sasht and kod and d not in ("", " в САЩ"):
        kod = None
    if kod == "NFP" and d != " в САЩ":
        mm = _DANNI[2][0].search(t)
        if mm and not re.search(r"(?i:non-?farm)|NFP", mm.group(0)) and not re.search(r"\b(?:US|U\.S\.)\s*$", t[:mm.start()]):
            kod = None                     # голото «payrolls» без САЩ до него — без кода
    kod_s = " (%s)" % kod if kod else ""
    if cyal:
        return cyal + d + kod_s, _FON_CYAL.get(cyal, cyal[0].lower() + cyal[1:]) + d + kod_s, poz
    return "Данни за " + ime + d + kod_s, "данните за " + ime + d + kod_s, poz


# ══════════════════════════════════════════════════════════════════════════
#  5 · ПРЕДМЕТЪТ НА ЗАГЛАВИЕТО И ПОСОКАТА МУ
# ══════════════════════════════════════════════════════════════════════════
# вид: «цена» (поевтинява/поскъпва) · «доход» (спада/расте) · «акции» (падат/се качват)
# mn: множествено число
_PREDMETI = (
    (r"(?:spot )?gold(?: prices?)?(?: \(XAU/USD\))?\s*(?:,|and|&)\s*silver(?: prices?)?", "Златото и среброто", "цена", True),
    (r"(?:spot )?silver(?: prices?)?\s*(?:and|&)\s*gold(?: prices?)?", "Среброто и златото", "цена", True),
    (r"(?:spot |comex |the )?(?:gold|XAU/?USD|bullion)(?: futures| price| prices| spot price)?(?: \(XAU/USD\))?", "Златото", "цена", False),
    (r"(?:spot |comex )?(?:silver|XAG/?USD)(?: futures| price| prices)?", "Среброто", "цена", False),
    (r"platinum(?: price| prices)?", "Платината", "цена", False),
    (r"palladium(?: price| prices)?", "Паладият", "цена", False),
    (r"copper(?: futures| price| prices)?", "Медта", "цена", False),
    (r"(?:oil|crude|crude oil|brent|brent crude|WTI|US crude)(?: futures| price| prices)?", "Петролът", "цена", False),
    (r"(?:the )?(?:canadian dollar|loonie)", "Канадският долар", "цена", False),
    (r"(?:the )?(?:australian dollar|aussie dollar)", "Австралийският долар", "цена", False),
    (r"(?:the )?(?:new zealand dollar|kiwi dollar)", "Новозеландският долар", "цена", False),
    (r"(?:the )?(?:US |U\.S\. |American )?(?:dollar|greenback)(?: index)?|(?:the )?(?:DXY|USD index|united states dollar index)", "Доларът", "цена", False),
    (r"(?:the )?euro", "Еврото", "цена", False),
    (r"(?:the )?(?:japanese )?yen", "Йената", "цена", False),
    (r"(?:the )?(?:british pound|pound sterling|pound|sterling)", "Британската лира", "цена", False),
    (r"(?:the )?swiss franc", "Швейцарският франк", "цена", False),
    # «Treasuries rally» е цената на облигациите — доходността тогава ПАДА; затова само «yields»
    (r"(?:the )?(?:US |U\.S\. )?(?:\d+-year |long-term |short-term )?(?:treasury|T-note|T-bond) yields?|"
     r"(?:the )?(?:US |U\.S\. )(?:bond )?yields", "Доходността на американските облигации", "доход", False),
    (r"(?:global |government )?bond yields", "Доходността на облигациите", "доход", False),
    (r"(?:US |U\.S\. |american )stocks|wall st(?:reet|\.)?(?: stocks)?|(?:the )?s&p 500(?: futures)?|(?:the )?dow(?: jones)?(?: futures)?|"
     r"(?:the )?nasdaq(?: composite)?(?: futures)?|US equit(?:y|ies)(?: indexes| indices| futures)?|US stock (?:futures|indexes|indices)", "Американските акции", "акции", True),
    (r"european stocks|european shares|european equities", "Европейските акции", "акции", True),
    (r"asian stocks|asia stocks|asian shares|asian markets", "Азиатските акции", "акции", True),
    (r"stocks|shares|equities", "Акциите", "акции", True),
    (r"(?:the )?stock market", "Фондовият пазар", "акции", False),
    (r"(?:bitcoin|BTC)(?: price| prices)?", "Биткойн", "цена", False),
    (r"(?:the )?crypto(?:currencies|currency)?(?: market| markets| prices)?", "Криптовалутите", "цена", True),
    (r"mortgage rates", "Ипотечните лихви", "доход", True),
)
# «(?!-)»: сложното прилагателно не е предметът · «Oil-Driven Fed Bets Sink Gold Nearly 4%» е за
# златото, не за петрола (пробата от живия файл, 30.09)
_PREDMETI_RE = tuple((re.compile(r"^(?:" + p + r")\b(?!-)", _I), bg, vid, mn) for p, bg, vid, mn in _PREDMETI)

_NAR = r"(?:(?:sharply|further|again|slightly|modestly|marginally|steadily|early|today|on \w+day)\s+)?"
_POSOKI = (
    # (вид_посока, израз · прилепен точно след предмета)
    ("leko_dolu", _r(r"^(?:edges?|inches?|ticks?|drifts?|creeps?|trades?|moves?) (?:lower|down)\b|^(?:is |are )?slightly (?:lower|down)\b")),
    ("leko_gore", _r(r"^(?:edges?|inches?|ticks?|drifts?|creeps?) (?:higher|up)\b|^(?:is |are )?slightly (?:higher|up)\b")),
    ("dolu", _r(r"^" + _NAR + r"(?:lower\b|buckles?|buckled|falls?|fell|drops?|dropped|slips?|slipped|slides?|slid|declines?|declined|sinks?|sank|"
                r"tumbles?|tumbled|plunges?|plunged|plummets?|plummeted|retreats?|retreated|eases?|eased|dips?|dipped|"
                r"loses|lost|slumps?|slumped|crash(?:es|ed)?|weakens?|weakened|sags?|sagged|skids?|skidded|"
                r"extends? (?:losses|decline|declines|slide|drop|fall)|pares? gains|sheds?|breaks? (?:below|under|down)|"
                r"(?:heads?|trades?|opens?|closes?|ends?|turns?|trends?|moves?|is|are|goes|go|finishes|settles?) lower|"
                r"(?:is |are )?down\b|(?:is |are )?(?:falling|dropping|sliding|slipping|declining|"
                r"sinking|tumbling|weakening|retreating)|corrects?|pulls? back|gives? up gains|"
                r"(?:has|have) (?:fallen|dropped|declined|tumbled|slipped|plunged))\b")),
    ("otskok", _r(r"^" + _NAR + r"(?:rebounds?|rebounded|bounces?(?: back)?|bounced|recovers?|recovered|regains?|regained|"
                  r"pares? losses|claws? back|(?:is |are )?(?:bouncing|rebounding|recovering)|extends? (?:recovery|rebound|bounce)|"
                  r"returns? above|(?:moves?|climbs?|gets?) back above|reclaims?)\b")),
    ("gore", _r(r"^" + _NAR + r"(?:higher\b|leads? (?:\w+ )?higher|rises?|rose|gains?|gained|climbs?|climbed|jumps?|jumped|rall(?:y|ies|ied)|surges?|surged|"
                r"soars?|soared|advances?|advanced|firms?|firmed|strengthens?|strengthened|spikes?|spiked|"
                r"shoots? (?:up|higher|to)|extends? (?:gains|rally|rise|advance|climb|rebound)|breaks? (?:above|higher|out)|"
                r"(?:heads?|trades?|opens?|closes?|ends?|turns?|trends?|moves?|is|are|goes|go|finishes|settles?|push(?:es)?|grinds) higher|"
                r"(?:is |are )?up\b|(?:is |are )?(?:rising|climbing|gaining|surging|rallying|jumping|strengthening|firming|advancing)|"
                r"(?:has|have) (?:risen|climbed|jumped|surged|rallied|gained))\b")),
    ("natisk", _r(r"^(?:(?:is |are |comes? |stays? |remains? )?under (?:heavy |renewed |selling )?pressure|faces? (?:renewed |more |fresh |heavy )?(?:selling )?pressure|(?:is |are )?pressured)\b")),
    ("stoi", _r(r"^(?:holds? steady|steadies|steadied|(?:is |are )?steady|stays? steady|(?:is |are |trades? |stays? )?flat|"
                r"(?:is |are )?muted|(?:is |are )?little changed|(?:is |are )?unchanged|consolidates?|(?:is |are )?consolidating|"
                r"treads? water|(?:is |are )?range-?bound|(?:is |are )?stable|stabili[sz]es?|stabili[sz]ed|holds? firm|holds? ground)\b")),
)
_PERIOD = r"(?P<n>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|several|multi|multiple)[- ](?P<u>week|month|year|day|session)s?"
_NIVA = (
    ("blizo_dyno", _r(r"^(?:(?:is |are )?(?:near|hovers? near|(?:is |are )?hovering near|stays? near|holds? near|sits? near|trades? near|"
                      r"lingers? near|(?:is |are )?close to|nears?|approaches|clings? to|holds? just above)|(?:holds?|stays?|hovers?|sits?|trades?) (?:at|around))"
                      r" (?:nearly |almost |roughly |near )?(?:a |an |the |its |fresh |new )?(?:nearly |almost )?" + _PERIOD + r"[- ](?:low|lows|bottom|trough)\b")),
    ("na_dyno", _r(r"^(?:hits?|touches?|touched|(?:falls?|fell|drops?|dropped|slides?|slid|sinks?|sank|declines?|declined|plunges?|plunged|"
                   r"slumps?|slumped|tumbles?|tumbled|retreats?) to|at|reaches?|reached|opens? at|marks?|sets?|posts?)"
                   r" (?:nearly |almost |roughly |near )?(?:a |an |the |its |fresh |new )?(?:nearly |almost )?" + _PERIOD + r"[- ](?:low|lows|bottom|trough)\b")),
    ("blizo_vryh", _r(r"^(?:(?:is |are )?(?:near|hovers? near|(?:is |are )?hovering near|stays? near|holds? near|sits? near|trades? near|"
                      r"(?:is |are )?close to|nears?|approaches|firms? near)|(?:holds?|stays?|hovers?|sits?|trades?) (?:at|around))"
                      r" (?:nearly |almost |roughly |near )?(?:a |an |the |its |fresh |new )?(?:nearly |almost )?" + _PERIOD + r"[- ](?:high|highs|peak|top)\b")),
    ("na_vryh", _r(r"^(?:hits?|touches?|touched|(?:rises?|rose|climbs?|climbed|jumps?|jumped|surges?|surged|soars?|soared|rall(?:ies|ied)|"
                   r"advances?|advanced|shoots?) to|at|reaches?|reached|marks?|sets?|posts?|scales?)"
                   r" (?:nearly |almost |roughly |near )?(?:a |an |the |its |fresh |new )?(?:nearly |almost )?" + _PERIOD + r"[- ](?:high|highs|peak|top)\b")),
    ("rekord", _r(r"^(?:hits?|touches?|touched|(?:rises?|rose|climbs?|climbed|jumps?|jumped|surges?|surged|soars?|soared|rall(?:ies|ied)|shoots?) to|"
                  r"at|reaches?|reached|sets?|marks?|posts?|notches?|scales?|(?:ends?|closes?|finishes|settles?|opens?) at)"
                  r" (?:a |an |the |fresh |new )?(?:record|all-time)(?: high| peak| close)?s?\b")),
)
_GODINA_OT = _r(r"^(?:hits?|reaches?|reached|at|touches?|climbs? to|rises? to|jumps? to|surges? to|falls? to|drops? to|sinks? to) "
                r"(?:its |the )?(?P<kr>highest|lowest)(?: level| point| close)? since (?P<g>(?:19|20)\d\d)\b")


def _period_bg(m):
    u = m.group("u").lower()
    n = m.group("n").lower()
    if u in ("day", "session"):
        return "от дни" if n not in ("one", "1") else None
    if n in ("one", "1"):
        return None                        # «1-week low» — «от седмици» би било преувеличено
    return {"week": "от седмици", "month": "от месеци", "year": "от години"}.get(u)


_GLAGOLI = {
    # вид: {посока: (ед., мн.)}
    "цена": {"dolu": ("поевтинява", "поевтиняват"), "gore": ("поскъпва", "поскъпват"),
             "leko_dolu": ("леко поевтинява", "леко поевтиняват"), "leko_gore": ("леко поскъпва", "леко поскъпват"),
             "otskok": ("се връща нагоре", "се връщат нагоре"), "stoi": ("е без голяма промяна", "са без голяма промяна"),
             "natisk": ("е под натиск", "са под натиск")},
    "доход": {"dolu": ("спада", "спадат"), "gore": ("расте", "растат"),
              "leko_dolu": ("леко спада", "леко спадат"), "leko_gore": ("леко расте", "леко растат"),
              "otskok": ("се връща нагоре", "се връщат нагоре"), "stoi": ("е без голяма промяна", "са без голяма промяна"),
             "natisk": ("е под натиск", "са под натиск")},
    "акции": {"dolu": ("пада", "падат"), "gore": ("се качва", "се качват"),
              "leko_dolu": ("леко пада", "леко падат"), "leko_gore": ("леко се качва", "леко се качват"),
              "otskok": ("се връща нагоре", "се връщат нагоре"), "stoi": ("е без голяма промяна", "са без голяма промяна"),
             "natisk": ("е под натиск", "са под натиск")},
}


def _nivo_bg(vid_n, period, mn):
    e = "са" if mn else "е"
    nai = {"blizo_dyno": ("близо до ", "най-ниско"), "na_dyno": ("на ", "най-ниско"),
           "blizo_vryh": ("близо до ", "най-високо"), "na_vryh": ("на ", "най-високо")}[vid_n]
    sam = (nai[1] + "то си ниво") if not mn else (nai[1] + "те си нива")
    sam = sam.replace("най-високоте", "най-високите").replace("най-нискоте", "най-ниските")   # мн. ч.
    return "%s %s%s %s" % (e, nai[0], sam, period)


def _posoka(ostatak, vid, mn):
    """Какво прави предметът · фраза («поевтинява», «е близо до най-ниското си
       ниво от седмици») или None. Гледа се САМО прилепеното след предмета."""
    o = ostatak.strip()
    o = re.sub(r"^(?:today|again|on \w+day|early \w+day|in early trade|in asia|in europe)[,:]?\s+", "", o, flags=_I)
    m = _GODINA_OT.match(o)
    if m:
        g = int(m.group("g"))
        if datetime.now(timezone.utc).year - g >= 2:
            return _nivo_bg("na_vryh" if m.group("kr").lower() == "highest" else "na_dyno", "от години", mn)
        return None
    for vid_n, rx in _NIVA:
        m = rx.match(o)
        if not m:
            continue
        if vid_n == "rekord":
            return ("са на рекордни нива" if mn else "е на рекордно ниво")
        p = _period_bg(m)
        if p:
            return _nivo_bg(vid_n, p, mn)
        break                              # «rises to one-week high» — периодът не става, глаголът става
    for vid_p, rx in _POSOKI:
        m = rx.match(o)
        if m:
            # «Gold rebound stalls» — ходът е спрял, не върви
            if _SPIRA.match(o[m.end():]):
                return None
            ed, mnoj = _GLAGOLI[vid][vid_p]
            return mnoj if mn else ed
    return None


_SPIRA = _r(r"^\s+(?:stalls?|stalled|fades?|faded|falters?|faltered|fizzles?|fizzled|halts?|halted|loses steam|runs out|"
            r"reverses?|reversed|is over|ends)\b")


# ── фонът · най-много два, по важност ─────────────────────────────────────
_BLIZAK_IZTOK = _r(r"\b(?:Iran|Iranian|Israel|Israeli|Gaza|Hamas|Hezbollah|Houthis?|Yemen|Middle East|Mideast|Hormuz|Red Sea|Lebanon)\b")
_UKRAYNA = _r(r"\b(?:Russia|Russian|Ukraine|Ukrainian|Kremlin|Putin|Zelensky\w*)\b")
# «risk» е напрежение само до мястото («Hormuz risk», «Iran war risks», «Oil Supply Risks Deepen
# as Hormuz…»), не «…Iran Bypasses US Sanctions as Oil Enigma Deepens Sell-Off Risk»;
# «clash with» е образ («Iran diplomacy hopes clash with hawkish Fed expectations»)
_NAPREZHENIE = _r(r"\b(?:war|wars|conflict|tensions?|attacks?|attacked|strikes?|struck|missiles?|drones?|(?<!de-)escalat\w*|crisis|"
                  r"blockade|clashes|clashed|clash(?! with)|fighting|hostilities|invasion|military|bombing|shelling|threats?|unrest|"
                  r"sanctions?)\b")
_RISK = _r(r"\brisks?\b")
_MIR = _r(r"\b(?:ceasefire|cease-fire|truce|peace(?: (?:talks|deal|plan|agreement|process|push|efforts?|proposal|offer|bid|hopes?|negotiations?))?|"
          r"de-escalat\w*)\b")
_PRIMIRIE = _r(r"\b(?:ceasefire|cease-fire|truce)\b")
# мирът е ПРОВАЛЕН: отхвърлен, рухнал, нарушен… → това е напрежение, не мир
_MIR_PROVAL = _r(r"\b(?:rejects?|rejected|rejecting|rebuff\w*|spurn\w*|dismiss\w*|collaps\w*|breaks? down|broke down|broken|"
                 r"fails?|failed|failing|falls? apart|fell apart|falter\w*|fades?|faded|fading|stall\w*|violat\w*|breach\w*|"
                 r"shatter\w*|crumbl\w*|derail\w*|scuttl\w*|dashed|dims?|dimmed|doubts?|jeopardi\w*|"
                 r"no (?:ceasefire|cease-fire|truce|peace|deal)|without (?:a )?(?:ceasefire|cease-fire|truce|peace|deal)|"
                 r"lack of|refuses?|refused|postpon\w*|delay\w*|cancel\w*|calls? off|called off)\b")
# успокояване: пауза в ударите, дипломация, отслабващо напрежение — с напрежение заедно = не е ясно
_DIPLOMACIA = _r(r"\bdiplomac\w*|\bdiplomatic\b|\btalks with\b|\bnegotiat\w*")
_UTIHVANE = _r(r"\b(?:pause[sd]?|pausing|halt\w*|suspend\w*|pull(?:s|ed)? back|withdraw\w*|de-escalat\w*|calm\w*|"
               r"(?:tensions?|fears?|worries) (?:ease[sd]?|easing|cool\w*|recede\w*|subside\w*|fade[sd]?)|easing tensions?|"
               r"eases? (?:tensions?|fears?)|relief)\b")
# думи, които казват, че примирието още НЕ е факт
_MIR_NE_FAKT = _r(r"\b(?:hopes?|hoped|hoping|optimism|talks|negotiat\w*|offer\w*|propos\w*|plan|push|bid|efforts?|calls? for|"
                  r"urges?|seeks?|seeking|possible|potential|prospects?|could|may|might|would|likely|nears?|close to|brokers?|"
                  r"diplomac\w*|deal)\b|\?")


def _blizo_do(rx_a, rx_b, t, prozorec=40):
    """Има ли rx_b на ≤ prozorec знака от някое rx_a."""
    for m in rx_a.finditer(t):
        if rx_b.search(t[max(0, m.start() - prozorec):m.end() + prozorec]):
            return True
    return False


def _geo_fon(t, rx_myasto, napr_fraza, kyde):
    """Фонът за едно място (Близкия изток · Украйна) · фраза или None, когато не е ясно."""
    napr = bool(_NAPREZHENIE.search(t)) or _blizo_do(rx_myasto, _RISK, t, 25)
    mir = bool(_MIR.search(t))
    # «Oil hits $108 as Gulf states postpone talks with Iran over Hormuz» — и отложената дипломация е провал
    proval = (mir and _blizo_do(_MIR, _MIR_PROVAL, t, 40)) or _blizo_do(_DIPLOMACIA, _MIR_PROVAL, t, 30)
    if proval:
        return napr_fraza                  # «Trump rejects Iran truce offer» → напрежение
    utih = bool(_UTIHVANE.search(t)) or bool(_DIPLOMACIA.search(t))
    if napr and not (mir or utih):
        return napr_fraza
    if napr:
        return None                        # и война, и успокояване в едно заглавие — без фон
    if _PRIMIRIE.search(t) and not _blizo_do(_PRIMIRIE, _MIR_NE_FAKT, t, 40):
        return "примирието " + kyde        # «Oil falls as Israel-Iran ceasefire holds»
    if _DIPLOMACIA.search(t):
        return "дипломатическите усилия " + kyde
    if mir or _r(r"\bde-escalat\w*").search(t):
        return ("надеждите за мир " if re.search(r"\bhop\w*|\boptimism\b", t, _I) else "усилията за мир ") + kyde
    return None
_MITA = _r(r"\b(?:tariffs?|trade war|trade tensions?|trade dispute|trade spat|levies)\b")
_TARGOVIYA = _r(r"\b(?:trade (?:deal|talks|agreement|truce|negotiations?))\b")
# «покупките» само с дума за купуване до централните банки: «Central Banks Are Hiking Again, Yet
# Gold Keeps Climbing» е за лихвите, не за покупки на злато (30.09)
_CB_ZLATO = _r(r"^(?=.*\bgold\b).*?(?:\b(?:central banks?|PBOC)(?:'s?)?\b.{0,50}?\b(?:buy|buys|buying|bought|purchas\w*|demand|"
               r"accumulat\w*|hoard\w*|stockpil\w*|adds?|adding|added)\b|\b(?:buying|purchases?|purchasing|demand|accumulation|"
               r"hoarding|stockpiling)\b.{0,30}\b(?:by|from|of|among) (?:the )?(?:central banks?|PBOC)\b|"
               r"\bcentral[- ]bank (?:gold )?(?:buying|purchases?|demand|accumulation|hoarding)\b)")
# «Oil Stocks» са акции на петролни компании, не цената на петрола; «XAU/USD» е
# златото, не доларът; «Treasuries» сами са облигациите, не доходността им
_PETROL = _r(r"\b(?:oil|crude|brent|WTI)\b(?! (?:stocks|majors|companies|firms|producers|shares|giant))")
_DOLAR = _r(r"\b(?:dollar|greenback|DXY)\b|(?<![/\w])USD(?![/\w])")
_DOHOD = _r(r"\byields?\b")
_SHUTDOWN = _r(r"\b(?:government )?shutdown\b")


# «преди» · събитието предстои: «ahead of the Fed decision», «jobs data looms»,
# «markets await Fed signals». Иначе връзката е «на фона на».
_PREDI_PRED = _r(r"\b(?:ahead of|before|awaits?|awaiting|eye|eyes|eyeing|braces? for|bracing for|in the run-up to|"
                 r"prepares? for|preparing for|countdown to|watch(?:es|ing)? for|looks? ahead to|"
                 # «Gold rebounds as traders position for Fed interest rate decision» (30.09)
                 r"position(?:s|ing|ed)? (?:themselves )?(?:for|into)|gears? up for|gearing up for)\b"
                 # «Wobbles Before Settling After Fed Raises Rates» — «before» е за друго, решението е минало
                 r"(?:\s+(?!(?:after|following|since|post)\b)[\w'.,&%$-]+){0,5}\s*$")
_PREDI_SLED = _r(r"^(?:\s+[\w'.-]+){0,2}\s+(?:looms?|looming|due|up next|on tap|on deck|in focus|test|approach(?:es)?|approaching|"
                 r"nears|nearing|next week|this week|later this week|coming up|ahead(?! of))\b")


def _predstoi(t, poz, kraj):
    """Предстои ли събитието · само в своето изречение: «…surging ahead of midterms. Will
       Fed rate hikes actually help?» — «ahead of» е за изборите, не за Фед."""
    predi = t[max(0, poz - 60):poz]
    k = max(predi.rfind(". "), predi.rfind("? "), predi.rfind("! "), predi.rfind("; "))
    if k >= 0:
        predi = predi[k + 2:]
    return bool(_PREDI_PRED.search(predi) or _PREDI_SLED.search(t[kraj:kraj + 40]))


def _pyrvo(rx, t):
    m = rx.search(t)
    return (m.start(), m.end()) if m else None


def _fonove(t, predmet_klyuch=None, s_glagol=False, samo_silni=False):
    """Фонът на новината · до два, по важност · [(фраза, предстои)]."""
    out = []

    def dobavi(fraza, mesto, moje_predi=True):
        if fraza and mesto and all(fraza != x[0] for x in out):
            out.append((fraza, moje_predi and _predstoi(t, mesto[0], mesto[1])))

    f, f_vid = _fed_kontekst(t, s_vid=True)
    if f == "Фед" and s_glagol:
        f = None                          # «Златото поскъпва на фона на Фед» не казва нищо вярно
    if f:
        # очакванията са сега по природа, станалото е станало; «преди» може само
        # решението, изказванията и общите решения («ahead of the Fed decision»)
        dobavi(f, _pyrvo(_r(r"\bFed\b|\bFederal Reserve\b|\bFOMC\b|\brate[- ]hikes?\b|\brate[- ]cuts?\b"), t),
               moje_predi=f_vid in _FON_MOJE_PREDI)
    d = _danni(t)
    if d:
        m = None
        for rx, *_ in _DANNI:
            mm = rx.search(t)
            if mm and mm.start() == d[2]:
                m = (mm.start(), mm.end())
                break
        dobavi(d[1], m or (d[2], d[2] + 3))
    if _CB_ZLATO.search(t) and predmet_klyuch != "cb":
        dobavi("покупките на злато от централните банки", _pyrvo(_r(r"\bcentral banks?\b|\bPBOC\b"), t))
    # Геополитиката · никога «преди» (войната не е насрочено събитие: «Gold drops to three-day
    # low, eyes $4,300 as … Iran risks» НЕ е «преди напрежението»). Мирът и напрежението — по
    # _geo_fon (отхвърленото примирие е напрежение, не примирие · втората проверка, 29.09).
    m = _pyrvo(_BLIZAK_IZTOK, t)
    g = _geo_fon(t, _BLIZAK_IZTOK, "напрежението в Близкия изток", "в Близкия изток") if m else None
    if g:
        dobavi(g, m, moje_predi=False)
    elif m:
        pass                               # Близкият изток е тук, но не е ясно какво — без фон
    elif _UKRAYNA.search(t):
        g = _geo_fon(t, _UKRAYNA, "войната в Украйна", "в Украйна")
        if g:
            dobavi(g, _pyrvo(_UKRAYNA, t), moje_predi=False)
    elif re.search(r"\bgeopolitic\w*\b", t, _I):
        dobavi("геополитическото напрежение", _pyrvo(_r(r"\bgeopolitic\w*\b"), t), moje_predi=False)
    if _MITA.search(t):
        dobavi("митата", _pyrvo(_MITA, t))
    elif _TARGOVIYA.search(t):
        dobavi("търговските преговори", _pyrvo(_TARGOVIYA, t))
    if _SHUTDOWN.search(t):
        dobavi("спирането на работата на правителството на САЩ", _pyrvo(_SHUTDOWN, t))
    if samo_silni:
        # без предмет в началото слабият фон (петрол, долар, доходност) лъже:
        # «The Dollar-Gold Standard's Lingering Demise» НЕ е «златото и движението на долара»
        return out[:2]
    # Слабият фон — само с дума за ход до него (20 знака преди, 36 след): «Dollar Debt Crisis» не е
    # «движението на долара», «oil prices rise» е «цената на петрола».
    def s_hod(mesto):
        if not mesto:
            return None
        # «Gold gains as US Dollar and yields pause» — доларът стои, не се движи (30.09)
        if re.match(r"^(?:\s+(?:and|&)\s+[\w-]+)?\s+(?:pauses?|paused|pausing|steady|steadies|steadied|(?:is |are )?flat|"
                    r"unchanged|little changed|stalls?|stalled|stable|holds? steady)\b", t[mesto[1]:], _I):
            return None
        return mesto if _HOD.search(t[max(0, mesto[0] - 20):mesto[1] + 36]) else None
    if predmet_klyuch not in ("Петролът",):
        dobavi("цената на петрола", s_hod(_pyrvo(_PETROL, t)), moje_predi=False)
    if predmet_klyuch not in ("Доларът",) and not re.search(
            r"\b(?:Canadian|Australian|Aussie|Singapore|Hong Kong|Taiwan|New Zealand) dollar\b", t, _I):
        dobavi("движението на долара", s_hod(_pyrvo(_DOLAR, t)), moje_predi=False)
    if predmet_klyuch not in ("Доходността на американските облигации", "Доходността на облигациите") \
            and not re.search(r"\bhigh-yield\b", t, _I):
        dobavi("доходността на облигациите", s_hod(_pyrvo(_DOHOD, t)), moje_predi=False)
    return out[:2]


_HOD = _r(r"\b(?:price|prices|rises?|rose|rising|surges?|surged|surging|soars?|soared|jumps?|jumped|climbs?|climbed|gains?|"
          r"rall\w*|spikes?|spiking|higher|lower|falls?|fell|falling|drops?|dropped|slides?|slid|slump\w*|plunge\w*|dips?|"
          r"eases?|eased|easing|declines?|declin\w*|retreats?|weak\w*|strong\w*|firm\w*|soft\w*|rebounds?|strength|"
          r"highs?|lows?|peak|record|shock|move|moves|swings?|volatil\w*|index|DXY|real|flying|surge|up|down|"
          r"relief|slump|decouple\w*|pressure|cap|caps|weigh\w*|lift\w*|boost\w*|squeez\w*)\b|[\d%$]")


def _i(spisak):
    return " и ".join(spisak)


def _sabiraj(glava, fonove, ima_glagol):
    """Главата + фонът. «на фона на» — за сега; «преди» — за предстоящото.
       Без глагол: «Златото и очакванията…» (само съседство, без причина)."""
    if not fonove:
        return glava
    sega = [f for f, p in fonove if not p]
    predi = [f for f, p in fonove if p]
    predi = ["новините за митата" if f == "митата" else f for f in predi]
    if ima_glagol:
        r = glava
        if sega:
            r += " на фона на " + _i(sega)
        if predi:
            r += (", преди " if sega else " преди ") + _i(predi)
        return r
    if predi:
        return glava + " преди " + _i(predi) + ((", на фона на " + _i(sega)) if sega else "")
    # «Златото и среброто и цената на петрола» → «Златото, среброто и цената на петрола»
    g = glava.replace(" и ", ", ")
    if len(sega) == 1:
        return g + " и " + sega[0]
    return g + ", " + sega[0] + " и " + sega[1]


# ══════════════════════════════════════════════════════════════════════════
#  6 · ОСТАНАЛИТЕ СЪБИТИЯ
# ══════════════════════════════════════════════════════════════════════════
_ZLATO = _r(r"\b(?:gold|bullion|XAU/?USD|XAUUSD)\b")
# изрази със «gold», които не са за златото: «Fool's gold: How geopolitical risk is taking
# some of the shine off the US dollar» е за долара
_IDIOMI = _r(r"\bfool's gold\b|\bgolden (?:age|rule|opportunity|goose|ticket|handshake|parachute|era|boy|girl|visa|years)\b|"
             r"\bgold standard\b|\bgold (?:medals?|medalist|card|star|rush|mine of)\b|\bgoldilocks\b|\bgold-plated\b")
_BANKI = ("Goldman Sachs", "JPMorgan", "J.P. Morgan", "JP Morgan", "Wells Fargo", "UBS", "Citi", "Citigroup",
          "Morgan Stanley", "Bank of America", "BofA", "HSBC", "Deutsche Bank", "Commerzbank", "ANZ",
          "Macquarie", "Societe Generale", "BNP Paribas", "ING", "Barclays", "Standard Chartered", "Julius Baer",
          "Saxo", "Jefferies", "RBC", "TD Securities", "BMO", "Scotiabank", "Nomura", "Mizuho")
_BANKA = r"(?P<banka>" + "|".join(re.escape(b) for b in _BANKI) + r")"
_BANKA_PROGNOZA = _r(r"^" + _BANKA + r"(?:'s?)?\s+(?:\w+\s+)?(?P<gl>raises|lifts|hikes|boosts|ups|lowers|cuts|trims|slashes|reduces|revises|"
                     r"maintains|keeps|reiterates|affirms)"
                     r" (?:its |their )?(?:[\w-]*\d{4} )?(?:(?P<met>gold|silver)(?: price)?(?: forecasts?| targets?| outlook| estimates?)|"
                     r"(?:price )?(?:forecasts?|targets?|outlook) (?:for|on) (?P<met2>gold|silver))", 0)
_CB_KUPUVA = _r(r"\bcentral banks?\b.{0,40}\b(?:buy|buys|buying|bought|purchases?|purchased|purchasing|adds?|added|adding|"
                r"accumulat\w*|hoard\w*|snap(?:s|ped)? up|stockpil\w*|boosts? (?:its |their )?gold)\b|"
                r"\b(?:PBOC|People's Bank of China|China's central bank)\b.{0,40}\b(?:buy|buys|buying|bought|adds?|added|adding|extends? gold)\b")
_CB_PRODAVA = _r(r"\bcentral banks?\b.{0,40}\b(?:sell|sells|selling|sold|offload\w*|dump\w*)\b.{0,20}\bgold\b")
_ETF = _r(r"\b(?:gold|silver|bullion)(?:-backed)? (?:ETFs?|ETPs?|exchange-traded funds?|funds)\b|\bSPDR Gold\b|\bGLD\b|\biShares Gold\b|\bSLV\b")
_ETF_VLIZA = _r(r"\binflows?\b|\bholdings (?:rise|rose|climb|jump|increase)\w*|\b(?:buying|demand) (?:rises|rose|jumps|surges)|"
                r"\bpour\w* .{0,30}\binto\b|\bpiled? into\b|\bflock(?:ed|s)? (?:to|into)\b")
_ETF_IZLIZA = _r(r"\boutflows?\b|\bholdings (?:fall|fell|drop|decline|slip)\w*")
_DNES = _r(r"^(?:the )?(?:current )?(?:price of gold|gold prices?|gold rates?|gold price|spot gold price)(?: today| now)\b|"
           r"^(?:the )?price of gold today\b|^current price of gold\b|^gold (?:price|rate)s? today\b|"
           r"^(?:the )?(?:current )?(?:price of silver|silver prices?|silver price|silver rates?)(?: today| now)\b|^current price of silver\b")
_PROGNOZA = _r(r"^(?P<met>gold|silver|platinum|palladium|copper|XAU/?USD|XAUUSD|XAG/?USD|(?:the )?(?:US |U\.S\. )?dollar|DXY|"
               r"(?:crude )?oil|WTI|brent)(?: \((?:XAU/?USD|XAG/?USD)\))?(?: (?:&|and) (?:silver|gold))?"
               r"(?: price| prices| index)?(?: q[1-4] \d{4})?(?: (?:technical|weekly|daily|monthly|near-term|short-term|long-term))?"
               r" (?:price )?(?:forecasts?|outlook|prediction|analysis|technical analysis|price prediction)\b")
_PROGNOZA_IME = (("gold", "златото"), ("xau", "златото"), ("silver", "среброто"), ("xag", "среброто"),
                 ("platinum", "платината"), ("palladium", "паладия"), ("copper", "медта"), ("dollar", "долара"),
                 ("dxy", "долара"), ("oil", "петрола"), ("wti", "петрола"), ("brent", "петрола"))
# злато за мините: и «g/t Au» (Au с главна — химичният знак, не думата)
_ZLATO_MINI = re.compile(r"(?i:\b(?:gold|bullion)\b)|\bAu\b")
# без «oz/ounces»: «Goldman Sachs maintains its forecast for gold at USD 5,400/oz» НЕ е минна новина
_MINNI = _r(r"\b(?:drill\w*|intersects?|intersections?|intercepts?|assays?|mineraliz\w*|mineralis\w*|g/t|"
            r"exploration|prospecting|resource estimate|feasibility|PEA|deposit|mine|mines|miners?|mining|"
            # «streaming» само като сделка на мините: «Gold Futures Streaming Chart» е графика (30.09)
            r"royalty|royalties|streaming (?:company|companies|deal|agreement|interest|portfolio|business)|streamers?|"
            r"(?:first |gold )pour|mill|ore|tailings)\b")
# РЕЗУЛТАТИ от сондажи — само с белезите на резултат (засечен интервал, грамове на тон).
# «Drill Targets», «Starts Drilling», «Drill Program Update» НЕ са резултати.
_SONDAZHI = _r(r"\b(?:intersects?|intersections?|intercepts?|g/t|drill(?:ing)? results|assay results|drills \d)")
_NE_REZULTAT = _r(r"\b(?:targets?|permits?|starts?|begins?|commences?|plans?|planned|to drill|program|programme|mobiliz\w*)\b")
_DRUGI_CB = (
    (r"\b(?:ECB|European Central Bank)\b", "ЕЦБ"),
    (r"\b(?:BoE|BOE|Bank of England)\b", "Английската централна банка"),
    (r"\b(?:BoJ|BOJ|Bank of Japan)\b", "Японската централна банка"),
    (r"\b(?:PBOC|PBoC|People's Bank of China)\b", "Китайската централна банка"),
    (r"\b(?:BoC|Bank of Canada)\b", "Канадската централна банка"),
    (r"\b(?:RBA|Reserve Bank of Australia)\b", "Австралийската централна банка"),
    (r"\b(?:RBI|Reserve Bank of India)\b", "Индийската централна банка"),
    (r"\b(?:SNB|Swiss National Bank)\b", "Швейцарската централна банка"),
    (r"\b(?:RBNZ|Reserve Bank of New Zealand)\b", "Новозеландската централна банка"),
    (r"\bBanxico\b", "Мексиканската централна банка"),
)
_DRUGI_CB_RE = tuple((re.compile(p), bg) for p, bg in _DRUGI_CB)
_DRZHAVA_LIHVA = _r(r"^(?P<d>Australia|Canada|Japan|India|Britain|UK|New Zealand|Switzerland|Mexico|Brazil|Turkey|South Korea|Norway|Sweden)"
                    r"(?:'s central bank)? (?P<gl>raises|hikes|lifts|cuts|lowers|holds|keeps|leaves)\b.{0,30}\b(?:interest )?rates?\b", 0)
_DRZHAVA_CB_BG = {"Australia": "Австралийската", "Canada": "Канадската", "Japan": "Японската", "India": "Индийската",
                  "Britain": "Английската", "UK": "Английската", "New Zealand": "Новозеландската",
                  "Switzerland": "Швейцарската", "Mexico": "Мексиканската", "Brazil": "Бразилската",
                  "Turkey": "Турската", "South Korea": "Южнокорейската", "Norway": "Норвежката", "Sweden": "Шведската"}


def _cb_reshenie(t, ime):
    """«ECB raises rates» → «ЕЦБ вдигна лихвата». Само прилепен глагол."""
    for rx, bg in _DRUGI_CB_RE:
        m = rx.search(t)
        if not m or m.start() > 3:
            continue
        o = t[m.end():]
        o = re.sub(r"^(?:'s)?\s+(?:just |unexpectedly |surprisingly |officially )?", " ", o)
        if re.match(r"^ (?:raises|raised|hikes|hiked|lifts|lifted)\b.{0,40}\brates?\b", o, _I):
            return bg + " вдигна лихвата"
        if re.match(r"^ (?:cuts|cut|lowers|lowered|slashes|slashed)\b.{0,40}\brates?\b", o, _I):
            return bg + " намали лихвата"
        if re.match(r"^ (?:holds|held|keeps|kept|leaves|left|maintains)\b.{0,40}\brates?\b", o, _I):
            return bg + " запази лихвата"
    m = _DRZHAVA_LIHVA.match(t) or _DRZHAVA_LIHVA_PAS.match(t)
    if m:
        cb = _DRZHAVA_CB_BG[m.group("d")] + " централна банка"
        gl = m.group("gl").lower()
        if gl in ("raises", "hikes", "lifts", "raised", "hiked", "lifted", "increased"):
            return cb + " вдигна лихвата"
        if gl in ("cuts", "lowers", "cut", "lowered", "reduced"):
            return cb + " намали лихвата"
        return cb + " запази лихвата"
    return None


# «Japan's interest rate hiked to 31-year high at 1.25% as inflation rises» — решението на
# банката, не данни за инфлацията (30.09)
_DRZHAVA_LIHVA_PAS = _r(r"^(?P<d>Australia|Canada|Japan|India|Britain|UK|New Zealand|Switzerland|Mexico|Brazil|Turkey|South Korea|"
                        r"Norway|Sweden)(?:'s)? (?:key |benchmark |policy |main )?(?:interest )?rate (?:is |was |has been )?"
                        r"(?P<gl>hiked|raised|lifted|increased|cut|lowered|reduced|held|kept|left)(?= (?:to|by|at|unchanged|steady)\b)")


# ══════════════════════════════════════════════════════════════════════════
#  7 · ГЛАВНОТО
# ══════════════════════════════════════════════════════════════════════════
# Общите етикети пред двоеточие («Gold News:», «Update:») не са предметът —
# предметът се търси и след тях.
_ETIKET = _r(r"^(?:[\w&.,'/ -]{2,40}?):\s+")
_FED_NACHALO = _r(r"^(?:the )?(?:US |U\.S\. )?(?:" + _MESECI + r" )?(?:Fed|Federal Reserve|FOMC)\b")
_DRUG_CB_IMA = re.compile("|".join(p for p, _ in _DRUGI_CB) + r"|\bcentral bank\b(?! of the U)")


def _predmet(t):
    """[(име, вид, мн, остатък)] — предметът в началото и/или след етикет с
       двоеточие («Sterling today: Pound slips…» → и «Sterling», и «Pound»)."""
    kandidati = [t]
    m = _ETIKET.match(t)
    if m:
        kandidati.append(t[m.end():])
    out = []
    for k in kandidati:
        for rx, bg, vid, mn in _PREDMETI_RE:
            mm = rx.match(k)
            if mm:
                out.append((bg, vid, mn, k[mm.end():], mm.group(0)))
                break
    return out


# «Wall Street» е и общността, не само борсата: «Wall Street turns bullish on gold»,
# «Wall Street braces for more Fed rate hikes» — като предмет само с глагол за посока
_SAMO_S_GLAGOL = _r(r"^wall st")
# не и «Trump adviser blasts Fed rate increase» — говори съветникът, не Тръмп
_TRAMP = _r(r"^(?:(?:US |U\.S\. )?President )?(?:Donald )?Trump(?:'s)?\b(?! (?:adviser|advisor|aide|administration|official|team|"
            r"economic|economist|pick|picked|nominee|ally|allies|camp|appointee|-picked))(?!-)")
# «Ahead of Fed meeting, Trump says…» — говори Тръмп; проверява се СЛЕД «Фед начело»,
# защото «Fed hikes key rate, defying Trump demands for a cut» е решението на Фед
_TRAMP_KAZVA = _r(r"\bTrump (?:says|said|urges|urged|calls|called|pushes|pushed|presses|pressed|wants|slams|"
                  r"attacks|criticizes|criticises|blasts|renews|repeats|again)\b")


def _tramp_red(t, fed_poz):
    if fed_poz:
        f = _fed_kontekst(t)
        return "Тръмп и " + ("решението на Фед за лихвата" if f == "решението на Фед за лихвата" else "лихвата на Фед")
    # митата — само ако са до името («Trump promises $5,000 checks… He also teased tariff…» НЕ е за митата)
    m = re.search(r"\bTrump\b", t)
    if m and _MITA.search(t[m.start():m.start() + 45]):
        return "Тръмп и митата"
    return None


def bg_red(zaglavie, emisiya=None, izvor=None):
    """Българският ред за една новина · низ или None (правилата не са сигурни).

    >>> bg_red("Barr, Economic Conditions and Monetary Policy", "Fed речи")
    'Реч на член на Фед (Barr) за паричната политика и икономиката'
    """
    t = _norm(zaglavie)
    if not t or len(t) < 8 or _KIRILICA.search(t):
        return None                      # празно или вече на кирилица — редът не е нужен
    t = re.sub(r"\s+", " ", _IDIOMI.sub(" ", t)).strip()
    # 1 · самите емисии на Фед
    if emisiya in FED_EMISII:
        return _fed_emisiya(t, emisiya)
    # 2 · изказване на човек от Фед
    r = _fed_chovek(t)
    if r:
        return r
    # 3 · централните банки и златото · фондовете за злато · банка сменя прогнозата
    if _CB_PRODAVA.search(t):
        return "Централни банки продават злато"
    if _CB_KUPUVA.search(t) and _ZLATO.search(t):
        if re.search(r"\b(?:PBOC|People's Bank of China|China's central bank)\b", t, _I):
            return "Китайската централна банка купува злато"
        return "Централни банки купуват злато"
    m = _ETF.search(t)
    if m:
        met = "среброто" if re.search(r"silver|SLV", m.group(0), _I) else "златото"
        if _ETF_IZLIZA.search(t) and not _ETF_VLIZA.search(t):
            return "Пари излизат от борсовите фондове за %s (ETF)" % met
        if _ETF_VLIZA.search(t) and not _ETF_IZLIZA.search(t):
            return "Пари влизат в борсовите фондове за %s (ETF)" % met
    m = _BANKA_PROGNOZA.search(t)
    if m:
        met = "златото" if (m.group("met") or m.group("met2")).lower() == "gold" else "среброто"
        gl = m.group("gl").lower()
        posoka = "вдига" if gl in ("raises", "lifts", "hikes", "boosts", "ups") else \
                 ("сваля" if gl in ("lowers", "cuts", "trims", "slashes", "reduces") else
                  ("запазва" if gl in ("maintains", "keeps", "reiterates", "affirms") else "променя"))
        return "%s %s прогнозата си за %s" % (m.group("banka"), posoka, met)
    # 4 · страниците «цената на златото днес» · металът е този, който правилото хвана
    m = _DNES.search(t)
    if m:
        return "Цената на " + ("среброто" if re.search(r"silver", m.group(0), _I) else "златото") + " днес"
    # 5 · анализ и прогноза (на изданието) за метал, долар, петрол
    m = _PROGNOZA.search(t) or (_PROGNOZA.search(t[_ETIKET.match(t).end():]) if _ETIKET.match(t) else None)
    if m:
        met = m.group("met").lower()
        ime = next((bg for k, bg in _PROGNOZA_IME if k in met), None)
        if ime:
            if re.match(r"^(?:gold|XAU/?USD)(?: \(XAU/USD\))? (?:&|and) silver", t, _I):
                ime = "златото и среброто"
            return "Анализ и прогноза за " + ime
    # 6 · предмет в началото: злато, долар, доходност, акции… + посока + фон.
    #     От двата кандидата (преди и след етикета) печели този с посока.
    kand = _predmet(t)
    if kand:
        nai = None
        for glava, vid, mn, ostatak, _tekst in kand:
            pos = _posoka(ostatak, vid, mn)
            if pos:
                nai = (glava, pos, ostatak)
                break
        if nai:
            return _sabiraj(nai[0] + " " + nai[1], _fonove(nai[2], nai[0], True), True)
        kand = [k for k in kand if not _SAMO_S_GLAGOL.match(k[4])]
        if kand:
            glava, vid, mn, ostatak, _tekst = kand[0]
            fon = _fonove(ostatak, glava)
            if fon:
                return _sabiraj(glava, fon, False)
    fed_poz = re.search(r"\bFed\b|\bFederal Reserve\b|\bFOMC\b", t, _I)
    drug_cb = _DRUG_CB_IMA.search(t)
    fed_pryv = fed_poz and not (drug_cb and drug_cb.start() < fed_poz.start())
    # 6б · Тръмп начело: той говори ЗА лихвата, не я решава («Trump urges Fed to cut
    #      rates» НЕ е «намаляване на лихвата»)
    if _TRAMP.match(t):
        return _tramp_red(t, fed_poz)
    # 7 · Фед е новината
    if fed_pryv and (_FED_NACHALO.search(t) or (_ETIKET.match(t) and _FED_NACHALO.search(t[_ETIKET.match(t).end():]))):
        r = _fed_red(t)
        if r:
            return r
    if _TRAMP_KAZVA.search(t):
        return _tramp_red(t, fed_poz)
    # 8 · данните — освен когато начело стои решение на друга централна банка (30.09)
    d = _danni(t)
    r_cb = _cb_reshenie(t, None)
    if d and not r_cb and (not fed_poz or d[2] <= fed_poz.start()):
        return d[0]
    # 9 · други централни банки · решение, или «<банката> и Фед», когато тя води
    r = r_cb
    if r:
        return r
    if fed_poz and not fed_pryv:
        for rx, bg in _DRUGI_CB_RE:
            m = rx.search(t)
            if m and m.start() <= 3:
                return bg + " и Фед"
    # 10 · Фед, споменат не в началото · без «Фед вдигна» (новината е за друго) и
    #      не когато пред Фед стои друга централна банка («Banxico … independently of Fed»).
    #      Има ли злато в заглавието — «Златото и <Фед>» казва повече от «За лихвата на Фед»
    #      («Citi Trims Gold Positions Amid Tighter Fed Policy View»).
    # минна новина — само ако начело не стои друг предмет («Bond Yields Are Pressuring Gold,
    # But Miners May Tell a Different Story» е за доходността, не за мина)
    mini = _ZLATO_MINI.search(t) and _MINNI.search(t) and not re.search(r"\b(?:price|prices)\b", t, _I) \
        and not any(k[0] not in ("Златото", "Златото и среброто", "Среброто и златото") for k in (kand or []))
    if fed_pryv:
        if _ZLATO.search(t) and not mini:
            fon = _fonove(t, samo_silni=True)
            if fon:
                return _sabiraj("Златото", fon, False)
        r = _fed_red(t, nachalo=False)
        if r:
            return r
    if d:
        return d[0]
    # 11 · минните компании (златото е в заглавието, а думите са от мините)
    if mini:
        if _SONDAZHI.search(t) and not _NE_REZULTAT.search(t):
            return "Минна компания съобщава резултати от сондажи за злато"
        return "Новина от минния бранш (злато)"
    # 12 · фон без предмет: злато + Фед/данни/война/мита (слабият фон не стига)
    if _ZLATO.search(t):
        fon = _fonove(t, samo_silni=True)
        if fon:
            return _sabiraj("Златото", fon, False)
    return None


# ══════════════════════════════════════════════════════════════════════════
#  8 · ПРОВЕРКАТА · python -X utf8 novini_bg.py --proveri [novini.json]
# ══════════════════════════════════════════════════════════════════════════
# Всеки ред е ръчно проверен: заглавие → очакван ред (None = правилата мълчат).
PRIMERI = (
    # емисиите на Фед · 29.09 живо
    ("Barr, Economic Conditions and Monetary Policy", "Fed речи",
     "Реч на член на Фед (Barr) за паричната политика и икономиката"),
    ("Bowman, Opening Remarks", "Fed речи", "Встъпително слово на член на Фед (Bowman)"),
    ("Cook, An Update on AI and the Economy", "Fed речи", "Реч на член на Фед (Cook) за изкуствения интелект и икономиката"),
    ("Warsh, In Our Time", "Fed речи", "Реч на член на Фед (Warsh)"),
    ("Federal Reserve issues FOMC statement", "Fed политика", "Решението на Фед за лихвата (изявлението на FOMC)"),
    ("Minutes of the Federal Open Market Committee, July 28–29, 2026", "Fed политика",
     "Протоколът от заседанието на Фед за лихвата (FOMC)"),
    # изказвания
    ("Fed's Barr signals further rate hikes needed as inflation risks rise", None,
     "Изказване на член на Фед (Barr) за вдигане на лихвата и инфлацията"),
    ("Fed's Lisa Cook Says AI Is Fueling Inflation — Warns Labor Market Faces a 'Painful Transition'", None,
     "Изказване на член на Фед (Cook) за инфлацията и пазара на труда"),
    ("Tim Cook says Apple will invest more in AI", None, None),
    ("Trump attacks Fed's Powell over rates", None, "Тръмп и лихвата на Фед"),
    ("Trump again calls for Federal Reserve to cut interest rates", None, "Тръмп и лихвата на Фед"),
    ("Former Fed Governor Warsh says rates should fall", None, "За лихвата на Фед"),
    # грешките от първото пускане върху live/novini.json (29.09) — да не се върнат
    ("Banxico can chart rate path independently of Fed, Governor says - Bloomberg", None, "Мексиканската централна банка и Фед"),
    ("USD Rates: Bill financing costs rise with Fed hikes - DBS", None, "За вдигане на лихвата от Фед"),
    ("Gold Price Today, Sep 29: Gold, Silver Rates Fall Amid US-Iran Conflict; Check City-Wise Prices", None,
     "Цената на златото днес"),
    ("NevGold Defines Multiple High-Priority Drill Targets Including Key Feeder Structures at Nutmeg Mountain Gold Project", None,
     "Новина от минния бранш (злато)"),
    ("Blue Lagoon Starts Drilling at Dome Mountain Gold Mine", None, "Новина от минния бранш (злато)"),
    ("Oil Extends Rally Despite Higher Hormuz Volume Reports", None, "Петролът поскъпва"),
    ("Gold Tests $4,143 as the VC PMI Mean Holds Overhead", None, None),
    ("Sterling today: Pound slips as oil-fuelled dollar demand builds", None, "Британската лира поевтинява"),
    ("Dollar firms near two-month peak as oil, US yields rise; jobs data looms", None,
     "Доларът е близо до най-високото си ниво от месеци на фона на цената на петрола, преди данните за заетостта в САЩ"),
    # решения и очаквания
    ("Federal Reserve raises interest rates", None, "Фед вдигна лихвата"),
    ("Fed Expected To Hike Rates Next Week as Inflation Remains Hot at 3.4%", None, "Очаквания за по-висока лихва от Фед"),
    ("What a Fed rate hike could mean for mortgage rates (and what borrowers need to do now)", None,
     "Какво значи вдигане на лихвата от Фед"),
    # данни
    ("JOLTS Job Openings", None, "Данни за свободните работни места в САЩ (JOLTS)"),
    ("UK inflation rises to 4% in August", None, "Данни за инфлацията във Великобритания"),
    ("What To Expect From Wednesday's Report On Inflation", None, "Данни за инфлацията"),
    # предмет + посока + фон
    ("Gold near seven-week low as Fed rate-hike fears mount", None,
     "Златото е близо до най-ниското си ниво от седмици на фона на очакванията за по-висока лихва от Фед"),
    ("Gold Falls as Stronger Dollar and Fed Rate Hike Expectations Weigh on Prices", None,
     "Златото поевтинява на фона на очакванията за по-висока лихва от Фед и движението на долара"),
    ("US 30-year Treasury yield hits highest since 2002", None,
     "Доходността на американските облигации е на най-високото си ниво от години"),
    ("Silver Rebounds as Markets Await Fed Signals", None,
     "Среброто се връща нагоре на фона на очакванията за лихвата на Фед"),
    ("Gold Holds $4,123 as October Fed Hike Odds Top 70%, $4,185 Bounce in Focus", None,
     "Златото и очакванията за по-висока лихва от Фед"),
    # от проверката на 220 случайни заглавия от историята (29.09) — да не се върнат
    ("Will the Fed Raise Interest Rates? No, Says One Expert", None, "Очакванията за лихвата на Фед"),
    ("Oil prices rebound after Trump rejects peace deal to resolve Iran conflict", None,
     "Петролът се връща нагоре на фона на напрежението в Близкия изток"),
    ("Stocks Rally, Shaking Off Fed's Rate Hike", None, "Акциите се качват на фона на вдигането на лихвата от Фед"),
    ("The Dollar-Gold Standard's Lingering Demise", None, None),
    ("Huntington Bancshares (HBAN) Cuts Guidance Following Fed Rate Hike, But Is It A Bargain", None,
     "След решението на Фед за лихвата"),
    ("Bearish On Gold Ahead Of FOMC", None, "Златото преди решението на Фед за лихвата"),
    # от второто четене (230 заглавия, 29.09)
    ("SC Sees Two More Fed Hikes Before Mid-2027, Stays Overweight On Equities", None, "Очаквания за по-висока лихва от Фед"),
    ("Gold rises on easing dollar, oil as Fed rate verdict looms", None,
     "Златото поскъпва на фона на цената на петрола, преди решението на Фед за лихвата"),
    ("Fed rate hike fails to calm troubled markets as Dow falls 600 points. Expect more sharp swings in stocks and bonds.", None,
     "За вдигане на лихвата от Фед"),
    ("Gold's Safe-Haven Premium Is Now Trading on Xi's Iran De-Escalation Push", None,
     "Златото и усилията за мир в Близкия изток"),
    ("What this Kansas City Fed meeting means for the economy and inflation | Opinion", None, None),
    ("Bond Yields Are Pressuring Gold, But Miners May Tell a Different Story", None, None),
    ("Federal Reserve hikes key rate for 1st time in 3 years, defying Trump demands for a cut", None, "Фед вдигна лихвата"),
    ("Ahead of Fed meeting, Trump says US should have world's lowest interest rate", None, "Тръмп и решението на Фед за лихвата"),
    ("Gold Falls to $4,292 as Fed Hike Odds Hit 89%. Is the Correction Just Getting Started?", None,
     "Златото поевтинява на фона на очакванията за по-висока лихва от Фед"),
    # от третото четене (200 заглавия без Фед, 29.09)
    ("US rate rise jolts yen ahead of Bank of Japan meeting", None, None),
    ("Fool's gold: How geopolitical risk is taking some of the shine off the US dollar", None, None),
    ("Gold rebound stalls as Treasury yields return toward multi-year highs", None, "Златото и доходността на облигациите"),
    ("US equities eclipse Treasuries in rare foreign capital shift", None, None),
    ("Investors pour $18 billion into gold ETFs in August as sovereign debt concerns grow - WGC report", None,
     "Пари влизат в борсовите фондове за златото (ETF)"),
    ("Mortgage Rates Hit Two-Year High as Federal Reserve Action Rattles Housing Market", None,
     "Ипотечните лихви са на най-високите си нива от години"),
    ("Gold and Silver Are Trading the Inflation the Oil Chart Is Missing", None, None),
    ("Gold, silver squeezed by yields as dollar threat lies dormant", None, "Златото, среброто и доходността на облигациите"),
    ("Trump adviser blasts Fed rate increase, questions Warsh", None, "За вдигане на лихвата от Фед"),
    ("A Fed Member Supported The Latest Rate Hike. She Says Chances Of Elevated Inflation Are 'Notably Higher'", None,
     "Изказване на член на Фед за вдигане на лихвата и инфлацията"),
    ("Strive CEO: Bitcoin Could 'Go to Infinity' as Dollar Debt Crisis Breaks", None, None),
    ("Copper futures rally despite Fed rate hike as traders await tariff news.", None,
     "Медта поскъпва на фона на решенията на Фед за лихвата, преди новините за митата"),
    ("Gold at a Crossroads: Can XAU/USD Hold Above $4,300 After the Latest Rally?", None, None),
    # от живото пускане на новия събирач (29.09, 21:25)
    ("Fed's Barr Says More Hikes Likely Needed as Growth Picks Up", None,
     "Изказване на член на Фед (Barr) за вдигане на лихвата"),
    ("Fed's Williams Hints Next Rate Increase Can Wait", None, "Изказване на член на Фед (Williams) за вдигане на лихвата"),
    ("US Dollar Rises Early Tuesday Ahead of Packed Data, Fed Speaker Schedule", None,
     "Доларът поскъпва преди изказванията на членове на Фед"),
    # от втората проверка (80 нови заглавия от историята + прегледа по групи, 29.09 вечер) — да не се върнат
    ("Oil up, Wall Street dips after Trump rejects Iran truce offer", None,
     "Петролът поскъпва на фона на напрежението в Близкия изток"),
    ("Oil takes off again, Wall Street dips after Trump rejects Iran truce offer", None,
     "Петролът и напрежението в Близкия изток"),
    ("Oil jumps after Iran ceasefire collapses", None, "Петролът поскъпва на фона на напрежението в Близкия изток"),
    ("Gold jumps as Iran rejects ceasefire proposal", None, "Златото поскъпва на фона на напрежението в Близкия изток"),
    ("Oil falls after Iran truce talks break down", None, "Петролът поевтинява на фона на напрежението в Близкия изток"),
    ("Gold rises as Russia rejects Ukraine peace plan", None, "Златото поскъпва на фона на войната в Украйна"),
    ("Oil falls as Israel-Iran ceasefire holds", None, "Петролът поевтинява на фона на примирието в Близкия изток"),
    ("Gold falls on Iran ceasefire hopes", None, "Златото поевтинява на фона на надеждите за мир в Близкия изток"),
    ("Oil falls as Middle East tensions ease", None, "Петролът поевтинява"),
    ("Gold Price Recovers To $4,450 On Trump's Iran Attack Pause", None, "Златото се връща нагоре"),
    ("Gold consolidates as Iran diplomacy hopes clash with hawkish Fed expectations", None,
     "Златото е без голяма промяна на фона на очакванията за по-висока лихва от Фед и дипломатическите усилия в Близкия изток"),
    ("Oil hits $108 as Gulf states postpone talks with Iran over Hormuz", None, "Петролът и напрежението в Близкия изток"),
    ("Gold drops to three-day low, eyes $4,300 as hawkish Fed and Iran risks underpin USD", None,
     "Златото е на най-ниското си ниво от дни на фона на очакванията за по-висока лихва от Фед и напрежението в Близкия изток"),
    ("Gold firms on softer dollar, inflation data and Mideast risks in focus", None,
     "Златото поскъпва на фона на данните за инфлацията и напрежението в Близкия изток"),
    ("Bitcoin Price Wobbles Before Settling After Fed Raises Rates", None, "Биткойн и решението на Фед за лихвата"),
    ("UBS Expects Two Fed Rate Hikes by End of 2026 After Warsh Speech and Jobs Data", None,
     "Очаквания за по-висока лихва от Фед"),
    ("Trump lashes out at Fed after Warsh backs rate hike", None, "Тръмп и лихвата на Фед"),
    ("Bitcoin Falls to $75,500 as Warsh Backs Fed Independence", None, "Биткойн поевтинява"),
    ("Gold slips as Fed officials signal rate hikes", None, "Златото поевтинява на фона на изказванията на членове на Фед"),
    ("More rate adjustments are likely needed to lower inflation, Fed Governor Barr says", None,
     "Изказване на член на Фед (Barr) за инфлацията"),
    ("In CT visit, Boston Fed President Collins backs rate hike, sees possible further increase", None,
     "Изказване на член на Фед (Collins) за вдигане на лихвата"),
    ("The Fed Hasn't Cut Rates Once This Year. Car Loans Got Cheaper Anyway.", None, "За лихвата на Фед"),
    ("Fed unlikely to hike rates this week despite 87% market odds", None, "Очакванията за лихвата на Фед"),
    ("Zheshang Securities: The implementation of the Federal Reserve's rate hike has improved liquidity expectations; "
     "the firm is also bullish on gold allocation opportunities.", None, "Златото и вдигането на лихвата от Фед"),
    ("Interest Rates and Gold: Why the Fed Didn't Move the Price", None, "Златото и лихвата на Фед"),
    ("U.S. Treasury Yields Fall as Fed Regains Trust, BOE Leaves Rates Unchanged", None,
     "Доходността на американските облигации спада"),
    ("AI Safety Fears Collide with Fed Rate Hikes, Roiling Markets", None, "За вдигане на лихвата от Фед"),
    ("Federal Reserve hawkish hike sent Gold price lower", None, "За вдигането на лихвата от Фед"),
    ("Economists See Fed Defying Expectations for Rate Hikes", None, "Очакванията за лихвата на Фед"),
    ("Fed should defy Donald Trump with rate rise, top economists say", None, "За вдигане на лихвата от Фед"),
    ("Goldman flips on Fed rate hike, then backtracks on forecast", None, "Очакванията за лихвата на Фед"),
    ("Fed's rate hike likely means more expensive credit cards, mortgages", None, "За вдигането на лихвата от Фед"),
    ("Singapore Dollar Consolidates; Fed Rate-Hike Prospects Could Weigh", None, "Очаквания за по-висока лихва от Фед"),
    ("Bond yields surge above 5% as Wall Street fears more Fed rate hikes", None,
     "Доходността на облигациите расте на фона на очакванията за по-висока лихва от Фед"),
    ("Warsh's Hawkish Background And The Federal Reserve's Policy Orientation - Analysis", None, "За лихвата на Фед"),
    ("What makes the Federal Reserve decide to raise or lower interest rates?", None, "За лихвата на Фед"),
    ("UK payrolls drop for fifth month as hiring slows", None, "Данни за работните места във Великобритания"),
    ("Week Ahead: US Payrolls Test Rate Path After Fed and ECB Hikes", None, "Данни за работните места (NFP)"),
    # от пробите 30.09 (40 от живия файл + нови 40 от историята) — да не се върнат
    ("Oil-Driven Fed Bets Sink Gold Nearly 4%, Opening a Selective Rebound Case", None,
     "Златото и очакванията за лихвата на Фед"),
    ("Gold Futures Streaming Chart", None, None),
    ("Experts Predict No Fed Rate Cut Next Week: What It Means", None, "Очакванията за лихвата на Фед"),
    ("COMMENTARY: Where will Fed tightening hit hardest in Asia?", None, "За лихвата на Фед"),
    ("Citi Trims Gold Positions Amid Tighter Fed Policy View", None, "Златото и очакванията за по-висока лихва от Фед"),
    ("Gold gains as US Dollar and yields pause, but weekly loss remains in sight", None, "Златото поскъпва"),
    ("MARKETS LIVE: Wall Street dips as oil steadies", None, "Американските акции падат"),
    ("Federal Reserve Inflation Outlook Signals a Critical Warning for Investors", None, None),
    ("Japan's interest rate hiked to 31-year high at 1.25% as inflation rises", None, "Японската централна банка вдигна лихвата"),
    ("Gold rebounds as traders position for Fed interest rate decision", None,
     "Златото се връща нагоре преди решението на Фед за лихвата"),
    ("Treasury Curve Narrows: Fed Hike Risks Growth", None, "За вдигане на лихвата от Фед"),
    ("Gold comes under pressure ahead of US PPI as Fed rate hike risks linger", None,
     "Златото е под натиск на фона на очакванията за по-висока лихва от Фед, преди данните за цените на производител в САЩ (PPI)"),
    ("Corporate finance chiefs lift inflation outlook, cite rates as concern - Fed survey", None, None),
    ("Fed Rate Cut Delayed as Strong Jobs Data Tests Bitcoin", None, "За лихвата на Фед"),
    ("Central Banks Are Hiking Again, Yet Gold Keeps Climbing", None, None),
    ("Gold, silver rebound as soft data cools October Fed hike bets - Kitco PM Report", None,
     "Златото и среброто се връщат нагоре на фона на очакванията за лихвата на Фед"),
    ("Odds of October Rate Increase Drop as Fed's Williams Signals He's Open to a Pause", None, "Очакванията за лихвата на Фед"),
    ("Bitcoin Breakout Cools as Fed Rate-Hike Bets Climb", None, "Биткойн и очакванията за по-висока лихва от Фед"),
    ("Fed rate hike odds tumble to coin flip after Williams says no rush", None, "Очакванията за лихвата на Фед"),
    ("Stocks edge higher ahead of US Fed rate call", None, "Акциите леко се качват преди решението на Фед за лихвата"),
    ("Bond Yields Keep Rising Despite Drop in Oil Price, Dovish Fed Speech", None,
     "Доходността на облигациите, изказванията на членове на Фед и цената на петрола"),
    ("Gold rises as oil slide eases Fed hike fears, Iran talks stay in focus", None,
     "Златото поскъпва на фона на очакванията за лихвата на Фед и цената на петрола"),
    ("Gold slips as oil rally fans rate hike bets ahead of Fed meeting", None,
     "Златото поевтинява на фона на очакванията за по-висока лихва от Фед и цената на петрола"),
    ("Musalem Warns Excessive Cut in Fed Communications Could Raise Rates and Inflation", None,
     "Изказване на член на Фед (Musalem) за инфлацията"),
    ("Socgen remains bullish on gold price in Q4 as central banks won't get ahead of inflation", None, None),
    ("Philippines Gold Prices Dip as Peso Conversion, Central Bank Demand and Dollar Moves Shape Outlook", None,
     "Златото и покупките на злато от централните банки"),
    # централни банки, фондове, банки
    ("Goldman Sachs maintains its end-2027 forecast for gold at USD 5,400/oz", None, "Goldman Sachs запазва прогнозата си за златото"),
    ("Central banks bought 20 tonnes of gold in August, WGC says", None, "Централни банки купуват злато"),
    ("Wells Fargo lowers gold price target amid rate concerns", None, "Wells Fargo сваля прогнозата си за златото"),
    ("Gold ETFs see third week of outflows", None, "Пари излизат от борсовите фондове за златото (ETF)"),
    ("Australia raises interest rates to 15-year high", None, "Австралийската централна банка вдигна лихвата"),
    # страници и анализи
    ("Current price of gold as of September 29, 2026", None, "Цената на златото днес"),
    ("Gold Price Forecast: Falling Rates Support Key Trend-Line Bounce", None, "Анализ и прогноза за златото"),
    ("Kobo Resources Intersects Strong Gold Mineralisation at the Road Cut Zone with 19.0 m at 1.94 g/t Au", None,
     "Минна компания съобщава резултати от сондажи за злато"),
    # това правилата НЕ пипат
    ("Could SpaceX be worth $12 trillion one day? Citi says Starship gets it a step closer.", None, None),
    ("How gold surpassed cocaine as Peru's most profitable criminal industry", None, None),
    ("Here's what Netflix skeptics are getting wrong about the stock, according to an analyst", None, None),
)
PRIMERI_EZIK = (
    ("Gold Prices Fall to 680,000 Won per Hondon", "조선일보", False),
    ("UBS Group: Historically, the Federal Reserve has never raised interest rates in October", "富途牛牛", False),
    ("El oro cae por la subida de los rendimientos", "Expansión", False),
    ("Золото дешевеет после решения ФРС", "РБК", False),
    ("Златото поевтинява след решението на Фед", "Капитал", True),
    ("Capella Receives Drill Permits for Hessjøgruva Copper Project, Central Norway", "Yahoo Finance", True),
    ("Gold near seven-week low as Fed rate-hike fears mount", "qz.com", True),
    ("Fed Official Says Policymakers Should Not Rush Another Rate Hike", "Межа. Новини України.", False),
    ("Gold price today", "Капитал", True),
)
# думите, които нямат място пред клиента (законът за кухнята) + «ще»
ZABRANENI = _r(r"(?<![\wа-я])(?:бот\w*|мозък\w*|мерен\w*|измерен\w*|наблюдени\w*|проверк\w*|пазач\w*|спирачк\w*|гейт\w*|"
               r"сянка|праг\w*|лост\w*|ръб\w*|шум\w*|присъд\w*|кандидат\w*|доказан\w*|опроверган\w*|ще)(?![\wа-я])")


def proveri(pyt=None):
    """Самопроверка · връща (грешки, редове за печат)."""
    greshki, izhod = [], []
    for zag, em, ochakvano in PRIMERI:
        real = bg_red(zag, em)
        if real != ochakvano:
            greshki.append("ПРИМЕР: %r → %r (очаквано %r)" % (zag, real, ochakvano))
    for zag, iz, ochakvano in PRIMERI_EZIK:
        if ezik_ok(zag, iz) != ochakvano:
            greshki.append("ЕЗИК: %r / %r → %r" % (zag, iz, not ochakvano))
    izhod.append("примери: %d · езикови: %d" % (len(PRIMERI), len(PRIMERI_EZIK)))
    if pyt:
        import json
        with open(pyt, "r", encoding="utf-8") as f:
            d = json.load(f)
        vse = d.get("novini") or []
        n = [x for x in vse if ezik_ok(x.get("zaglavie"), x.get("izvor"))]   # каквото ситото пуска
        izhod.append("езиковото сито: %d от %d остават" % (len(n), len(vse)))
        fed_danni = [x for x in n if (x.get("emisiya") in FED_EMISII) or _FED_ILI_DANNI.search(_norm(x.get("zaglavie")))]
        s_red = [x for x in n if bg_red(x.get("zaglavie"), x.get("emisiya"), x.get("izvor"))]
        fd_red = [x for x in fed_danni if bg_red(x.get("zaglavie"), x.get("emisiya"), x.get("izvor"))]
        izhod.append("файл: %d новини · с български ред: %d · Фед и данни: %d, от тях с ред: %d (%.1f%%)" % (
            len(n), len(s_red), len(fed_danni), len(fd_red), 100.0 * len(fd_red) / max(1, len(fed_danni))))
        for x in n:
            r = bg_red(x.get("zaglavie"), x.get("emisiya"), x.get("izvor"))
            if r and ZABRANENI.search(r):
                greshki.append("ЗАБРАНЕНА ДУМА: %r → %r" % (x.get("zaglavie"), r))
            if r and re.search(r"\d", re.sub(r"\((?:[A-Z]{2,5}|БВП)\)", "", r)):
                greshki.append("ЧИСЛО В РЕДА: %r → %r" % (x.get("zaglavie"), r))
    for zag, em, ochakvano in PRIMERI:
        if ochakvano and (ZABRANENI.search(ochakvano) or re.search(r"\d", re.sub(r"\((?:[A-Z]{2,5}|БВП)\)", "", ochakvano))):
            greshki.append("ПРИМЕРЪТ НАРУШАВА ЗАКОНА: %r" % ochakvano)
    return greshki, izhod


# «Фед и данни» за мярката на покритието · независимо от правилата горе
_FED_ILI_DANNI = _r(r"\bFed\b|\bFederal Reserve\b|\bFOMC\b|\bPowell\b|\bWarsh\b|\bCPI\b|\bPCE\b|\bPPI\b|\bpayrolls?\b|\bNFP\b|"
                    r"\bjobs report\b|\bjobless claims\b|\bJOLTS\b|\bjob openings\b|\bGDP\b|\bretail sales\b|\bPMI\b|\bISM\b|"
                    r"\bconsumer (?:confidence|sentiment)\b|\binflation (?:data|report)\b|\breport on inflation\b")


if __name__ == "__main__":
    if "--proveri" in sys.argv:
        ostatak = [a for a in sys.argv[1:] if a != "--proveri"]
        g, iz = proveri(ostatak[0] if ostatak else None)
        for red in iz:
            print(red)
        for red in g:
            print("✗", red)
        print("ПРОВЕРКАТА:", "ЗЕЛЕНО" if not g else "ЧЕРВЕНО · %d" % len(g))
        sys.exit(0 if not g else 1)
    for a in sys.argv[1:]:
        print(a, "→", bg_red(a))
