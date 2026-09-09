# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════
 AERO · ДРИП НА НОВИНИТЕ · за самия бот, не за платформата
───────────────────────────────────────────────────────────────────────────
 ЗАЩО ИЗОБЩО ГО ИМА
 Платформата (браузър) НЕ МОЖЕ да тегли тези емисии сама — браузърът ги
 спира заради правилото за чужд адрес и всяка заявка се проваля още преди
 да тръгне. Проверено на живо: Yahoo, Google News, Fed, Investing — всички
 падат в браузъра. Затова тегли ботът (Python няма такова ограничение) и
 записва ЕДИН файл: <out_dir>/novini.json. Платформата само го чете.

 КАКВО ПРАВИ
   · тегли 11 емисии ПАРАЛЕЛНО, всяка с таймаут 12 секунди
   · един паднал източник не вали останалите — падналите се изброяват
   · разчита RSS/Atom само със стандартната библиотека (xml.etree, а при
     счупен XML — резервно четене с регулярни изрази)
   · маха дублираните заглавия (и вътре в тегленето, и спрямо стария файл)
   · дава `vazhnost` 1-3, `za` (злато / долар / лихви / общо) и `zashto`
     (изречение на български) по ключови думи
   · пази последните 200, най-новите отгоре
   · пише АТОМАРНО (временен файл + преименуване) — половин файл няма как
     да се появи, дори токът да спре
   · ако ВСИЧКИ източници паднат, старият файл НЕ се пипа

 🔴🔴 09.09.2026 · ИМЕНАТА НА ПОЛЕТАТА БЯХА ДРУГИ И ПАНЕЛЪТ ГИ НЕ ВИЖДАШЕ.
 Този файл пишеше `utc` и `iztochnik`. Панелът (assets/novini_zhivi.js,
 функция `razcheti`) чете `x.chas` и `x.izvor`. Пуснах събирача истински и
 прочетох резултата ТОЧНО както го чете панелът:
     200 заглавия · 0 от 200 с източник на екрана · 200 от 200 «без час»
     обобщението щеше да казва «Нищо ново в последните 3 часа»
 при положение, че единайсет живи емисии току-що бяха дали пресни новини.
 Тоест панелът щеше да работи, да не гърми и да лъже — най-лошият вид
 счупено. Затова полетата тук вече се казват КАКТО ГИ ТЪРСИ ПАНЕЛЪТ.
 Панелът НЕ е пипан — той е чужд файл и е прав.
 Проверих и че никой друг не чете старите имена: в кода на бота няма
 нищо, което да отваря novini.json.

 ФОРМАТЪТ НА ФАЙЛА (това чете платформата · имената НЕ са по избор)
 {
   "kogato": "2026-09-09T18:12:44Z",       # кога е теглено · панелът го чете
   "broi": 200,
   "iztochnici_ok": ["Yahoo злато", ...],
   "iztochnici_padnali": [{"ime": "...", "greshka": "..."}],
   "belezhki": [...],                       # каквото подадеш в notes
   "novini": [
     {
       "zaglavie": "...",                   # ЧЕТЕ СЕ от панела
       "vryzka": "https://...",             # ЧЕТЕ СЕ · само http/https минава
       "izvor": "Reuters",                  # ЧЕТЕ СЕ · изданието, не емисията
       "chas": "2026-09-09T17:41:00Z",      # ЧЕТЕ СЕ · може да е null
       "vazhnost": 3,                       # ЧЕТЕ СЕ · 1-3
       "za": "лихви",                       # ЧЕТЕ СЕ · това е филтърът
       "emisiya": "Google Fed",             # коя емисия го донесе (за мен)
       "chas_ot_iztochnika": true,          # false = емисията не даде час
       "duma": "fed",                       # ДОКАЗАТЕЛСТВОТО за важността
       "zashto": "Fed решава каква да е..." # защо това мести златото
     }, ...
   ]
 }
 Панелът чете само първите шест. Останалите не му пречат — той си взима
 по име това, което му трябва, и подминава всичко друго. Държа ги, защото
 «важност 3» без думата, която я е вдигнала, е число на доверие.

 ЧЕСТНОТО
 `chas` може да е null — има емисии без час на новината. Тогава
 `chas_ot_iztochnika` е false и мястото в списъка е по реда на теглене,
 не по истински час. Не си измислям час, за да изглежда наред.
 `zashto` е null, когато нито една ключова дума не е излязла. Не съчинявам
 причина, за да е пълна колонката.

 ПЪТ НАЗАД: скриптът пише САМО novini.json в подадената папка. Връщане =
 изтриване на файла или възстановяване на novini.json.bak (пази се копие
 на предишния при всяко успешно писане).
═══════════════════════════════════════════════════════════════════════════
"""

import concurrent.futures
import gzip
import html
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen

# ── източниците ───────────────────────────────────────────────────────────
# Тук нарочно НЯМА ECB, BLS, Treasury, Kitco, Reuters, FRED, Finnhub — те
# падат или искат ключ.
# `za_ako_nyama` е темата по подразбиране: когато заглавието само по себе си
# не издава за какво е, източникът я издава (емисия на Fed = лихви).
#
# 🟢 МЕРЕНО 09.09.2026, всеки адрес поотделно · ЖИВИ СА ВСИЧКИ 11, нито един
# за изхвърляне. Отговор, брой единици вътре, размер:
#     Yahoo злато    200 ·  18 ·  17 КБ        CNBC           200 ·  30 ·  20 КБ
#     Yahoo долар    200 ·  15 ·  10 КБ        FT пазари      200 ·  25 ·  12 КБ
#     Fed всички     200 ·  20 ·  14 КБ        Google злато   200 · 100 · 141 КБ
#     Fed политика   200 ·  15 ·  10 КБ        Google Fed     200 · 100 · 133 КБ
#     MarketWatch    200 ·  10 ·   8 КБ
#     Investing      200 ·  10 ·   3 КБ
#     Mining.com     200 ·  36 · 275 КБ
# Най-бавният се събра за 0.97с. Ако някой почне да пада редовно, махни го
# ОТ ТУК и допиши датата — списъкът да не остарява мълчаливо.
#
# `ime` е за МОЕТО броене (кой е паднал, кой колко даде). `ekran` е това, което
# вижда клиентът. Разделени са, защото «Fed всички» и «Yahoo злато» са имена на
# емисии, а не на издания — на екрана до заглавието те четат като бъркотия.
IZTOCHNICI = (
    {"ime": "Yahoo злато",   "ekran": "Yahoo Finance",   "za_ako_nyama": "злато",
     "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F&region=US&lang=en-US"},
    {"ime": "Yahoo долар",   "ekran": "Yahoo Finance",   "za_ako_nyama": "долар",
     "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=DX-Y.NYB&region=US&lang=en-US"},
    {"ime": "Fed всички",    "ekran": "Fed",             "za_ako_nyama": "лихви",
     "url": "https://www.federalreserve.gov/feeds/press_all.xml"},
    {"ime": "Fed политика",  "ekran": "Fed",             "za_ako_nyama": "лихви",
     "url": "https://www.federalreserve.gov/feeds/press_monetary.xml"},
    {"ime": "MarketWatch",   "ekran": "MarketWatch",     "za_ako_nyama": "общо",
     "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},
    {"ime": "Investing",     "ekran": "Investing.com",   "za_ako_nyama": "общо",
     "url": "https://www.investing.com/rss/commodities.rss"},
    {"ime": "Mining.com",    "ekran": "Mining.com",      "za_ako_nyama": "злато",
     "url": "https://www.mining.com/feed/"},
    {"ime": "CNBC",          "ekran": "CNBC",            "za_ako_nyama": "общо",
     "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"},
    {"ime": "FT пазари",     "ekran": "Financial Times", "za_ako_nyama": "общо",
     "url": "https://www.ft.com/markets?format=rss"},
    # Двете отдолу са ТЪРСЕНИЯ, не издания — истинското издание идва в самата
    # емисия и се взима оттам. `ekran` тук е само резервата, ако някой ден
    # спрат да го дават.
    {"ime": "Google злато",  "ekran": "Google Новини",   "za_ako_nyama": "злато",
     "url": "https://news.google.com/rss/search?q=gold+price+when:1d&hl=en-US&gl=US&ceid=US:en"},
    {"ime": "Google Fed",    "ekran": "Google Новини",   "za_ako_nyama": "лихви",
     "url": "https://news.google.com/rss/search?q=federal+reserve+rates+when:1d&hl=en-US&gl=US&ceid=US:en"},
)

TAJMAUT = 12          # секунди на източник — колкото е поръчано
OBSHT_TAJMAUT = 40    # цялото тегляне; паралелно е, значи 12с стигат, това е предпазител
# МЕРЕНО 09.09: единайсетте емисии дават 259 заглавия, 248 след махане на
# дублите, тоест 48 изпадат под чертата. От тях 26 са на Fed — техните
# съобщения са от преди дни и се подреждат най-отдолу. НЕ вдигам прага за
# това: панелът показва последните 12 по час, а съобщение на Fake отпреди
# седмица няма как да се появи там при никакъв праг. В деня на решението за
# лихвата то е най-НОВОТО и влиза начело. Пише се, за да не тръгне някой да
# «поправя» сметка, която не е сгрешена. Съобщение на Fed отпреди седмица
# няма как да се появи между последните 12 при НИКАКЪВ праг.
PAZI = 200            # колко новини се пазят във файла
MAX_OT_IZTOCHNIK = 40 # една емисия да не изяде целия файл (FT и MW дават по 30-40)

# Подпис на обикновен браузър. НЕ е маскировка на друг сайт — това е UA,
# без който FT и Investing връщат 403 на голото „Python-urllib".
PODPIS = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ── думите, които вдигат важността ────────────────────────────────────────
# Търси се ЦЯЛА дума (\b...\b), защото „rate" се крие в „corporate" и
# „moderate", а „war" — в „warning" и „forward". Без границите половината
# заглавия щяха да излязат тройка.
DUMI_3 = ("fed", "fomc", "rate", "rates", "inflation", "cpi", "pce", "nfp",
          "payroll", "payrolls", "powell", "war", "sanctions", "ceasefire",
          "tariff", "tariffs")
DUMI_2 = ("gold", "bullion", "dollar", "treasury", "treasuries", "yield",
          "yields", "recession", "shutdown", "unemployment", "safe haven")

# ── ЗАЩО тази новина мести златото ────────────────────────────────────────
# Едно изречение на човешки за всяка дума, която вдига важността. Пише се във
# файла до самата дума, за да може човек да види КАКВО е било сметнато за
# важно и ЗАЩО — вместо да вярва на една цветна точка.
# Няма ли дума — няма и изречение (null). Съчинена причина е по-лоша от
# празно място.
ZASHTO = {
    "fed":          "Fed решава каква да е лихвата в САЩ. По-евтини пари обикновено вдигат златото.",
    "fomc":         "Това е заседанието, на което се решава лихвата в САЩ — най-силният лост върху златото.",
    "powell":       "Думите на шефа на Fed местят очакванията за лихвата, а с тях и златото.",
    "rate":         "Лихвите са прекият съперник на златото: то не носи доход и поевтинява, когато другаде плащат повече.",
    "rates":        "Лихвите са прекият съперник на златото: то не носи доход и поевтинява, когато другаде плащат повече.",
    "inflation":    "Инфлацията е основната причина да се държи злато — то пази стойност, когато парите я губят.",
    "cpi":          "ЦПИ е измерването на инфлацията. Изненада в него мести златото в същия ден.",
    "pce":          "Това е измерването на инфлацията, което Fed гледа най-внимателно при решението за лихвата.",
    "nfp":          "Заетостта в САЩ решава дали Fed ще пипне лихвата — оттам стига до златото.",
    "payroll":      "Заетостта в САЩ решава дали Fed ще пипне лихвата — оттам стига до златото.",
    "payrolls":     "Заетостта в САЩ решава дали Fed ще пипне лихвата — оттам стига до златото.",
    "unemployment": "Слаб пазар на труда бута лихвата надолу, а по-ниската лихва обикновено вдига златото.",
    "war":          "Война значи страх, а страхът гони парите към златото.",
    "ceasefire":    "Затихващо напрежение — страхът спада и златото често губи от това.",
    "sanctions":    "Санкциите разбъркват търговията и валутите; златото е убежището при такова.",
    "tariff":       "Митата вдигат цените и карат страните да търсят убежище — и двете стигат до златото.",
    "tariffs":      "Митата вдигат цените и карат страните да търсят убежище — и двете стигат до златото.",
    "gold":         "Пряко за златото.",
    "bullion":      "Пряко за физическото злато.",
    "dollar":       "Златото се мери в долари: по-силен долар обикновено значи по-евтино злато.",
    "treasury":     "Доходността на американския дълг е прякото сравнение за златото — качи ли се тя, златото обикновено пада.",
    "treasuries":   "Доходността на американския дълг е прякото сравнение за златото — качи ли се тя, златото обикновено пада.",
    "yield":        "Доходността другаде е цената, която златото плаща — то самò не плаща лихва.",
    "yields":       "Доходността другаде е цената, която златото плаща — то самò не плаща лихва.",
    "recession":    "Свиване на икономиката обикновено значи по-ниски лихви и повече търсене на убежище.",
    "shutdown":     "Спряло правителство на САЩ носи несигурност, а несигурността обикновено помага на златото.",
    "safe haven":   "Точно това е ролята на златото в такъв ден — убежище.",
}

DUMI_ZLATO = ("gold", "bullion", "xau", "gld", "precious metal", "precious metals",
              "silver", "comex")
DUMI_DOLAR = ("dollar", "greenback", "dxy", "euro", "yen", "forex", "currency",
              "currencies")
DUMI_LIHVI = ("fed", "fomc", "rate", "rates", "inflation", "cpi", "pce", "nfp",
              "payroll", "payrolls", "treasury", "treasuries", "yield", "yields",
              "powell", "monetary", "central bank", "hike", "cut", "cuts")


def _re_dumi(dumi):
    """Един израз за цял списък думи — по-бърз от списък от изрази и,
       по-важното, с граници, за да не лови думи вътре в други думи."""
    return re.compile(r"\b(" + "|".join(re.escape(d) for d in dumi) + r")\b",
                      re.IGNORECASE)


R3 = _re_dumi(DUMI_3)
R2 = _re_dumi(DUMI_2)
R_ZLATO = _re_dumi(DUMI_ZLATO)
R_DOLAR = _re_dumi(DUMI_DOLAR)
R_LIHVI = _re_dumi(DUMI_LIHVI)


# ══════════════════════════════════════════════════════════════════════════
#  дребните помощници
# ══════════════════════════════════════════════════════════════════════════

def _belezhka(notes, tekst):
    """`notes` може да е списък (добавям), функция (викам) или None (мълча).
       Прието е така, защото различните части на бота водят дневник различно
       и не искам да налагам една форма."""
    if notes is None:
        return
    try:
        if callable(notes):
            notes(tekst)
        elif isinstance(notes, list):
            notes.append(tekst)
    except Exception:
        pass  # дневникът НИКОГА не бива да вали тегленето


_RE_TAG = re.compile(r"<[^>]+>")
_RE_PROSTOR = re.compile(r"\s+")
_RE_UPRAVLYAVASHTI = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _chist_tekst(s):
    """Маха HTML етикетите и разгъва &amp; · емисиите бъкат и от двете."""
    if not s:
        return ""
    s = _RE_TAG.sub(" ", str(s))
    s = html.unescape(s)
    s = s.replace(" ", " ")
    return _RE_PROSTOR.sub(" ", s).strip()


# Опашката на Google News: „ - Reuters", „ - usatoday.com", „ - The Wall
# Street Journal". Реже се САМО ако наистина прилича на име на издание.
#
# 🔴 ПЪРВАТА ВЕРСИЯ РЕЖЕШЕ ВСЯКА ОПАШКА ДО 40 ЗНАКА И ТОВА Е ОПАСНО.
# „Jobs report is out - what to watch" и „Jobs report is out - the full
# text" стават ЕДНО заглавие и едната новина изчезва. По-добре един
# дубликат на екрана, отколкото изгубена новина.
# Затова опашката трябва да е име: всяка дума започва с главна буква,
# цифра или & (Reuters · The Wall Street Journal · CNBC · U.S. News),
# ИЛИ да е домейн (usatoday.com · fxstreet.com). „what to watch" не е
# нито едното. Плюс: главата отпред остава поне 25 знака.
_RE_ISTOCHNIK_OPASHKA = re.compile(r"(?<=.{25})\s+[-–—]\s+([^-–—]{2,40})$")
_RE_IZDANIE = re.compile(r"^[A-Z0-9&][\w.'’]*(?:\s+[A-Z0-9&][\w.'’]*){0,3}$")
_RE_DOMEYN = re.compile(r"^[\w-]+(?:\.[\w-]+)+$")


def _klyuch(zaglavie):
    """Ключът за дублиране. Google News лепи ' - Име на изданието' в края,
       затова една и съща новина идва два пъти с различна опашка. Опашката
       се маха САМО за сравнението — на екрана заглавието остава цяло."""
    t = zaglavie or ""
    m = _RE_ISTOCHNIK_OPASHKA.search(t)
    if m:
        opashka = m.group(1).strip()
        if _RE_IZDANIE.match(opashka) or _RE_DOMEYN.match(opashka):
            t = t[:m.start()]
    t = re.sub(r"[^0-9a-zA-Zа-яА-Я ]+", " ", t.lower())
    t = _RE_PROSTOR.sub(" ", t).strip()
    return t[:110]


def _utc_ot(tekst):
    """Час на новината → ISO в UTC, или None. НЕ подставям сегашния час,
       когато емисията не дава — измисленият час е измислено число."""
    if not tekst:
        return None
    tekst = tekst.strip()
    # 1 · RFC-822 (Mon, 08 Sep 2026 17:41:00 GMT) — това дава 9 от 11 емисии
    try:
        d = parsedate_to_datetime(tekst)
        if d is not None:
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass
    # 2 · ISO (2026-09-08T17:41:00+00:00 или ...Z) — Atom и Fed
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?"
                 r"\s*(Z|[+-]\d{2}:?\d{2})?", tekst)
    if m:
        try:
            g = m.groups()
            d = datetime(int(g[0]), int(g[1]), int(g[2]), int(g[3]), int(g[4]),
                         int(g[5] or 0), tzinfo=timezone.utc)
            zona = g[6]
            if zona and zona != "Z":
                zona = zona.replace(":", "")
                znak = 1 if zona[0] == "+" else -1
                otm = znak * (int(zona[1:3]) * 3600 + int(zona[3:5]) * 60)
                d = datetime.fromtimestamp(d.timestamp() - otm, tz=timezone.utc)
            return d.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return None
    return None


def _vazhnost(tekst):
    """Връща (важност, думата-доказателство). Думата се записва във файла,
       за да може човек да види ЗАЩО нещо е тройка, вместо да ми вярва."""
    m = R3.search(tekst)
    if m:
        return 3, m.group(1).lower()
    m = R2.search(tekst)
    if m:
        return 2, m.group(1).lower()
    return 1, None


def _za(tekst, po_podrazbirane):
    """Темата. Редът е нарочен: златото е инструментът на собственика, значи
       «Gold rises as Fed cuts» е ЗЛАТО, не лихви. После долар, после лихви."""
    if R_ZLATO.search(tekst):
        return "злато"
    if R_DOLAR.search(tekst):
        return "долар"
    if R_LIHVI.search(tekst):
        return "лихви"
    return po_podrazbirane or "общо"


# ══════════════════════════════════════════════════════════════════════════
#  тегленето
# ══════════════════════════════════════════════════════════════════════════

def _svali(url, tajmaut=TAJMAUT):
    """Сурово тегляне → текст. Хвърля при провал; ловенето е нагоре."""
    zayavka = Request(url, headers={
        "User-Agent": PODPIS,
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        # 🔴 БЕЗ 'br' · brotli не се разгъва от стандартната библиотека и
        # отговорът идва като боклук. Само gzip/deflate, които мога.
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urlopen(zayavka, timeout=tajmaut) as otg:
        surovo = otg.read()
        kodirane = (otg.headers.get("Content-Encoding") or "").lower()
        vid = otg.headers.get("Content-Type") or ""
    if "gzip" in kodirane or surovo[:2] == b"\x1f\x8b":
        try:
            surovo = gzip.GzipFile(fileobj=io.BytesIO(surovo)).read()
        except Exception:
            pass
    elif "deflate" in kodirane:
        try:
            import zlib
            surovo = zlib.decompress(surovo, -zlib.MAX_WBITS)
        except Exception:
            pass
    # знакът се взима от отговора, а ако го няма — от самия XML пролог
    znak = None
    m = re.search(r"charset=([\w-]+)", vid, re.IGNORECASE)
    if m:
        znak = m.group(1)
    if not znak:
        m = re.search(rb'encoding=["\']([\w-]+)["\']', surovo[:200])
        if m:
            znak = m.group(1).decode("ascii", "ignore")
    try:
        return surovo.decode(znak or "utf-8", "replace")
    except LookupError:
        return surovo.decode("utf-8", "replace")


def _lokalno(etiket):
    """<{http://www.w3.org/2005/Atom}entry> → 'entry'. Пространствата на
       имената са различни при всяка емисия и не носят нищо тук."""
    return etiket.rsplit("}", 1)[-1].lower()


def _razcheti_xml(surovo):
    """Основното четене · xml.etree. Връща списък от суровите петорки."""
    tekst = _RE_UPRAVLYAVASHTI.sub("", surovo).lstrip("﻿ \r\n\t")
    koren = ET.fromstring(tekst)
    izlaz = []
    for el in koren.iter():
        if _lokalno(el.tag) not in ("item", "entry"):
            continue
        zag = vryzka = opis = chas = izdanie = None
        for dete in list(el):
            ime = _lokalno(dete.tag)
            if ime == "title" and not zag:
                zag = "".join(dete.itertext())
            elif ime == "link" and not vryzka:
                # RSS държи адреса в текста, Atom — в атрибут href
                vryzka = (dete.text or "").strip() or dete.get("href") or None
            elif ime in ("description", "summary", "content") and not opis:
                opis = "".join(dete.itertext())
            elif ime in ("pubdate", "published", "updated", "date") and not chas:
                chas = (dete.text or "").strip()
            # 🔴 Google News слага истинското издание тук: <source>Reuters</source>.
            # Без него на екрана пишеше «Google злато», което не е издание и
            # не казва на клиента нищо. Мерено 09.09: и двете емисии на Google
            # дават <source> на ВСИЧКИТЕ 100 заглавия. Другите девет емисии
            # нямат такъв етикет и си остават с името на емисията.
            elif ime == "source" and not izdanie:
                izdanie = "".join(dete.itertext())
            elif ime == "guid" and not vryzka and (dete.text or "").startswith("http"):
                vryzka = dete.text.strip()
        if zag:
            izlaz.append((zag, vryzka, opis, chas, izdanie))
    return izlaz


# Резервното четене. Пуска се САМО когато XML-ът е счупен — случва се при
# емисии с неекранирано „&" в заглавие. По-добре пет новини с регулярен
# израз, отколкото нула заради една лоша амперсанда.
_RE_EDINICA = re.compile(r"<(item|entry)[\s>].*?</\1>", re.IGNORECASE | re.DOTALL)
_RE_ZAG = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_RE_VRYZKA = re.compile(r"<link[^>]*?href=[\"']([^\"']+)[\"']|<link[^>]*>(.*?)</link>",
                        re.IGNORECASE | re.DOTALL)
_RE_CHAS = re.compile(r"<(?:pubDate|published|updated|dc:date)[^>]*>(.*?)"
                      r"</(?:pubDate|published|updated|dc:date)>",
                      re.IGNORECASE | re.DOTALL)
_RE_CDATA = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)
_RE_IZDANIE_EL = re.compile(r"<source[^>]*>(.*?)</source>", re.IGNORECASE | re.DOTALL)


def _razcheti_regex(surovo):
    izlaz = []
    for m in _RE_EDINICA.finditer(surovo):
        parche = m.group(0)
        z = _RE_ZAG.search(parche)
        if not z:
            continue
        zag = _RE_CDATA.sub(r"\1", z.group(1))
        v = _RE_VRYZKA.search(parche)
        vryzka = None
        if v:
            vryzka = (v.group(1) or v.group(2) or "").strip()
        c = _RE_CHAS.search(parche)
        # и тук същият етикет · петорките на двете четения ТРЯБВА да съвпадат,
        # иначе резервното четене ще гърми точно в деня, в който е нужно
        i = _RE_IZDANIE_EL.search(parche)
        izlaz.append((zag, vryzka, None, c.group(1).strip() if c else None,
                      _RE_CDATA.sub(r"\1", i.group(1)) if i else None))
    return izlaz


def _edin_iztochnik(iz):
    """Тегли и разчита ЕДИН източник. Всяка грешка се връща като стойност,
       не се вдига — иначе един паднал сайт вали цялото тегляне."""
    zapochna = time.time()
    try:
        surovo = _svali(iz["url"])
    except Exception as e:
        return {"ime": iz["ime"], "ok": False,
                "greshka": type(e).__name__ + ": " + str(e)[:120],
                "sek": round(time.time() - zapochna, 2), "novini": []}

    nachin = "xml"
    try:
        surovi = _razcheti_xml(surovo)
    except Exception:
        nachin = "резервно"
        try:
            surovi = _razcheti_regex(surovo)
        except Exception as e:
            return {"ime": iz["ime"], "ok": False,
                    "greshka": "нечетим отговор: " + str(e)[:100],
                    "sek": round(time.time() - zapochna, 2), "novini": []}
    if not surovi:
        # 200, но празно · това Е провал: значи форматът се е сменил
        return {"ime": iz["ime"], "ok": False, "greshka": "празна емисия",
                "sek": round(time.time() - zapochna, 2), "novini": []}

    novini = []
    for zag, vryzka, opis, chas, izdanie in surovi[:MAX_OT_IZTOCHNIK]:
        zaglavie = _chist_tekst(zag)
        if not zaglavie or len(zaglavie) < 8:
            continue

        # 🔴 Опашката „ - Име на изданието" се реже САМО при ТОЧНО съвпадение с
        # това, което самата емисия е обявила за издание. Мерено 09.09 на живо:
        # 200 от 200 заглавия на двете емисии на Google завършват точно така.
        # Точното съвпадение е и защитата: „Jobs report - what to watch" няма
        # как да пострада, защото „what to watch" не е обявеното издание.
        # На екрана изданието и без това стои отделно вляво — оставено в
        # заглавието, то се повтаря два пъти на всеки ред.
        izdanie = _chist_tekst(izdanie)
        if izdanie and zaglavie.endswith(" - " + izdanie):
            glava = zaglavie[:-(len(izdanie) + 3)].strip()
            if len(glava) >= 25:          # да не остане чуканче вместо заглавие
                zaglavie = glava

        # Важността се съди по заглавие + описание, но описанието се реже:
        # цял абзац дава думата „rate" почти винаги и всичко става тройка.
        za_dumi = zaglavie + " " + _chist_tekst(opis)[:180]
        vazhnost, duma = _vazhnost(za_dumi)
        utc = _utc_ot(chas)
        novini.append({
            # 🔴 Имената `zaglavie · vryzka · izvor · chas · vazhnost · za` НЕ
            # са по мой избор — панелът ги търси буквално така. Смениш ли ги,
            # той не гърми, а показва «без час» и празен източник на всеки ред.
            "zaglavie": zaglavie[:220],
            "vryzka": (vryzka or "").strip()[:600] or None,
            "izvor": (izdanie or iz.get("ekran") or iz["ime"])[:60],
            "chas": utc,
            "vazhnost": vazhnost,
            "za": _za(za_dumi, iz.get("za_ako_nyama")),
            # оттук надолу панелът не чете нищо · това е за човека и за мен
            "emisiya": iz["ime"],
            "chas_ot_iztochnika": utc is not None,
            "duma": duma,
            "zashto": ZASHTO.get(duma),
        })
    return {"ime": iz["ime"], "ok": True, "greshka": None, "nachin": nachin,
            "sek": round(time.time() - zapochna, 2), "novini": novini}


# ══════════════════════════════════════════════════════════════════════════
#  писането
# ══════════════════════════════════════════════════════════════════════════

def _stari(pyt):
    """Старият файл. Липсва или е счупен → празно, БЕЗ да вдига.

    🔴 Тук се превеждат и записите от първия вид на файла (`utc`,
    `iztochnik`). Без този превод първото пускане след поправката слепва
    200 стари реда, които панелът ще покаже като «без час» и без източник —
    тоест поправката ще изглежда неуспяла цял ден, докато старите изпаднат.
    Три реда сега спестяват точно това. Махат се, щом старият вид отмре."""
    try:
        with open(pyt, "r", encoding="utf-8") as f:
            d = json.load(f)
        n = d.get("novini")
        if not isinstance(n, list):
            return []
        for z in n:
            if isinstance(z, dict):
                if "chas" not in z and "utc" in z:
                    z["chas"] = z.pop("utc")
                if "izvor" not in z and "iztochnik" in z:
                    z["izvor"] = z.get("iztochnik")
        return n
    except Exception:
        return []


def _pishi_atomarno(pyt, dannite):
    """Временен файл в СЪЩАТА папка (os.replace е атомарно само в един дял),
       после преименуване. Половин файл не може да се появи."""
    papka = os.path.dirname(os.path.abspath(pyt)) or "."
    os.makedirs(papka, exist_ok=True)
    if os.path.exists(pyt):
        try:
            shutil.copy2(pyt, pyt + ".bak")   # 🔴 пътят назад
        except Exception:
            pass
    vr = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=papka,
                                     prefix=".novini-", suffix=".tmp",
                                     delete=False, newline="\n")
    try:
        json.dump(dannite, vr, ensure_ascii=False, indent=1)
        vr.flush()
        os.fsync(vr.fileno())
        vr.close()
        os.replace(vr.name, pyt)
    except Exception:
        try:
            vr.close()
        except Exception:
            pass
        try:
            os.unlink(vr.name)
        except Exception:
            pass
        raise


def _red(n):
    """Ключ за подредбата. Новина без час от източника отива НАЙ-ОТДОЛУ в
       рамките на своя ред — не я вдигам, за да не изпревари истински час."""
    return (n.get("chas") or "0000")


def dryp_novini(out_dir, notes=None):
    """Тегли всички източници и записва <out_dir>/novini.json.

    Връща (брой_нови, източници_ок, източници_паднали), където
    `източници_ок` е списък с имена, а `източници_паднали` — списък от
    {"ime": ..., "greshka": ...}.

    При ПЪЛЕН провал (нито един източник) старият файл НЕ се пипа и
    връщането е (0, [], [...]).
    """
    zapochna = time.time()
    pyt = os.path.join(out_dir, "novini.json")
    rezultati = []

    izpylnitel = concurrent.futures.ThreadPoolExecutor(
        max_workers=min(len(IZTOCHNICI), 11))
    try:
        bydeshti = {izpylnitel.submit(_edin_iztochnik, iz): iz for iz in IZTOCHNICI}
        try:
            for b in concurrent.futures.as_completed(bydeshti, timeout=OBSHT_TAJMAUT):
                try:
                    rezultati.append(b.result())
                except Exception as e:
                    iz = bydeshti[b]
                    rezultati.append({"ime": iz["ime"], "ok": False,
                                      "greshka": str(e)[:120], "novini": []})
        except concurrent.futures.TimeoutError:
            # общият предпазител · каквото не е дошло, се брои за паднало
            for b, iz in bydeshti.items():
                if not b.done():
                    rezultati.append({"ime": iz["ime"], "ok": False,
                                      "greshka": "не се събра в "
                                                 + str(OBSHT_TAJMAUT) + " сек",
                                      "novini": []})
    finally:
        try:
            izpylnitel.shutdown(wait=False, cancel_futures=True)
        except TypeError:            # Python под 3.9 не знае cancel_futures
            izpylnitel.shutdown(wait=False)

    ok = [r["ime"] for r in rezultati if r.get("ok")]
    padnali = [{"ime": r["ime"], "greshka": r.get("greshka")}
               for r in rezultati if not r.get("ok")]

    for r in sorted(rezultati, key=lambda x: x["ime"]):
        _belezhka(notes, "новини · " + r["ime"] + " · "
                  + (str(len(r["novini"])) + " бр. за " + str(r.get("sek")) + "с"
                     if r.get("ok") else "ПАДНА: " + str(r.get("greshka"))))

    # 🔴 Нито един източник → не пипам стария файл. По-добре вчерашни новини,
    # отколкото празен екран, и по-добре празен екран, отколкото изтрити данни.
    if not ok:
        _belezhka(notes, "новини · ВСИЧКИ паднаха — старият файл е запазен")
        return 0, [], padnali

    svezhi = []
    for r in rezultati:
        svezhi.extend(r.get("novini") or [])
    svezhi.sort(key=_red, reverse=True)

    # ── дублирането ────────────────────────────────────────────────────
    # Първо прясното (то бие, защото носи по-новия час), после старото.
    # Един и същ надслов от три издания е ЕДНА новина.
    starite = _stari(pyt)                     # чете се ВЕДНЪЖ
    stari_klyuchove = set(_klyuch(x.get("zaglavie", "")) for x in starite)
    vidyani = set()
    spisyk = []
    for n in svezhi + starite:
        k = _klyuch(n.get("zaglavie", ""))
        if not k or k in vidyani:
            continue
        vidyani.add(k)
        spisyk.append(n)

    spisyk.sort(key=_red, reverse=True)
    spisyk = spisyk[:PAZI]
    # 🔴 „Нови" се брои СЛЕД рязането на 200. Мерено на първото пускане:
    # 244 непознати заглавия, но във файла влизат 200 — да върна 244 значи
    # да обещая 44 новини, които никой няма да види. Числото трябва да
    # описва файла, не намерението.
    novi = sum(1 for n in spisyk if _klyuch(n.get("zaglavie", "")) not in stari_klyuchove)

    dannite = {
        "kogato": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sekundi": round(time.time() - zapochna, 2),
        "broi": len(spisyk),
        "novi_tozi_pyt": novi,
        "iztochnici_ok": ok,
        "iztochnici_padnali": padnali,
        "belezhki": (notes if isinstance(notes, list) else []),
        "novini": spisyk,
    }
    _pishi_atomarno(pyt, dannite)
    _belezhka(notes, "новини · записани " + str(len(spisyk)) + " ("
              + str(novi) + " нови) в " + pyt)
    return novi, ok, padnali


# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Ползване:  python ЗА_БОТА_novini.py <папка> [--na-vseki <минути>]
    dovodi = [a for a in sys.argv[1:]]
    na_vseki = 0
    if "--na-vseki" in dovodi:
        i = dovodi.index("--na-vseki")
        try:
            na_vseki = int(dovodi[i + 1])
        except Exception:
            na_vseki = 0
        del dovodi[i:i + 2]
    papka = dovodi[0] if dovodi else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    pyt = os.path.join(papka, "novini.json")

    # 🔴 СПИРАЧКА ЗА ЧЕСТОТАТА. Ботът тръгва на всеки 5 минути през деня —
    # това е 288 пускания на ден по 11 емисии = над 3000 заявки към чужди
    # сайтове ДНЕВНО за всяка от тях. Yahoo вече е връщал 429 на бота
    # (записано в неговия работен файл). Новините не остаряват за 5 минути,
    # затова спирачката стои ТУК, а не в разписанието: който извика този
    # файл, си получава защитата наготово.
    # Изход 0, защото «още е рано» НЕ е провал — иначе всяко второ пускане
    # ще светва червено за нищо.
    #
    # 🔴🔴 ВЪЗРАСТТА СЕ ЧЕТЕ ОТ `kogato` ВЪТРЕ ВЪВ ФАЙЛА, НЕ ОТ ДАТАТА МУ.
    # Първо го написах по датата на файла и това щеше да го изключи ЗАВИНАГИ:
    # ботът работи в GitHub, а там всеки път се тегли ново копие на всичко —
    # тоест файлът е «създаден преди 0 минути" при ВСЯКО пускане, колкото и
    # стар да е записът вътре. Спирачка, която винаги спира, не е спирачка,
    # а изключвател. Часът вътре го е писал самият събирач и не лъже.
    if na_vseki > 0:
        try:
            with open(pyt, "r", encoding="utf-8") as f:
                kogato = json.load(f).get("kogato")
            posl = datetime.strptime(kogato, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc)
            vyzrast = (datetime.now(timezone.utc) - posl).total_seconds() / 60.0
        except Exception:
            vyzrast = None       # няма файл / нечетим / без час → тегли
        if vyzrast is not None and 0 <= vyzrast < na_vseki:
            print("новини · последното събиране е отпреди {:.0f} мин, а прагът "
                  "е {} — не пипам нищо".format(vyzrast, na_vseki))
            sys.exit(0)

    dnevnik = []
    novi, ok, padnali = dryp_novini(papka, notes=dnevnik)
    for red in dnevnik:
        print(red)
    print("─" * 62)
    print("нови:", novi, "· източници ок:", len(ok), "· паднали:", len(padnali))
    if padnali:
        for p in padnali:
            print("   ✗", p["ime"], "→", p["greshka"])
    if os.path.exists(pyt):
        with open(pyt, "r", encoding="utf-8") as f:
            d = json.load(f)
        print("във файла:", d["broi"], "новини ·",
              sum(1 for x in d["novini"] if x["vazhnost"] == 3), "важни(3) ·",
              sum(1 for x in d["novini"] if not x["chas_ot_iztochnika"]), "без час ·",
              sum(1 for x in d["novini"] if x.get("zashto")), "с обяснение")
        for x in d["novini"][:5]:
            print("  [{}] {} · {} · {}".format(x["vazhnost"], x["za"],
                                               x["izvor"], x["zaglavie"][:70]))
    # 🔴 Изходът е 0/1, а НЕ True/False: bool е int в Python и sys.exit(True)
    # излиза с код 1, тоест «успях» се чете като провал.
    sys.exit(0 if ok else 1)
