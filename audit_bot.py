# -*- coding: utf-8 -*-
"""
🤖 ОДИТ-РОБОТ на AERO бота — преглежда ВСИЧКО и казва какво е счупено.

Пуска се:
  ЛОКАЛНО:  python audit_bot.py --repo <път-до-клонирано-repo>
  В GITHUB: сам, всеки ден (audit.yml) → праща отчета в Телеграм с --send

Какво прави: тегли живото състояние + свежи пазарни данни и проверява 5 групи:
  ⏱ ВРЕМЕ    — навреме ли идват данните (ПРИОРИТЕТ №1 на собственика)
  🎯 ТОЧНОСТ  — верни ли са числата, които ботът казва
  💀 МЪРТВИ   — заседнало, застояло, изгубено
  🔒 ЦЯЛОСТ   — живата версия, фийдовете, тестовете
  📊 ЧЕСТНОСТ — твърди ли ботът неща, които данните не подкрепят

Табло: «ВСИЧКО НАРЕД» = всички червени нули. Пускай ПРЕДИ и СЛЕД всяка промяна.
Не пипа нищо — само чете. Безопасен е.
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

AUDIT_VERSION = "1.0"
RED, YEL, GRN = "ЧЕРВЕНО", "ЖЪЛТО", "ЗЕЛЕНО"
SKP = "НЕПРОВЕРЕНО"     # има ли вход изобщо? без него зеленото е самохвалство
CATS = [("⏱", "ВРЕМЕ"), ("🎯", "ТОЧНОСТ"), ("💀", "МЪРТВИ"), ("🔒", "ЦЯЛОСТ"), ("📊", "ЧЕСТНОСТ")]


class Audit:
    def __init__(self):
        self.rows = []
        self.notes = []

    def add(self, cat, code, name, level, detail="", fix=""):
        self.rows.append({"cat": cat, "code": code, "name": name, "level": level,
                          "detail": detail, "fix": fix})
        icon = {RED: "❌", YEL: "⚠️", GRN: "✅", SKP: "⊘"}[level]
        line = f"  {icon} {code} · {name}"
        if detail:
            line += f" — {detail}"
        print(line)

    def ok(self, cat, code, name, detail=""):
        self.add(cat, code, name, GRN, detail)

    def warn(self, cat, code, name, detail="", fix=""):
        self.add(cat, code, name, YEL, detail, fix)

    def fail(self, cat, code, name, detail="", fix=""):
        self.add(cat, code, name, RED, detail, fix)

    def skip(self, cat, code, name, detail=""):
        self.add(cat, code, name, SKP, detail)

    def count(self, cat, level):
        return sum(1 for r in self.rows if r["cat"] == cat and r["level"] == level)

    @property
    def reds(self):
        return [r for r in self.rows if r["level"] == RED]

    @property
    def yellows(self):
        return [r for r in self.rows if r["level"] == YEL]


A = Audit()


# ─────────────────────────── помощни ───────────────────────────
def sofia(dt):
    from zoneinfo import ZoneInfo
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo("Europe/Sofia"))


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_trading_time(dt_utc):
    """Пазарът работи ли — по НЮ ЙОРК (DST), СЪЩИЯТ източник като бота (_market_closed):
    иначе одитът брои неделя вечер за «затворено» (реален отвор ~22-23 UTC) → фалшиво
    зелено при спрял Actions, и лятото петък 21-22 UTC не маркира дупка. НАХОДКА C."""
    _lb = globals().get("lb")
    if _lb is not None:
        try:
            return not _lb._market_closed(dt_utc.isoformat())
        except Exception:
            pass
    wd = dt_utc.weekday()                                  # резерва, ако lb още не е зареден
    if wd >= 5:
        return False
    if wd == 4 and dt_utc.hour >= 21:
        return False
    return True


def търговски_минути(a, b, стъпка=15):
    """ОДИТ-22: колко от интервала [a, b] е в ТЪРГОВСКО време.
    Дотук дупките се мереха в СТЕННИ минути и се броеха, ако само НАЧАЛОТО им е
    в търговско време. Затова всеки уикенд (петък вечер → неделя вечер) влизаше
    като «дупка от 2946 минути» и вдигаше ЧЕРВЕНО. Пазарът е бил затворен —
    това не е пропуснат будилник."""
    общо = (b - a).total_seconds() / 60
    if общо <= 0:
        return 0.0
    if общо > 60 * 24 * 14:                      # предпазител срещу безумно дълъг интервал
        return общо
    минути = 0.0
    t = a
    while t < b:
        нап = min(стъпка, (b - t).total_seconds() / 60)
        if is_trading_time(t):
            минути += нап
        t += timedelta(minutes=нап)
    return минути


def jload(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def jlines(p):
    out = []
    try:
        for ln in Path(p).read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    except Exception:
        pass
    return out


def jall(live: Path, name: str):
    """ОДИТ-9 (A2): ботът РОТИРА дневника месечно в live/archive/, а одитът четеше
    само текущия файл — тоест виждаше ~11% от историята и обявяваше «наред е» върху
    една десета от доказателствата. Сега чете архива + текущия, по ред."""
    rows = []
    stem = name.split(".")[0]
    try:
        for p in sorted((live / "archive").glob(stem + "-*.jsonl")):
            rows.extend(jlines(p))
    except Exception:
        pass
    rows.extend(jlines(live / name))
    return rows


def http(url, timeout=10, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


# ─────────────────── ⏱ ВРЕМЕ (приоритет №1) ───────────────────
def check_time(live: Path, code_dir: Path, bars):
    cat = "ВРЕМЕ"
    J = jall(live, "live_journal.jsonl")
    if not J:
        A.fail(cat, "В0", "журналът е празен/липсва", "няма какво да се одитира",
               "провери дали repo-то е клонирано и дали ботът пише в live/")
        return J
    last = J[-1]
    t_last = datetime.fromisoformat(last["run_utc"])
    age = (now_utc() - t_last).total_seconds() / 60

    # В1 · ПУЛС — жив ли е ботът СЕГА
    if not is_trading_time(now_utc()):
        A.ok(cat, "В1", "пулс", f"пазарът е затворен · последно пускане преди {age:.0f} мин")
    elif age <= 12:
        A.ok(cat, "В1", "пулс", f"последно пускане преди {age:.0f} мин")
    elif age <= 30:
        A.warn(cat, "В1", "пулс", f"тишина от {age:.0f} мин (очаквано ≤10)",
               "провери будилника и Actions")
    else:
        A.fail(cat, "В1", "пулс — БОТЪТ МЪЛЧИ", f"няма пускане от {age:.0f} мин!",
               "будилникът е спрял ИЛИ токенът е изтекъл ИЛИ Actions е червено")

    # В2 · КАДАНС — дупки в търговско време
    gaps = []
    for a, b in zip(J, J[1:]):
        ta, tb = datetime.fromisoformat(a["run_utc"]), datetime.fromisoformat(b["run_utc"])
        d = (tb - ta).total_seconds() / 60
        if d <= 20:
            continue
        # ОДИТ-22: мери ТЪРГОВСКИТЕ минути вътре, не стенните. Уикендът има нула
        # такива → не е дупка. Дотук се гледаше само дали НАЧАЛОТО е в търговско
        # време и петък вечер → неделя вечер влизаше като дупка от 2946 минути.
        тм = търговски_минути(ta, tb)
        if тм > 20:
            gaps.append((ta, тм))
    deltas = sorted((datetime.fromisoformat(b["run_utc"]) - datetime.fromisoformat(a["run_utc"])).total_seconds() / 60
                    for a, b in zip(J, J[1:]))
    med = deltas[len(deltas) // 2] if deltas else 0
    if not gaps:
        A.ok(cat, "В2", "каданс без дупки", f"медиана {med:.1f} мин между пусканията")
    else:
        worst = max(gaps, key=lambda g: g[1])
        lvl = A.fail if len(gaps) > 5 else A.warn
        lvl(cat, "В2", "дупки в кадънса",
            f"{len(gaps)} дупки >20 ТЪРГОВСКИ мин · най-голяма {worst[1]:.0f} мин на "
            f"{sofia(worst[0]):%d.%m %H:%M} (уикендите не се броят)",
            "будилникът пропуска — провери интервала му")

    # В3 · ВЪЗРАСТ НА БАРА (само v5 журнал)
    v5 = [r for r in J if "bar" in r and "spot" in r]
    if not v5:
        A.warn(cat, "В3", "възраст на бара — неизмерима",
               "журналът е от стара версия (няма поле bar/spot) → живата версия е предишна",
               "качи новия live_bot.py")
    else:
        A.ok(cat, "В3", "журналът е нов формат", f"{len(v5)} пускания с bar/spot")

    # В4 · ЗАКЪСНЕНИЕ УДАР → СЪОБЩЕНИЕ (сърцето на одита)
    #   Реконструира от журнала: кога е пратен изход vs кога РЕАЛНО е ударено нивото
    exits = [r for r in J if r.get("exits") and any("SENT" in s for s in r.get("status", []))]
    if not exits:
        A.ok(cat, "В4", "закъснение удар→съобщение", "няма изходи в журнала за мерене")
    elif bars is None:
        A.warn(cat, "В4", "закъснение удар→съобщение", "няма барове (мрежата?) — пропуснато")
    else:
        A.notes_delay = []
        A.ok(cat, "В4", "изходи за анализ", f"{len(exits)} пускания с пратени изходи (виж В5)")

    # В6 · ПЪРВАТА КАРТА НА ДЕНЯ
    by_day = {}
    for r in J:
        if any("signal=SENT" in s for s in r.get("status", [])):
            d = r["run_utc"][:10]
            by_day.setdefault(d, []).append(r["run_utc"])
    if by_day:
        firsts = [sofia(v[0]).strftime("%H:%M") for v in by_day.values()]
        A.ok(cat, "В6", "първа карта на деня", f"по дни: {', '.join(firsts[-5:])} София")

    # В7 · СПОТ-СВЕЖЕСТ И ОТКАЗИ (нови v5.3 полета)
    v53 = [r for r in J if "spot_rejected" in r]
    if v53:
        rej = sum(1 for r in v53 if r.get("spot_rejected"))
        spot_only = sum(1 for r in v53 if r.get("track_mode") == "spot-only")
        ages = [r["spot_age_sec"] for r in v53 if r.get("spot_age_sec")]
        rej_pct = 100 * rej / len(v53)
        detail = f"{len(v53)} v5.3 пускания · спот отрязан {rej_pct:.0f}% · spot-only {spot_only}"
        if ages:
            detail += f" · спот-възраст медиана {sorted(ages)[len(ages)//2]:.0f}сек"
        if rej_pct > 40 or spot_only > 3:
            A.fail(cat, "В7", "спот често недостъпен", detail, "санитито реже или 5м потокът липсва")
        else:
            A.ok(cat, "В7", "спот-свежест", detail)
    else:
        A.warn(cat, "В7", "спот-свежест — неизмерима", "журналът е стара версия (без spot_rejected)")
    return J


def check_delay_engine(live: Path, bars5, A_):
    """В5 · Точното закъснение: за всеки пратен ТП/СТОП реконструира кога РЕАЛНО е ударен."""
    import pandas as pd
    cat = "ВРЕМЕ"
    J = jall(live, "live_journal.jsonl")
    # възстановяваме сделките от git историята на състоянието
    trades = reconstruct_trades(live)
    if not trades or bars5 is None:
        A_.warn(cat, "В5", "точно закъснение удар→съобщение", "недостатъчно данни за реконструкция")
        return
    sent_exits = []
    for r in J:
        for s in r.get("status", []):
            # 🔧 О17 · ДОТУК ТОЗИ РЕГЕКС ХВАЩАШЕ САМО ЗЛАТНИТЕ ИЗХОДИ.
            # Сребърните тагове са `s-exit:...`, а `re.match` иска съвпадение от
            # НАЧАЛОТО на низа → нула сребърни изхода в целия одит. Тоест
            # закъснението на среброто не се е мерило НИТО ВЕДНЪЖ.
            m = re.match(r"(?:s-)?exit:(\w+)=SENT", s)
            if m:
                sent_exits.append((r["run_utc"], m.group(1)))
    if not sent_exits:
        A_.ok(cat, "В5", "точно закъснение", "няма пратени изходи за мерене")
        return
    delays = []
    for run_utc, kind in sent_exits:
        tr = None
        for t in trades:
            if t["opened"] <= run_utc and (t.get("closed") is None or t["closed"] >= run_utc):
                tr = t
        if tr is None or kind not in tr["levels"]:
            continue
        lvl = tr["levels"][kind]; d = tr["direction"]
        w = bars5[bars5.index > pd.Timestamp(tr["opened"])]
        w = w[w.index <= pd.Timestamp(run_utc) + pd.Timedelta(minutes=5)]
        if kind == "sl":
            m = w[w["High"] >= lvl] if d == "short" else w[w["Low"] <= lvl]
        else:
            m = w[w["Low"] <= lvl] if d == "short" else w[w["High"] >= lvl]
        if len(m) == 0:
            continue
        touch = m.index[0]
        delay = (pd.Timestamp(run_utc) - touch).total_seconds() / 60
        if 0 <= delay < 24 * 60:
            delays.append((delay, kind, str(touch), run_utc))
    if not delays:
        A_.warn(cat, "В5", "точно закъснение", "не можах да съпоставя изходи с барове")
        return
    vals = sorted(x[0] for x in delays)
    med = vals[len(vals) // 2]; mx = vals[-1]
    p90 = vals[int(len(vals) * 0.9)] if len(vals) > 3 else mx
    worst = max(delays, key=lambda x: x[0])
    txt = f"n={len(vals)} · медиана {med:.0f} мин · p90 {p90:.0f} · най-лошо {mx:.0f} мин"
    if med <= 7:
        A_.ok(cat, "В5", "закъснение удар→съобщение", txt + " (спот-засичането работи)")
    elif med <= 15:
        A_.warn(cat, "В5", "закъснение удар→съобщение", txt + " — типично за бар-засичане",
                "живата версия още не ползва спот-засичане (Ф7.1) → качи новия бот")
    else:
        A_.fail(cat, "В5", "ЗАКЪСНЕНИЕ ТВЪРДЕ ГОЛЯМО", txt +
                f" · най-лошото: {worst[1]} ударен {sofia(worst[2]):%d.%m %H:%M}, пратен {sofia(worst[3]):%H:%M}",
                "това е бъгът от 14.07 — следенето изпуска барове")
    A_.notes.append(f"закъснения (мин): {[round(v) for v in vals]}")


def reconstruct_trades(live: Path):
    """Вади всички сделки от git историята на open_trade.json/silver_trade.json."""
    repo = live.parent
    out = []
    for fname in ("open_trade.json", "silver_trade.json"):
        try:
            log = subprocess.run(["git", "-C", str(repo), "log", "--format=%H", "--", f"live/{fname}"],
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", timeout=60).stdout.split()
        except Exception:
            continue
        seen = {}
        for h in log:
            try:
                c = subprocess.run(["git", "-C", str(repo), "show", f"{h}:live/{fname}"],
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=30).stdout
                d = json.loads(c)
                key = (d.get("entry"), d.get("opened"))
                if key not in seen:
                    seen[key] = d
            except Exception:
                pass
        for d in seen.values():
            d["closed"] = None
            out.append(d)
    return sorted(out, key=lambda d: d.get("opened", ""))


# ─────────────────── 🎯 ТОЧНОСТ ───────────────────
def check_accuracy(live: Path, code_dir: Path, lb, bars5):
    import pandas as pd
    cat = "ТОЧНОСТ"
    tr = jload(live / "open_trade.json")
    s_tr = jload(live / "silver_trade.json")

    # Т1 · аритметика на нивата
    bad = []
    for name, t, fn in (("злато", tr, lb._levels), ("сребро", s_tr, lb._levels_silver)):
        if not t:
            continue
        want = dict(fn(t["entry"], t["direction"]))
        if t.get("hit", {}).get("tp1"):          # след ТП1 sl легитимно = входа (BE-стоп) — НЕ е повреда
            want["sl"] = t["entry"]
        if want != t["levels"]:
            bad.append(f"{name}: записани {t['levels']} ≠ сметнати {want}")
    if not tr and not s_tr:
        A.skip(cat, "Т1", "аритметика на нивата — НЕ Е ПРОВЕРЕНА", "няма отворени сделки")
    elif bad:
        A.fail(cat, "Т1", "НИВАТА НЕ СЪВПАДАТ с формулата", " | ".join(bad),
               "състоянието е повредено или версията е сменена насред сделка")
    else:
        A.ok(cat, "Т1", "аритметика на нивата", "точна до цент")

    # Т2 · спот-леджър (мигрирани ли са сделките)
    unmig = [n for n, t in (("злато", tr), ("сребро", s_tr)) if t and t.get("ledger") != "spot"]
    if not (tr or s_tr):
        A.skip(cat, "Т2", "спот-леджър — НЕ Е ПРОВЕРЕН", "няма сделки")
    elif unmig:
        A.warn(cat, "Т2", "сделка с ФЮЧЪРСНИ нива", f"{', '.join(unmig)} — старата версия",
               "новият бот ще ги мигрира сам при първото пускане")
    else:
        A.ok(cat, "Т2", "спот-леджър", "всички сделки са в спот-цени")

    # Т3 · базисът
    meta = jload(live / "meta.json", {})
    bg = meta.get("basis_g")
    if bg is None:
        A.warn(cat, "Т3", "базис фючърс−спот", "не се мери (стара версия)")
    else:
        _sp = meta.get("last_spot_g") or 2000.0
        _cap = max(25.0, 0.02 * _sp)          # кери = спот x лихва x срок; при 4088$ това е ~55$
        if abs(bg) <= _cap:
            A.ok(cat, "Т3", "базис фючърс-спот", f"{bg:+.2f}$ = {bg / _sp * 100:+.2f}% от спота (кери, нормално)")
        else:
            A.fail(cat, "Т3", "БАЗИСЪТ Е АБСУРДЕН", f"{bg:+.2f}$ = {bg / _sp * 100:+.2f}% от спота (таван {_cap:.0f}$)",
                   "това не е кери; дали базисът превежда вярно казва Т5")

    # Т4 · ПРОПУСНАТ УДАР ← това е бъгът от 14.07
    if tr and bars5 is not None:
        since = pd.Timestamp(tr.get("checked", tr["opened"]))
        w = bars5[bars5.index > since]
        # КРИТИЧНО: преведи фючърсните барове в спот (High−базис), точно както track_trade —
        # иначе сравняваш спот-нива срещу сурови фючърси → фалшива «ПРОПУСНАТ УДАР» при почти
        # всяка LONG близо до цел. bg от meta.json (v5); за v4 (без базис) → 0, нивата са фючърсни.
        b = bg if bg is not None else 0.0
        missed = []
        for k in ("tp1", "tp2", "tp3"):
            if tr["hit"].get(k):
                continue
            lvl = tr["levels"][k]
            hit = ((w["Low"] - b) <= lvl).any() if tr["direction"] == "short" else ((w["High"] - b) >= lvl).any()
            if hit:
                missed.append(k)
        sl = tr["levels"]["sl"]
        sl_hit = ((w["High"] - b) >= sl).any() if tr["direction"] == "short" else ((w["Low"] - b) <= sl).any()
        if sl_hit:
            missed.append("sl")
        if missed:
            A.fail(cat, "Т4", "ПРОПУСНАТ УДАР — БОТЪТ НЕ Е ПРАТИЛ",
                   f"нивата {', '.join(m.upper() for m in missed)} са докоснати след последната проверка!",
                   "точно бъгът от 14.07 — следенето изпуска барове; провери track_trade")
        else:
            A.ok(cat, "Т4", "няма пропуснат удар", "всички нива по баровете са отчетени")
    elif tr:                                      # има отворена сделка, но НЯМА барове (мрежа долу)
        A.warn(cat, "Т4", "пропуснат удар — непроверим", "yfinance недостъпен — не мога да сверя удар")
    else:
        A.skip(cat, "Т4", "пропуснат удар — НЕ Е ПРОВЕРЕН", "няма отворена сделка")

    # Т5 · съответствие карта ↔ спот (само v5)
    J = jall(live, "live_journal.jsonl")
    v5 = [r for r in J if r.get("spot") and r.get("bar")]
    if v5:
        offs = [abs(r["bar"] - (r.get("basis") or 0.0) - r["spot"]) for r in v5 if r.get("spot")]
        if offs:
            mx = max(offs)
            if mx <= 25:
                A.ok(cat, "Т5", "спот срещу бар", f"най-голяма разлика {mx:.1f}$ СЛЕД базиса (остатъчна)")
            else:
                A.fail(cat, "Т5", "СПОТЪТ И БАРЪТ СЕ РАЗМИНАВАТ", f"до {mx:.1f}$ СЛЕД изваждане на базиса",
                       "базисът вече не превежда бара в спот — провери _basis_update/роловъра")
    else:
        A.warn(cat, "Т5", "спот срещу бар", "живата версия не записва спот")

    # Т6 · Д2: геометрията срещу живата волатилност (SL/ATR, TP3/ATR)
    if bars5 is not None:
        try:
            daily = bars5["High"].resample("D").max() - bars5["Low"].resample("D").min()
            atr = float(daily.dropna().tail(14).mean())
            sl_ratio = lb.SL_D / atr if atr else 0
            tp3_ratio = TP3_D(lb) / atr if atr else 0
            det = f"ATR≈${atr:.0f} · SL/ATR {sl_ratio:.2f} · ТП3/ATR {tp3_ratio:.2f}"
            if 0.5 <= sl_ratio <= 3.0 and tp3_ratio <= 3.5:
                A.ok(cat, "Т6", "геометрия срещу волатилност", det)
            else:
                A.warn(cat, "Т6", "геометрия ≠ волатилност", det,
                       "стопът/целите не пасват на текущия ATR — обмисли ATR-мащаб (отделен тест)")
        except Exception as e:
            A.warn(cat, "Т6", "геометрия — НЕПРЕСМЕТНАТА", type(e).__name__,
                   "проверката гръмна — това не е зелено")
    else:
        A.warn(cat, "Т6", "геометрия — НЕПРОВЕРЕНА", "няма барове (yfinance недостъпен)")


def TP3_D(lb):
    return lb.TPS[2][2]      # $/oz на ТП3


# ─────────────────── 💀 МЪРТВИ ───────────────────
def check_dead(live: Path):
    cat = "МЪРТВИ"
    # М1 · заседнала поща (+ Б6: отровно съобщение)
    ob = jlines(live / "outbox.jsonl")
    if not (live / "outbox.jsonl").exists():
        A.ok(cat, "М1", "пощенска кутия", "няма (стара версия — съобщенията НЕ са защитени)")
    elif not ob:
        A.ok(cat, "М1", "пощенска кутия", "празна — всичко е пратено")
    else:
        # Реалният праг за «отровно» е hard_fails≥3 (само ТВЪРДИ 4xx: 400/403/404/413),
        # НЕ attempts — мрежов/429 провал ретрайва вечно и НЕ се хвърля.
        poison = [m for m in ob if m.get("hard_fails", 0) >= 3]
        near = [m for m in ob if 1 <= m.get("hard_fails", 0) < 3]
        if poison:
            A.fail(cat, "М1", "ОТРОВНО СЪОБЩЕНИЕ", f"{len(poison)} с ≥3 твърди провала: {[m.get('tag') for m in poison][:3]}",
                   "развален HTML/забранен (4xx) — вече се хвърля; провери текста")
        elif near:
            A.warn(cat, "М1", "близо до отровно", f"{len(near)} с 1-2 твърди провала: {[m.get('tag') for m in near][:3]}",
                   "4xx провал — още 1-2 опита и се хвърля; провери HTML-а")
        else:
            A.warn(cat, "М1", "чакащи съобщения", f"{len(ob)} чакат (мек провал, ретрай вечно): {[m.get('tag') for m in ob][:4]}",
                   "Телеграм отказва (мрежа/429/токен) — провери токена/чата; НЕ се губят")

    # М2 · повредени файлове
    corr = list(live.glob("*.corrupt"))
    if corr:
        A.warn(cat, "М2", "имало е повреден файл", f"{[c.name for c in corr]} — самолекуването е сработило",
               "провери дали пускането не е прекъсвано")
    else:
        A.ok(cat, "М2", "повредени файлове", "няма")

    # М3 · застояла сделка
    for name, f in (("злато", "open_trade.json"), ("сребро", "silver_trade.json")):
        t = jload(live / f)
        if not t:
            continue
        age = (now_utc() - datetime.fromisoformat(t["opened"])).days
        if age >= 30:
            A.fail(cat, "М3", f"{name}: сделка на {age} дни", "трябваше да излезе по време",
                   "времевият изход не е сработил")
        elif age >= 21:
            A.warn(cat, "М3", f"{name}: сделка на {age} дни", "наближава времевия изход")
        else:
            A.ok(cat, "М3", f"{name}: възраст на сделката", f"{age} дни")

    # М4 · състояние от стар ден
    for f, key in (("guard.json", "date"), ("last_sent.json", "date"), ("silver_sent.json", "date")):
        d = jload(live / f)
        if not d:
            continue
        if d.get(key) and d[key] < str((now_utc() - timedelta(days=4)).date()):
            A.warn(cat, "М4", f"{f} е от {d[key]}", "ботът не е пращал отдавна")
        else:
            A.ok(cat, "М4", f"{f}", f"от {d.get(key)}")

    # М5 · дублирани карти (един ключ, пратен 2 пъти)
    J = jall(live, "live_journal.jsonl")
    sig_runs = [r for r in J if any("signal=SENT" in s for s in r.get("status", []))]
    days = {}
    for r in sig_runs:
        days.setdefault(r["run_utc"][:10], []).append(r["run_utc"])
    burst = {d: v for d, v in days.items() if len(v) >= 6}
    if burst:
        # ОДИТ-12: печаташе СУРОВ python речник — нечетимо на телефон. Сега: най-лошият
        # ден + бройката, човешки.
        _wd, _wn = max(((d, len(v)) for d, v in burst.items()), key=lambda x: x[1])
        A.warn(cat, "М5", "много карти в един ден",
               f"{len(burst)} такива дни · най-много на {_wd[8:10]}.{_wd[5:7]} — {_wn} карти",
               "възможен спам или нервен пазар — виж дали е оправдано")
    else:
        A.ok(cat, "М5", "брой карти на ден", "в норма (<6)")

    # М6 · ТИХА СМЪРТ: има активен сигнал, но никаква карта от 24ч
    if sig_runs:
        last_sig = datetime.fromisoformat(sig_runs[-1]["run_utc"])
        h = (now_utc() - last_sig).total_seconds() / 3600
        if h > 48 and is_trading_time(now_utc()):
            A.warn(cat, "М6", "тиха смърт?", f"няма карта от {h:.0f} часа",
                   "нормално при застоял пазар, но провери дали не е бъг")
        else:
            A.ok(cat, "М6", "последна карта", f"преди {h:.1f} часа")


# ─────────────────── 🔒 ЦЯЛОСТ ───────────────────
def check_integrity(live: Path, code_dir: Path, repo: Path, skip_selftest=False):
    cat = "ЦЯЛОСТ"
    # Ц1 · живата версия == нашата?
    # ОДИТ-9 (A9/Ц1): ТАВТОЛОГИЯ. Workflow-ът вика `--repo . --code .`, значи
    # `repo/live_bot.py` и `code_dir/live_bot.py` бяха ЕДИН И СЪЩ ФАЙЛ и сравнението
    # `rtxt == local` беше винаги True. Най-важната проверка за цялост НЕ МОЖЕШЕ да гръмне.
    # Сега сравняваме с ЖИВИЯ файл от GitHub API (не raw — raw кешира и лъже).
    local = (code_dir / "live_bot.py").read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'VERSION\s*=\s*"([^"]+)"', local)
    lv = m.group(1) if m else "?"
    rf = repo / "live_bot.py"
    same_file = rf.exists() and rf.resolve() == (code_dir / "live_bot.py").resolve()
    rtxt = None
    src = "GitHub API"
    try:
        import base64 as _b64
        _api = "https://api.github.com/repos/AEROBOTAMOVE/PROMEGAAEERO/contents/live_bot.py?ref=main"
        rtxt = _b64.b64decode(json.loads(http(_api, 12))["content"]).decode("utf-8")
    except Exception as e:
        if rf.exists() and not same_file:
            rtxt = rf.read_text(encoding="utf-8", errors="ignore"); src = "repo-папка"
        else:
            A.warn(cat, "Ц1", "живата версия — НЕПРОВЕРИМА",
                   f"GitHub API не отговори ({type(e).__name__}), а локалният път сочи същия файл",
                   "не приемай това за зелено — просто не можах да сверя")
    if rtxt is not None:
        m2 = re.search(r'VERSION\s*=\s*"([^"]+)"', rtxt)
        rv = m2.group(1) if m2 else "v4 (без версия)"
        import hashlib as _hl
        h_live = _hl.sha256(rtxt.encode("utf-8")).hexdigest()[:12]
        h_loc = _hl.sha256(local.encode("utf-8")).hexdigest()[:12]
        if h_live == h_loc:
            A.ok(cat, "Ц1", "живата версия", f"{rv} — идентична с локалната (sha {h_live}, по {src})")
        else:
            A.fail(cat, "Ц1", "ЖИВАТА ВЕРСИЯ Е РАЗЛИЧНА",
                   f"живо: {rv} sha {h_live} · локално: {lv} sha {h_loc}",
                   "качи новия live_bot.py — иначе одитираш едно, а работи друго!")

    # Ц2 · selftest
    st = code_dir / "selftest.py"
    if skip_selftest:
        A.ok(cat, "Ц2", "selftest", "(пропуснат на повторно преминаване)")
    elif st.exists():
        r = subprocess.run([sys.executable, str(st)], cwd=str(code_dir), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=180,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0:
            n = out.count("PASS")
            A.ok(cat, "Ц2", "selftest", f"{n}/{n} минават")
        else:
            fails = [l for l in out.splitlines() if l.startswith("FAIL") or "SELFTEST FAIL" in l]
            A.fail(cat, "Ц2", "SELFTEST ПАДА", "; ".join(fails[:3]) or out[-200:],
                   "НЕ КАЧВАЙ този код!")
    else:
        A.warn(cat, "Ц2", "selftest", "липсва selftest.py")

    # Ц3 · фийдовете живи СЕГА
    feeds = {
        "спот злато (Swissquote)": ("https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD", 3000, 6000),
        "спот сребро (Swissquote)": ("https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAG/USD", 15, 150),
        "резерва PAXG (Binance)": ("https://api.binance.com/api/v3/ticker/bookTicker?symbol=PAXGUSDT", 3000, 6000),
        "резерва PAXG (Coinbase)": ("https://api.exchange.coinbase.com/products/PAXG-USD/ticker", 3000, 6000),
        "резерва PAXG (Kraken)": ("https://api.kraken.com/0/public/Ticker?pair=PAXGUSD", 3000, 6000),
    }
    for name, (url, lo, hi) in feeds.items():
        try:
            d = json.loads(http(url, 10))
            if isinstance(d, dict) and "bidPrice" in d:            # Binance
                px = float(d["bidPrice"])
            elif isinstance(d, dict) and d.get("result"):          # Kraken
                px = float(list(d["result"].values())[0]["b"][0])
            elif isinstance(d, dict) and "bid" in d:               # Coinbase
                px = float(d["bid"])
            else:                                                  # Swissquote
                px = float(d[0]["spreadProfilePrices"][0]["bid"])
            if lo <= px <= hi:
                A.ok(cat, "Ц3", name, f"жив · {px:.2f}")
            else:
                A.fail(cat, "Ц3", name, f"абсурдна цена {px}")
        except Exception as e:
            # Binance е забранен за US-IP (рънърите): 0 котировки в 4075 живи ръна.
            # Първи е във веригата, но НЕ е този, който спасява -> жълто, не червено.
            # името остава СЪЩОТО и при провал -> редът е сравним между преминаванията
            (A.warn if "Binance" in name else A.fail)(
                cat, "Ц3", name, f"НЕ ОТГОВАРЯ ({type(e).__name__})",
                "ботът ще падне на бар-цени (по-бавно, но работи)")
    try:
        txt = http("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10", 25)
        A.ok(cat, "Ц3", "лихви (FRED)", f"жив · {len(txt.splitlines())} реда")
    except Exception:
        A.warn(cat, "Ц3", "FRED не отговаря", "ботът ще ползва ^TNX резервата")

    # Ц4 · workflow-и + заковани версии
    try:
        import yaml
        _wf = ("aero-bot.yml", "tests.yml", "audit.yml")
        _miss = [w for w in _wf if not (code_dir / ".github/workflows" / w).exists()]
        for w in _wf:
            _p = code_dir / ".github/workflows" / w
            if _p.exists():
                yaml.safe_load(_p.read_text(encoding="utf-8"))
        if _miss:
            A.fail(cat, "Ц4", "ЛИПСВА WORKFLOW", ", ".join(_miss), "без него нищо не се пуска")
        else:
            A.ok(cat, "Ц4", "workflow файловете", f"{len(_wf)} валидни: " + ", ".join(_wf))
    except Exception as e:
        A.fail(cat, "Ц4", "WORKFLOW СЧУПЕН", str(e)[:120])
    req = (code_dir / "requirements.txt").read_text(encoding="utf-8") if (code_dir / "requirements.txt").exists() else ""
    _un = [l.strip() for l in req.splitlines()
           if l.strip() and not l.lstrip().startswith("#") and "==" not in l]
    if req and not _un:
        A.ok(cat, "Ц5", "заковани версии", req.replace("\n", " ").strip())
    else:
        A.warn(cat, "Ц5", "версиите НЕ са заковани",
               ("незаковани: " + ", ".join(_un)) if _un else "няма requirements.txt",
               "нов pandas/numpy може да счупи бота за една нощ")


# ─────────────────── 📊 ЧЕСТНОСТ ───────────────────
def check_honesty(code_dir: Path, data_dir: Path):
    cat = "ЧЕСТНОСТ"
    st = jload(code_dir / "backtest_stats.json", {})
    tfs = ["1мин", "5м", "15м", "30м", "1час", "4час", "1ден"]
    vals = set()
    for t in tfs:
        if t in st:
            L = st[t]["long"]["premium"]
            vals.add((L["win"], L["net"]))
    if len(vals) == 1 and len(tfs) > 1:
        A.warn(cat, "Ч1", "7-те ТФ показват ЕДНО число",
               f"{vals.pop()} под всичките {len(tfs)} етикета — един бектест под 7 имена",
               "картата вече не ги печата, но «7/7 ТФ съгласни» пресилва — те делят едно макро ядро")
    else:
        A.ok(cat, "Ч1", "ТФ статистиките", "различни по ТФ")

    th = st.get("tp_hits", {}).get("long", {}).get("premium", {})
    w = st.get("1ден", {}).get("long", {}).get("premium", {}).get("win")
    if th.get("tp3") and w:
        d = abs(th["tp3"] - w)
        mid = th["tp1"] - th["tp3"]
        if d < 3:
            A.warn(cat, "Ч2", "разпределението е БИМОДАЛНО",
                   f"ТП3-hit {th['tp3']}% ≈ win {w}% · само {mid:.1f}% живеят между ТП1 и ТП3",
                   "стълбицата от 3 тейка е предимно театър — знай го")
        else:
            A.ok(cat, "Ч2", "стълбицата работи", f"{mid:.1f}% от сделките живеят между ТП1 и ТП3")

    # Ч3-5 · леджерите са изследователски (не се качват в repo-то) → само ако папката е налична
    if not data_dir.exists():
        A.warn(cat, "Ч3", "ЧЕСТНОСТ не е проверена",
               "папката с леджери липсва в тази среда -> Ч3/Ч4/Ч5 НЕ СА ИЗПЪЛНЕНИ",
               "подай --data; windows-пътят по подразбиране никога не съществува на рънъра")
        return
    rules = {"US-щит": "f18_runs", "ре-влизане": "f18_runs", "флип само премиум": "f19_runs",
             "замразени референции": "f19_runs", "сребро само дневна": "f19_runs",
             "геометрия (boxoq)": "f20_runs"}
    missing = [r for r, f in rules.items() if not (data_dir / f).exists()]
    if missing:
        A.warn(cat, "Ч3", "правило без леджер", ", ".join(missing))
    else:
        A.ok(cat, "Ч3", "правилата имат тестове", f"{len(rules)} правила ↔ леджери")

    # Ч4 · липсващи леджери в поредицата
    have = sorted(int(m.group(1)) for p in data_dir.glob("f*_runs")
                  for m in [re.match(r"f(\d+)_runs", p.name)] if m)
    if have:
        gaps = [n for n in range(min(have), max(have) + 1) if n not in have]
        if gaps:
            A.warn(cat, "Ч4", "липсващи леджери", f"F{', F'.join(map(str, gaps))} — тестове без артефакт",
                   "F16 е родителят на бота (конфлуенцията) и няма запис на диска")
        else:
            A.ok(cat, "Ч4", "леджерите са пълни", f"F{min(have)}–F{max(have)}")
        dead = 0
        for p in data_dir.glob("f*_runs/*.json"):
            if "THREAD_ENDS" in p.read_text(encoding="utf-8", errors="ignore"):
                dead += 1
        A.ok(cat, "Ч5", "честна равносметка на тестовете",
             f"{len(have)} теста · {dead} с THREAD_ENDS → ~{100*dead/max(len(have),1):.0f}% мъртви")


# ─────────────────── ТАБЛО ───────────────────
def scoreboard(passes_info=""):
    print()
    print("═" * 74)
    print(f"🤖 ТАБЛО НА ОДИТ-РОБОТА · {sofia(now_utc()):%d.%m.%Y %H:%M} София{passes_info}")
    print("═" * 74)
    print(f"{'група':<14}{'❌ червени':>12}{'⚠️ жълти':>12}{'✅ зелени':>12}{'⊘ непров.':>12}")
    print("─" * 74)
    for icon, cat in CATS:
        r, y, g = A.count(cat, RED), A.count(cat, YEL), A.count(cat, GRN)
        k = A.count(cat, SKP)
        mark = "" if r == 0 else "  ← ГЛЕДАЙ ТУК"
        print(f"{icon} {cat:<12}{r:>12}{y:>12}{g:>12}{k:>12}{mark}")
    print("─" * 74)
    R, Y = len(A.reds), len(A.yellows)
    K = sum(1 for r in A.rows if r["level"] == SKP)
    print(f"{'ОБЩО':<14}{R:>12}{Y:>12}{len(A.rows)-R-Y-K:>12}{K:>12}")
    print()
    if R == 0 and Y == 0:
        print("🟢 ВСИЧКО НАРЕД — всички нули. Ботът е здрав.")
    elif R == 0:
        print(f"✅ НЯМА СЧУПЕНО · {Y} бележки за знаене:")
        for x in A.yellows:
            print(f"   ⚠️  {x['code']} {x['name']} — {x['detail']}")
            if x["fix"]:
                print(f"       → {x['fix']}")
    else:
        print(f"🔴 {R} СЧУПЕНИ НЕЩА — оправи ги преди всичко друго:")
        for x in A.reds:
            print(f"   ❌ {x['code']} {x['name']} — {x['detail']}")
            if x["fix"]:
                print(f"       → {x['fix']}")
        if Y:
            print(f"\n   (+ {Y} жълти — виж по-горе)")
    print("═" * 74)
    return R, Y


# ОДИТ-12: ИЗВЕСТНИ И ПРИЕТИ. Тези не са новини — те са факти за бота, които собственикът
# вече знае и е решил да живее с тях. Всеки ден на върха на отчета са ШУМ: научават го да
# не гледа жълтото, точно както фалшивото червено го научи да не гледа червеното.
# Слизат най-долу, в един ред, без подробности.
ЗНАЙНИ = {"Ч1", "Ч2", "М5", "Ч3"}
# ── ОДИТ-18: «НЕ МОЖАХ ДА ПРОВЕРЯ» ≠ «НЕЩО Е СЧУПЕНО» ─────────────────────
# 11 от 27-те жълти казваха само това: нямаше какво да се мери (няма отворена
# сделка, няма барове, API мълчи, журналът е от стара версия). Рисувани с ⚠️,
# те давят истинските предупреждения и учат човека да не ги гледа.
# Слизат при ⊘ — вижда се, че не е проверено, но не е тревога.
НЕ_МОЖАХ = re.compile(
    r"неизмерим|непровер|непресметнат|не се мери|недостатъчно данни|"
    r"не отговор|няма барове|няма сделк|няма отворен|стара версия|"
    r"липсва в тази среда|не можах", re.I)
# ОДИТ-12: когато yfinance/мрежата липсва, ТРИ проверки викат за ЕДНА причина (В4, В5, Т6).
# На телефона това изглежда като три счупени неща. Слепват се в един ред.
ЕДНА_ПРИЧИНА = [({"В4", "В5", "Т6"}, "няма барове",
                 "пазарни данни недостъпни в този рън (yfinance/мрежа) → В4, В5 и Т6 не могат да се проверят")]


def _esc(t):
    """ОДИТ-12: Телеграм чете < като начало на HTML таг. «pandas>=2.2,<4» стигаше до
    човека като «pandas>=2.2,» — изяден текст. При лош баланс Телеграм връща 400 и
    ЦЯЛАТА карта не се доставя. Всяко ЧУЖДО съдържание минава оттук."""
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ОДИТ-31 · «одит ти казах не искам». Отчетът върви в лога на Actions,
# не в Телеграм. Смениш ли това на True, се връща както беше.
ПРАЩАЙ_ОТЧЕТ = False

ПОЗДРАВИ = [
    # ОДИТ-30: първата версия ги пишеше «тука съм» — прочел бях
    # «НАПРАВИ ГО НАКЪВ ПОЗДРАВ КОСТА ТУКА СЪМ» като негово име.
    # Не е негово име. Поздравът е топъл и БЕЗ име, докато не каже как да го викам.
    "тука съм",
    "обиколих всичко",
    "минах през бота",
    "ето ме",
    "отвсякъде погледнах",
    "дежурството мина",
    "проверих го от край до край",
    "готово",
]


def telegram_msg(R, Y):
    """ОДИТ-29 · собственикът, 11.08: «махни това добър ден — толкова е сухо и тъпо;
    направи го някакъв поздрав тука съм» и «съобщението провери бота
    трябва да е МЕГА КЪСО, както вече говорехме хиляда пъти».

    При всичко наред → ЕДИН ред. Картата има право да порасне САМО когато има
    какво да се прави — и пак: какво е счупено, откога, какво да направиш."""
    _h = sofia(now_utc())
    # ОДИТ-29: индексът беше САМО по ден, а роботът се обажда 3× на ден →
    # един и същ поздрав три пъти в един ден. Часът влиза в сметката.
    _пз = ПОЗДРАВИ[(_h.timetuple().tm_yday * 3 + _h.hour // 8) % len(ПОЗДРАВИ)].capitalize()

    # 🔴 ОДИТ-21 · тук имаше `A.yellows = [...]`, а `yellows` е @property БЕЗ
    # setter → AttributeError при всяко пускане с --send. Присвояването беше и
    # излишно: `yellows` се извежда от `rows` по ниво.
    for _x in list(A.yellows):
        if НЕ_МОЖАХ.search(f"{_x.get('name','')} {_x.get('detail','')}"):
            _x["level"] = SKP
    _ново = [x for x in (A.reds + A.yellows) if x["code"] not in ЗНАЙНИ]
    _слети = []
    for codes, name, why in ЕДНА_ПРИЧИНА:
        hit = [x for x in _ново if x["code"] in codes]
        if len(hit) >= 2 and all(x["level"] == YEL for x in hit):
            _ново = [x for x in _ново if x["code"] not in codes]
            _слети.append({"code": "+".join(sorted(codes)), "name": name,
                           "detail": why, "level": YEL, "fix": ""})
    _ново = _слети + _ново
    _червени = [x for x in _ново if x["level"] == RED]

    # ── всичко работи → ЕДИН ред, точка ───────────────────────────────────
    if not _червени:
        опашка = "" if not _ново else f" · {len(_ново)} дребни бележки"
        return f"🤖 {_пз} · всичко чисто{опашка} · {_h:%H:%M}"

    # ── има счупено → какво, откога, какво да правя ───────────────────────
    L = [f"🤖 {_пз} · има {'проблем' if len(_червени) == 1 else f'{len(_червени)} проблема'}"
         f" · {_h:%H:%M}"]
    for x in _червени[:4]:
        L.append(f"🔴 {_esc(x['code'])} {_esc(x['name'])}")
        if x.get("detail"):
            L.append(f"📌 {_esc(x['detail'])[:120]}")
        if x.get("fix"):
            L.append(f"→ {_esc(x['fix'])[:100]}")
    if len(_червени) > 4:
        L.append(f"📌 и още {len(_червени) - 4}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=f"🤖 Одит-робот на AERO бота v{AUDIT_VERSION}")
    ap.add_argument("--repo", default="live", help="път до клонираното repo (или 'live' = текущата папка)")
    ap.add_argument("--code", default=".", help="папка с live_bot.py за одит")
    ap.add_argument("--data", default=r"C:\Users\User\Downloads\ЛОЦО\f6_data", help="папка с леджерите")
    ap.add_argument("--passes", type=int, default=1, help="колко пъти да мине по нестабилните проверки")
    ap.add_argument("--send", action="store_true", help="прати отчета в Телеграм")
    args = ap.parse_args()

    repo = Path(args.repo); live = repo / "live" if (repo / "live").exists() else repo
    code_dir = Path(args.code); data_dir = Path(args.data)

    print(f"🤖 ОДИТ-РОБОТ v{AUDIT_VERSION} · тръгвам...")
    print(f"   живо състояние: {live}")
    print(f"   код за одит:    {code_dir}")
    print()

    # свежи барове (за реконструкция на ударите)
    bars5 = None
    try:
        import warnings; warnings.filterwarnings("ignore")
        import pandas as pd, yfinance as yf
        df = yf.download("GC=F", period="60d", interval="5m", progress=False, auto_adjust=True)
        df.columns = [c if isinstance(c, str) else c[0] for c in df.columns]
        idx = pd.DatetimeIndex(df.index)
        if idx.tz is not None:
            idx = idx.tz_convert("UTC").tz_localize(None)
        df.index = idx
        bars5 = df.dropna(subset=["Close"])
        print(f"   свежи барове: {len(bars5)} × 5м · последен {bars5.index[-1]}")
    except Exception as e:
        print(f"   ⚠ баровете не се дръпнаха ({type(e).__name__}) — част от проверките ще се пропуснат")

    import importlib.util
    spec = importlib.util.spec_from_file_location("lb", code_dir / "live_bot.py")
    lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)
    globals()["lb"] = lb                                   # НАХОДКА C: за is_trading_time (пазар-часове по НЮ ЙОРК)

    # МНОГОКРАТНО МИНАВАНЕ: нестабилните проверки (фийдове, пулс, барове) се въртят
    # N пъти и се пази НАЙ-ЛОШИЯТ резултат — така прескачащ фийд не се крие.
    passes = max(1, args.passes)
    if passes > 1:
        print(f"   🔁 {passes} преминавания (пази най-лошия резултат от нестабилните проверки)")
    for pi in range(passes):
        A.rows = []                                       # чист лист всяко преминаване
        for icon, cat in CATS:
            if pi == 0:
                print(f"\n{icon} {cat}")
                print("─" * 40)
            silent = pi > 0
            _sink = A.add
            if silent:                                    # тихо на следващите преминавания
                A.add = lambda *a, **k: A.rows.append({"cat": a[0], "code": a[1], "name": a[2],
                                                       "level": a[3], "detail": a[4] if len(a) > 4 else "",
                                                       "fix": a[5] if len(a) > 5 else ""})
            if cat == "ВРЕМЕ":
                check_time(live, code_dir, bars5)
                if pi == 0:                                # В5 git-реконструкция е бавна → веднъж
                    check_delay_engine(live, bars5, A)
            elif cat == "ТОЧНОСТ":
                check_accuracy(live, code_dir, lb, bars5)
            elif cat == "МЪРТВИ":
                check_dead(live)
            elif cat == "ЦЯЛОСТ":
                check_integrity(live, code_dir, repo, skip_selftest=(pi > 0))   # selftest бавен → веднъж
            elif cat == "ЧЕСТНОСТ":
                check_honesty(code_dir, data_dir)
            A.add = _sink
        if pi == 0:
            worst = {(r["code"], r["name"]): r for r in A.rows}
        else:
            for r in A.rows:                              # запази по-лошия статус
                sev = {GRN: 0, YEL: 1, RED: 2}
                _k = (r["code"], r["name"])
                if _k not in worst or sev[r["level"]] > sev[worst[_k]["level"]]:
                    worst[_k] = r
    if passes > 1:
        A.rows = list(worst.values())

    R, Y = scoreboard()
    # ═══ ОДИТ-23 · ОДИТЪТ МЪЛЧИ, ОСВЕН КОГАТО НЕЩО НАИСТИНА Е СЧУПЕНО ═══
    # Собственикът, дословно: «той не спира да бълва това добро утро и тая огромна
    # дразнеща проверка — трябва да спре всичко това».
    # Прав е. Одитът е ИНСТРУМЕНТ ЗА МЕН — начин да хвана дефект, преди той да го
    # усети. Три пъти дневно да му изсипвам таблица с 35 реда «всичко работи» не
    # му дава нищо и го учи да не гледа съобщенията от бота изобщо — а точно тях
    # трябва да гледа.
    # ОТСЕГА: праща се САМО при истинско червено. Нула червени → тишина.
    # Всичко останало си остава в лога на Actions, където ми е мястото.
    # ОДИТ-31 · собственикът, 11.08 вечерта: «одит ти казах не искам —
    # разбрахме се, искаме само неща полезни за човек трейдър».
    # Одитът ПРОДЪЛЖАВА да върви (той е моят щит), но не пише в Телеграм.
    # Будилникът при 6 поредни провала на самия бот остава — той е в yml-а
    # и е друг механизъм; това тук е само отчетът.
    if args.send and not ПРАЩАЙ_ОТЧЕТ:
        print("🔕 отчетът НЕ се праща в Телеграм (по изрично искане) — виж лога по-горе")
    elif args.send and not A.reds:
        print(f"✅ нула счупени неща ({Y} бележки) — НЕ пращам нищо "
              f"(по изрично искане на собственика; отчетът е в лога по-горе)")
    elif args.send:
        try:
            res = lb._send_raw(telegram_msg(R, Y))
            # ОДИТ-9 (A1): преди това всеки провал се печаташе и се излизаше с код 0 —
            # Actions показваше зелено, а отчетът не беше стигнал доникъде. Мълчалив
            # провал на самия одитор е по-опасен от всяко негово червено.
            if res is None or "SENT" not in str(res):
                print("::error::отчетът НЕ Е ДОСТАВЕН — Телеграм върна:", res)
                sys.exit(1)
            print("отчетът е пратен в Телеграм:", res)
        except Exception as e:
            print("::error::пращането се провали:", e)
            sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
