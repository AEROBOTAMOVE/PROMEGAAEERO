"""
live_bot.py — AERO METALS BOT v5.0 «ТОЧНОСТ ПРЕДИ ВСИЧКО» (16.07.2026)

КАЧВАНЕ 1 от МЕГА-УЛТРА ПЛАНА. Новото спрямо v4:
  Ф1   Компактни СПОТ-ПЪРВИ карти: всички числа готови от живия спот, ред
       «ВЛИЗАЙ: ДА/ВНИМАТЕЛНО/НЕ», изходи с ЧАСА на реалния удар, изричен
       ред «НОВО ВЛИЗАНЕ: ДА/НЕ + защо». Нула смятане за човека.
  Ф2   Стоп-пазач (2 стопа/посока/ден = край) · ре-влизане по F18 правилата
       (SHORT пресен и SHORT в US-прозореца — блокирани; данните го казаха)
       · US-щит 8:25–9:15 НЮ ЙОРКСКО време (само за SHORT — F18).
  Ф7.1 Моментално засичане на ТП/СТОП по ЖИВИЯ спот (≈каданса: ≤5 мин денем UTC 5-21,
       ≤10-15 мин нощем; плюс опашката на GitHub Actions при пик).
  Ф8   Пощенска кутия (съобщение не се губи при Telegram провал) · спот-
       санити · самолекуващо се състояние · датата само напред.
  Ф9   СПОТ-ЛЕДЖЪР: сделките живеят в спот-света на брокера ти; базисът
       фючърс−спот се мери автоматично (EMA) и превежда баровете · роловър-
       детекция · гап-детекция (изход на реалната цена) · нива от правилната
       страна на спреда · ъпгрейд на класа минава анти-спам паузата.

Данни: Yahoo (барове, ~10-15 мин закъснение) + Swissquote спот (реално
време) + FRED. ЧЕСТНО: бичи backtest; SHORT е слаб; хартия първо; не е
финансов съвет. Токен: env TELEGRAM_TOKEN + TELEGRAM_CHAT_ID.
"""
from __future__ import annotations
import argparse, copy, io, json, os, urllib.parse, urllib.request, warnings
from datetime import datetime, timezone
from pathlib import Path
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

VERSION = "v5.5e"
PIP = 0.10
SL_PIPS = 200; SL_D = SL_PIPS * PIP                       # стоп: 200п = $20/oz
TPS = [("ТП1", 75, 7.5), ("ТП2", 120, 12.0), ("ТП3", 200, 20.0)]
S_TPS = [0.20, 0.32, 0.54]; S_SL = 0.54                   # СРЕБРО $/oz
TFS = [("1мин", "1m", "7d", None), ("5м", "5m", "60d", None), ("15м", "15m", "60d", None),
       ("30м", "30m", "60d", None), ("1час", "60m", "730d", None),
       ("4час", "60m", "730d", "4h"), ("1ден", None, None, None)]
MACRO_LBL = ["миньори", "долар", "лихви"]
BASIS_ALPHA = 0.25          # EMA тегло на базиса фючърс−спот
ROLLOVER_JUMP = 8.0         # скок на базиса >$8 за нощ = роловър → ре-анкер
SHIELD_ET = (8 * 60 + 25, 9 * 60 + 15)   # US-щит: 8:25–9:15 Ню Йорк (САМО short)


# ---------- дърпане на данни (упорито) ----------
def _retry(fn, tries=3, base_wait=4):
    import time
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            last = e
            print(f"  опит {i+1}/{tries} неуспешен: {type(e).__name__}; чакам {base_wait*(i+1)}с")
            time.sleep(base_wait * (i + 1))
    raise last


def _yf(sym, period="2y", interval="1d"):
    def go():
        import yfinance as yf
        df = yf.download(sym, period=period, interval=interval, progress=False, auto_adjust=True)
        if df is None or len(df) == 0:
            raise RuntimeError(f"празни данни за {sym} ({interval})")
        df.columns = [a if isinstance(a, str) else a[0] for a in df.columns]
        idx = pd.DatetimeIndex(df.index)
        if idx.tz is not None:
            idx = idx.tz_convert("UTC")   # интрадей идва в NY време → първо в UTC!
        df.index = idx.tz_localize(None) if idx.tz is not None else idx
        return df.dropna(subset=["Close"])
    return _retry(go)


def _fred(series_id):
    def go():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        with urllib.request.urlopen(url, timeout=30) as r:
            df = pd.read_csv(io.BytesIO(r.read()))
        df.columns = ["date", "v"]
        df["date"] = pd.to_datetime(df["date"]); df["v"] = pd.to_numeric(df["v"], errors="coerce")
        return df.dropna().set_index("date")["v"]
    return _retry(go)


def _rates():
    try:
        s = _fred("DFII10"); print("  лихви: FRED DFII10 (реални) ✓"); return s
    except Exception:
        df = _yf("^TNX", "2y", "1d"); print("  лихви: ^TNX (резерва)")
        return df["Close"] / 10.0


# ---------- сигнал (ЯДРОТО — непипнато от v4) ----------
def _macro(gold_d, gdx_d, dxy_d, rr):
    idx = gold_d.index
    g = gold_d["Close"]; gd = gdx_d["Close"].reindex(idx).ffill()
    dx = dxy_d["Close"].reindex(idx).ffill(); r = rr.reindex(idx).ffill()
    return {"миньори": bool(((gd.pct_change(50) - g.pct_change(50)) > 0).iloc[-1]),
            "долар": bool(((-(dx.pct_change(20))) > 0).iloc[-1]),
            "лихви": bool(((-(r - r.shift(20))) > 0).iloc[-1])}


def _sofia(iso_utc=None):
    from zoneinfo import ZoneInfo
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat(str(iso_utc)) if iso_utc else datetime.now(timezone.utc).replace(tzinfo=None)
        return dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Europe/Sofia")).strftime("%H:%M")
    except Exception:
        return "?"


def _in_shield(now_utc=None):
    """В US-прозореца 8:25–9:15 НЮ ЙОРКСКО време ли сме (данните в 8:30 ET)?
    Дефиниран в ET, не в София — лятното време се мести в различни седмици."""
    from zoneinfo import ZoneInfo
    try:
        dt = datetime.fromisoformat(str(now_utc)) if now_utc else datetime.now(timezone.utc).replace(tzinfo=None)
        et = dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/New_York"))
        m = et.hour * 60 + et.minute
        return SHIELD_ET[0] <= m <= SHIELD_ET[1]
    except Exception:
        return False


def _shield_sofia_label():
    """Прозорецът на щита, преведен в София час (за картите)."""
    from zoneinfo import ZoneInfo
    try:
        today = datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York")).date()
        a = datetime(today.year, today.month, today.day, SHIELD_ET[0] // 60, SHIELD_ET[0] % 60,
                     tzinfo=ZoneInfo("America/New_York")).astimezone(ZoneInfo("Europe/Sofia"))
        b = datetime(today.year, today.month, today.day, SHIELD_ET[1] // 60, SHIELD_ET[1] % 60,
                     tzinfo=ZoneInfo("America/New_York")).astimezone(ZoneInfo("Europe/Sofia"))
        return f"{a.strftime('%H:%M')}–{b.strftime('%H:%M')} София"
    except Exception:
        return "15:25–16:15 София"


def _streaks(gold_d, gdx_d, dxy_d, rr):
    idx = gold_d.index
    g = gold_d["Close"]; gd = gdx_d["Close"].reindex(idx).ffill()
    dx = dxy_d["Close"].reindex(idx).ffill(); r = rr.reindex(idx).ffill()
    m_l = ((gd.pct_change(50) - g.pct_change(50)) > 0) & ((-(dx.pct_change(20))) > 0) & ((-(r - r.shift(20))) > 0)
    m_s = ((gd.pct_change(50) - g.pct_change(50)) < 0) & ((dx.pct_change(20)) > 0) & (((r - r.shift(20)) > 0))
    def last_streak(s):
        s = s.fillna(False)
        return int(s.groupby((~s).cumsum()).cumsum().iloc[-1])
    return {"long": last_streak(m_l), "short": last_streak(m_s)}


def _refs(gold_d):
    c, h, l = gold_d["Close"], gold_d["High"], gold_d["Low"]
    def last(x):
        v = x.iloc[-1]; return float(v) if pd.notna(v) else np.nan
    return {"sma50": last(c.rolling(50).mean()), "sma20": last(c.rolling(20).mean()),
            "ago5": last(c.shift(5)), "ago20": last(c.shift(20)),
            "low20": last(l.rolling(20).min()), "high20": last(h.rolling(20).max())}


def _regime(gold_hist, gold_today=None):
    """Ф9.1: стойностите (SMA, вол) — от ЗАВЪРШЕНИ дни (gold_hist);
    MA-докосванията — с ДНЕШНИЯ жив бар (gold_today, ако е подаден)."""
    c, h, l = gold_hist["Close"], gold_hist["High"], gold_hist["Low"]
    sma50 = c.rolling(50).mean().iloc[-1]; sma200 = c.rolling(200).mean().iloc[-1]
    vol20 = c.pct_change().rolling(20).std()
    volmed = vol20.rolling(252).median().iloc[-1]
    src = gold_today if gold_today is not None else gold_hist
    cN, hN, lN = float(src["Close"].iloc[-1]), float(src["High"].iloc[-1]), float(src["Low"].iloc[-1])
    below = bool(cN < sma200) if pd.notna(sma200) else None
    lowv = bool(vol20.iloc[-1] < volmed) if pd.notna(volmed) and pd.notna(vol20.iloc[-1]) else None
    vr = vol20.rolling(504).rank(pct=True).iloc[-1]
    vol_rank = float(vr) if pd.notna(vr) else None
    ma = {}
    if pd.notna(sma50):
        ma["long_ma50"] = bool(lN <= sma50 and cN > sma50)
        ma["short_ma50"] = bool(hN >= sma50 and cN < sma50)
    if pd.notna(sma200):
        ma["long_ma200"] = bool(lN <= sma200 and cN > sma200)
        ma["short_ma200"] = bool(hN >= sma200 and cN < sma200)
    return {"below_sma200": below, "low_vol": lowv, "ma": ma, "vol_rank": vol_rank,
            "sma50": float(sma50) if pd.notna(sma50) else None,
            "sma200": float(sma200) if pd.notna(sma200) else None}


def _scores(df, refs, macro):
    cN = float(df["Close"].iloc[-1]); lN = float(df["Low"].iloc[-1]); hN = float(df["High"].iloc[-1])
    def nn(v): return not (v is None or (isinstance(v, float) and np.isnan(v)))
    ml = [macro["миньори"], macro["долар"], macro["лихви"]]
    ms = [not m for m in ml]
    lp = [nn(refs["sma50"]) and cN > refs["sma50"], nn(refs["sma20"]) and cN > refs["sma20"],
          nn(refs["ago20"]) and cN > refs["ago20"],
          nn(refs["ago5"]) and nn(refs["ago20"]) and (cN / refs["ago5"] - 1 < 0) and (cN / refs["ago20"] - 1 > 0),
          nn(refs["low20"]) and lN <= refs["low20"] * 1.015]
    sp = [nn(refs["sma50"]) and cN < refs["sma50"], nn(refs["sma20"]) and cN < refs["sma20"],
          nn(refs["ago20"]) and cN < refs["ago20"],
          nn(refs["ago5"]) and nn(refs["ago20"]) and (cN / refs["ago5"] - 1 > 0) and (cN / refs["ago20"] - 1 < 0),
          nn(refs["high20"]) and hN >= refs["high20"] * 0.985]
    return sum(ml) + sum(1 for x in lp if x), sum(ms) + sum(1 for x in sp if x), cN


def _tier(score, m3):
    if m3: return ("premium", "ПРЕМИУМ")
    if score >= 6: return ("strong", "СИЛЕН")
    if score >= 4: return ("medium", "СРЕДЕН")
    return ("weak", "ЧАКАЙ")


def _resolve(ls, ss, macro):
    m3l = all(macro.values()); m3s = not any(macro.values())
    if ls > ss:
        tk, tn = _tier(ls, m3l); return ("long", ls, tk, tn)
    if ss > ls:
        tk, tn = _tier(ss, m3s); return ("short", ss, tk, tn)
    return ("wait", max(ls, ss), "weak", "ЧАКАЙ")


def _levels_gen(entry, direction, tp1, tp2, tp3, sl, dec=2):
    s = 1 if direction == "long" else -1
    return {"tp1": round(entry + s * tp1, dec), "tp2": round(entry + s * tp2, dec),
            "tp3": round(entry + s * tp3, dec), "sl": round(entry - s * sl, dec)}


def _levels(entry, direction):
    return _levels_gen(entry, direction, TPS[0][2], TPS[1][2], TPS[2][2], SL_D, 2)


def _levels_silver(entry, direction):
    return _levels_gen(entry, direction, S_TPS[0], S_TPS[1], S_TPS[2], S_SL, 3)


# ---------- спот в реално време + санити (Ф8.3) ----------
SPOT_MAX_AGE = 90        # A1: котировка по-стара от 90 сек не е «реално време»
CLOCK_SKEW = 60          # T1: сървърният ts може да води с ~1с спрямо рънъра → толеранс
def _spot(instr="XAU/USD", market_closed=False):
    """Swissquote публичен фийд, без ключ; за злато има РЕЗЕРВА (Binance PAXG).
    A1: избира цена САМО от ПРЯСНА платформа; прозорец 90 сек. Връща bid/ask/mid/src/age_sec.
    T1: под-секундно часово разминаване (age малко под 0) НЕ бракува фийда."""
    import time as _t
    try:
        url = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/" + instr
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=8) as r:
            data = json.loads(r.read().decode())
        best = None; best_age = None
        now_ms = _t.time() * 1000
        for plat in data:
            age = (now_ms - plat.get("ts", 0)) / 1000.0
            if age < -CLOCK_SKEW or age > SPOT_MAX_AGE:  # от «бъдещето» (боклук ts) ИЛИ застояла
                continue
            age = max(age, 0.0)                          # T1: часово скю → третирай като «сега»
            for p in plat.get("spreadProfilePrices", []):
                if p["bid"] < p["ask"] and (best is None or (p["ask"] - p["bid"]) < (best[1] - best[0])):
                    best = (p["bid"], p["ask"]); best_age = age
        if best is not None:
            return {"bid": round(best[0], 3), "ask": round(best[1], 3),
                    "mid": round((best[0] + best[1]) / 2, 3), "src": "swq",
                    "age_sec": round(best_age, 1)}
    except Exception:
        pass
    if market_closed:                                     # T5: не ползвай крипто-прокси при затворен пазар
        return None
    if instr == "XAU/USD":                                # Ф9.5: резервен източник (PAXG ≈ злато)
        try:
            url = "https://api.binance.com/api/v3/ticker/bookTicker?symbol=PAXGUSDT"
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=8) as r:
                q = json.loads(r.read().decode())
            b, a = float(q["bidPrice"]), float(q["askPrice"])
            if 0 < b < a:
                return {"bid": round(b, 2), "ask": round(a, 2), "mid": round((b + a) / 2, 2),
                        "src": "paxg", "age_sec": None}
        except Exception:
            pass
    return None


def _bar_range(fine, n=5):
    """A4: среден диапазон (High−Low) на последните n бара — мярка за скорост/новина."""
    try:
        if fine is None or len(fine) < n:
            return None
        w = fine.iloc[-n:]
        return float((w["High"] - w["Low"]).mean())
    except Exception:
        return None


def _spot_sane(spot, reference, base_diff, bar_rng=None, spot_jump=None):
    """Санити: спотът е близо до ОЧАКВАНОТО (бар−базис).
    A4: при новина цената скача $20-40 за секунди; фиксиран праг би отрязал живия спот.
    T3: барът ИЗОСТАВА → освен него ползвай и СКОКА на самия спот (spot_jump = |спот
    сега − спот преди|), който реагира моментално на новината."""
    if spot is None or reference is None:
        return None
    tol = base_diff
    if bar_rng:
        tol = max(tol, 1.8 * bar_rng)
    if spot_jump:
        # F2: спотът скочи → новина. НО глич също скача → не му позволявай да се
        # САМОВАЛИДИРА отвъд това, което барът подкрепя (иначе $100 глич минава сам).
        jump_cap = 2.5 * bar_rng if bar_rng else base_diff * 2
        tol = max(tol, min(1.5 * spot_jump, jump_cap))
    return spot if abs(reference - spot["mid"]) <= tol else None


def _entry_side(spot, direction):
    """Правилната страна на спреда: SHORT продава на BID, LONG купува на ASK."""
    return spot["bid"] if direction == "short" else spot["ask"]


def _to_ny(now_utc):
    """T2: UTC → Ню Йорк (America/New_York) — сам смята лятно/зимно време."""
    from zoneinfo import ZoneInfo
    dt = datetime.fromisoformat(str(now_utc)) if not isinstance(now_utc, datetime) else now_utc
    return dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/New_York"))


def _market_closed(now_utc):
    """A3/T2: пазарът затворен ли е — по НЮЙОРКСКО време (сам ловим DST).
    Затворено: петък 17:00 ET → неделя 18:00 ET (CME златото отваря нед 18:00 ET)."""
    try:
        et = _to_ny(now_utc); wd = et.weekday(); h = et.hour   # 0=пон … 4=пет, 5=съб, 6=нед
    except Exception:
        return False
    if wd == 5:                                        # цяла събота
        return True
    if wd == 4 and h >= 17:                            # петък след 17:00 ET
        return True
    if wd == 6 and h < 18:                             # неделя до 18:00 ET (после отваря)
        return True
    return False


# ---------- състояние: желязно четене (Ф8.2) ----------
def _load_state(path, default):
    """Повреден файл → самолекуване: преименува го и започва чисто."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        try:
            path.rename(path.with_suffix(".corrupt"))
            print(f"  ⚠ повреден {path.name} → чист старт (старият е .corrupt)")
        except Exception:
            pass
    return default


# ---------- базис фючърс−спот (Ф9.2 + роловър Ф9.7) ----------
def _cme_pause(now_utc):
    """A5/T2: CME Globex дневна пауза 17:00-18:00 НЮ ЙОРК (ловим DST сами).
    Тогава фючърсът спира, спотът върви → базисът «скача» фалшиво. Не ре-анкервай."""
    try:
        return _to_ny(now_utc).hour == 17
    except Exception:
        return False


def _basis_update(state, key, raw_spot, bar_close, notes, cap=40.0, now_utc=None):
    """EMA на базиса. ПОЛЗВА СУРОВИЯ спот (преди санитито) — иначе роловърът
    (скок +$25-30) реже спота, базисът замръзва и детекторът не се задейства = deadlock.
    Скок >$8 = роловър → ре-анкер, НО само ако е под cap (глич) И не сме в CME паузата (A5)."""
    if raw_spot is None or bar_close is None:
        return state.get(key, 0.0)
    now_b = bar_close - raw_spot["mid"]
    old = state.get(key)
    prev_bar = state.get(key + "_bar")
    state[key + "_bar"] = round(bar_close, 3)        # за кръстосана проверка следващия рън
    # НАХОДКА-B: резервата PAXG търгува с ~$1-4 премия → НЕ замърсявай базис-EMA с нея;
    # дръж последния swq-базис за конверсията, изчакай swq да се върне.
    if raw_spot.get("src") == "paxg":
        return state.get(key, round(now_b, 3))
    if old is None:                                 # НАХОДКА-D: студен старт без глич-защита
        if abs(now_b) <= cap:
            state[key] = round(now_b, 3)
        else:                                       # първи сампъл е глич → не го анкервай
            notes.append(f"студен старт: базис {now_b:+.1f} извън диапазон — изчаквам")
            return 0.0
    elif abs(now_b - old) > ROLLOVER_JUMP:
        moved = prev_bar is not None and abs(bar_close - prev_bar) >= 0.5 * abs(now_b - old)
        if _cme_pause(now_utc):                     # A5: нощна пауза → игнорирай скока, пази базиса
            notes.append(f"скок на базиса ({now_b:+.1f}) в CME паузата — игнориран, пазя {old:+.2f}")
        elif abs(now_b) <= cap and moved:           # НАХОДКА-A: ре-анкер САМО ако и БАРЪТ скочи сходно
            notes.append(f"роловър на контракта ({old:+.2f}→{now_b:+.2f}, барът скочи) — ре-анкер")
            state[key] = round(now_b, 3)
        else:                                       # само спотът «скочи» (глич) или абсурден → пази стария
            notes.append(f"отхвърлен скок на базиса ({now_b:+.1f}) — глич/несходно с бара, пазя {old:+.2f}")
    else:
        state[key] = round(old + BASIS_ALPHA * (now_b - old), 3)
    return state[key]


# ---------- съвети (Ф1.3 / Ф2 / F18) ----------
MIN_N = 100      # В4: под толкова сделки процентът е шум → не се цитира
def _pct(seg, label):
    """В4/В6: цитирай процент САМО ако има n≥MIN_N; иначе — без число."""
    if seg.get("n") and seg["n"] >= MIN_N and seg.get("win") is not None:
        return f": {label} {seg['win']}% · {seg['net']:+}$/oz (n={seg['n']})"
    return " (историята е малка — без число)"


def _advice_entry(direction, streak_n, stats, fast, shield, guard_n, sym="XAUUSD", stale_price=False):
    """(текст, ok) за реда «ВЛИЗАЙ». В1: сребро цитира САМО сребърни числа.
    Г2: изходът е ясен — ДА / ИЗЧАКАЙ / НЕ. В5: губещ клас се казва явно."""
    if guard_n >= 2:
        return "НЕ — 2 стопа днес в тази посока (стоп-пазач)", False
    if shield and direction == "short":
        return f"НЕ СЕГА — US-щит ({_shield_sofia_label()}); изчакай края му", False
    if stale_price:                                      # Г9: спотът недостъпен → цената е стара
        return "ИЗЧАКАЙ — цената е ~10-15 мин стара (спотът недостъпен); само лимитирана поръчка на нивото", False
    is_gold = sym == "XAUUSD"
    if is_gold:
        fr = stats.get("fresh", {}).get(direction, {})
        seg_fresh = fr.get("day1" if streak_n == 1 else "fresh", {})
        seg_stale = fr.get("stale", {})
        src = "пресен ден-" + str(streak_n)
    else:                                                # В1: сребро — от stats['silver'], не злато!
        sv = stats.get("silver", {}).get(direction, {})
        seg_fresh = sv.get("fresh", {}); seg_stale = sv.get("stale", {})
        src = "сребро пресен"
    # F4: «ден N» валиден само за ЗЛАТОТО (стрийкът е от златната цена); сребро → без ден-номер
    dn = f"ден {streak_n}" if is_gold else "по макро-подреждане"
    if 1 <= streak_n <= 3:
        seg = seg_fresh
        if seg.get("n", 0) >= MIN_N and seg.get("net", 0) <= 0:   # В5: пресен, но нулев/губещ клас
            return f"ИЗЧАКАЙ — пресен ({src}), но исторически {seg['win']}% · {seg['net']:+}$/oz — без ръб", False
        return f"ДА — пресен сигнал ({dn})" + _pct(seg, src) + _fast(fast), True
    seg = seg_stale
    if seg.get("n", 0) >= MIN_N and seg.get("net", 0) < 0:
        # НЕ обвинявай «макрото» (то може да е за тази посока, напр. 0/3 подкрепя шорт) —
        # губещ е ИСТОРИЧЕСКИЯТ КЛАС на този сетъп.
        cls = "този клас исторически губи (макрото не е ПОДРЕДЕНО днес)" if streak_n == 0 else f"застоял ({dn})"
        return f"НЕ — {cls}: {seg['win']}% · {seg['net']:+}$/oz — ГУБЕЩ клас" + _fast(fast), False
    # положителен-но-слаб клас: текстът СЪОТВЕТСТВА на action (следи се) — «ДА (слаб)», не «ИЗЧАКАЙ»
    ctx = "макро-подреждането не е активно днес — сигналът е по ценова структура" if streak_n == 0 else f"застоял ({dn}) — ръбът е по-слаб"
    return f"ДА (слаб) — {ctx}; малък размер" + _pct(seg, "клас") + _fast(fast), True


def _fast(fast):
    return f" · БЪРЗ ПАЗАР ±${fast:.0f}/10мин — само лимитирана поръчка" if fast else ""


def _reentry_verdict(direction, streak_n, shield, guard_n):
    """(може_ли, защо) за ре-влизане след приключена сделка — F18 правилата."""
    if guard_n >= 2:
        return False, "2 стопа днес в тази посока — стоп-пазач до утре"
    if direction == "short" and shield:
        return False, f"US-щит ({_shield_sofia_label()}) — шорт в прозореца губи (F18: −2.14$)"
    if direction == "short" and 1 <= streak_n <= 3:
        return False, "шорт ре-влизане при пресен сигнал исторически губи (F18: −2.75$)"
    return True, ""


# ---------- СЪОБЩЕНИЯ v5 — компактни, спот-първи ----------
def _fmt(p, dec=2):
    return f"{p:,.{dec}f}"


def _sig_msg(direction, score, agree_n, tier_name, spot, bar_price, bar_ts, lv, entry,
             advice_txt, macro, streak_n, regime, stats, balance, risk_pct, weekly=None,
             reentry=False, open_trade=None, sym="XAUUSD", dec=2, extra_ctx=None, adv_ok=True):
    """Компактна карта: 11-14 реда, всички числа готови."""
    dcol = "🔴" if direction == "short" else "🟢"
    metal = "ЗЛАТО" if sym == "XAUUSD" else "СРЕБРО"
    dword = "SHORT (продажба)" if direction == "short" else "LONG (купуване)"
    # Г2: тонът от съвета влиза и в цвета/иконата на заглавието
    warn = advice_txt.startswith("НЕ") or advice_txt.startswith("ИЗЧАКАЙ")
    head_icon = "🟡" if warn else dcol
    tf_part = " · макро+ценова структура" if sym == "XAUUSD" else " · дневен сигнал"   # В2: не «7 независими гласа»
    L = [f"{head_icon} <b>{metal} {dword}</b> · {tier_name} {score}/8{tf_part}",
         "─────────────────"]
    if open_trade:
        op = f"{open_trade['opened'][:10]} {_sofia(open_trade['opened'])}"
        hit = open_trade.get("hit", {})
        def hmark(k): return " ✅" if hit.get(k) else ""
        be = " · <i>стопът е на входа (безрисково)</i>" if hit.get("tp1") else ""   # Г / №9
        L += [f"СЪЩИЯТ СИГНАЛ ПРОДЪЛЖАВА — следим сделката от <code>{_fmt(open_trade['entry'], dec)}</code> <i>(от {op})</i>, НЕ нов вход.",
              f"ТП1 <code>{_fmt(open_trade['levels']['tp1'], dec)}</code>{hmark('tp1')} · ТП2 <code>{_fmt(open_trade['levels']['tp2'], dec)}</code>{hmark('tp2')} · ТП3 <code>{_fmt(open_trade['levels']['tp3'], dec)}</code>{hmark('tp3')}",
              f"СТОП <code>{_fmt(open_trade['levels']['sl'], dec)}</code>{be}"]
        if spot:
            L.append(f"Спот сега: <code>{_fmt(spot['mid'], dec)}</code>")
        L.append("<b>ДРЪЖ:</b> сделката тече — <b>не отваряй нова</b>.")   # Г1: НЕ «ВЛИЗАЙ» при отворена
    else:
        if reentry:
            L.append("РЕ-ВЛИЗАНЕ — предишната сделка приключи, сигналът още стои.")
        head = "<b>ВХОД СЕГА</b>" if adv_ok else "<b>АКО ВСЕ ПАК ВЛЕЗЕШ</b>"   # НАХОДКА 1: не карай да влиза при «НЕ»
        src = "спот, реално време" if spot else "по бара, ~10-15 мин назад — спотът е недостъпен!"
        L += [f"{head} ({src}): <code>{_fmt(entry, dec)}</code>",
              f"ТП1 <code>{_fmt(lv['tp1'], dec)}</code> · ТП2 <code>{_fmt(lv['tp2'], dec)}</code> · ТП3 <code>{_fmt(lv['tp3'], dec)}</code>",
              f"СТОП <code>{_fmt(lv['sl'], dec)}</code>"]
        if adv_ok:                                          # «сложи веднага / раздели» само когато съветът е ДА
            L += ["→ Раздели на 3: затвори 1/3 на ТП1, 1/3 на ТП2, 1/3 на ТП3; стопът е общ.",
                  "→ Сложи нивата при брокера ВЕДНАГА — изпълняват се сами."]
        if spot:
            L.append(f"<i>спред {abs(spot['ask']-spot['bid']):.2f} · вход от {'bid' if direction=='short' else 'ask'} страната</i>")
        L += [f"<b>ВЛИЗАЙ:</b> {advice_txt}"]                             # Г1: само при НОВ вход
    mac = sum(1 for v in macro.values() if v)
    # Г10: макрото спрямо ПОСОКАТА (за short «мечо» подкрепя, за long «бичо»)
    supports = (mac >= 2 and direction == "long") or (mac <= 1 and direction == "short")
    ctx = f"Макро {mac}/3 ({'подкрепя ✓' if supports else 'против ⚠'})"
    # В1/В4: УЛТРА само за ЗЛАТО (среброто няма такъв клас) и само с n≥MIN_N
    if sym == "XAUUSD" and regime and regime.get("vol_rank") is not None and 1 <= streak_n <= 3 and regime["vol_rank"] < 0.40:
        u = stats.get("fresh", {}).get(direction, {}).get("ultra", {})
        # УЛТРА само при СМИСЛЕН ръб (>$1/oz над спреда) — не при +0.04 (шорт-ултра = монета на ръба)
        if u.get("n", 0) >= MIN_N and u.get("net", 0) >= 1.0:
            ctx += f" · УЛТРА клас: {u['win']}% · {u['net']:+}$/oz (n={u['n']})"
    if weekly:
        lean = weekly.get("gold", {}).get("lean", "")
        if lean in ("bullish", "bearish"):
            ag = (lean == "bullish") == (direction == "long")
            ctx += " · седм. анализ: " + ("съгласен ✓" if ag else "ПРОТИВ ⚠")
    if extra_ctx:
        ctx += " · " + extra_ctx
    L.append(ctx)
    risk_amt = balance * risk_pct / 100.0
    _rp = lambda d: (d / balance * 100.0 if balance else 0.0)   # реален % от баланса
    if sym == "XAUUSD":
        oz = risk_amt / SL_D                       # 1 oz губи $20 при 200п стоп · 1 лот = 100 oz
        lot = oz / 100.0
        if lot < 0.01:                             # под брокерския минимум → не лъжи с «0.0 лот»
            mn = 1.0 * SL_D                         # най-малката реална позиция = 0.01 лот = 1 oz
            L.append(f"Риск ${balance:g}@{risk_pct:g}%: под мин. лот — най-малкото е <b>0.01 лот</b> "
                     f"(1 oz), което рискува −${mn:.0f} = {_rp(mn):.1f}% от баланса")
        else:
            L.append(f"Риск ${balance:g}@{risk_pct:g}%: <b>{lot:.2f} лот</b> ({oz:.1f} oz) → макс −${risk_amt:.2f}")
    else:
        oz = risk_amt / S_SL                       # 1 лот сребро = 5000 oz · мин. 0.01 лот = 50 oz
        if oz < 50.0:                              # под мин. лот — реалният риск НАДХВЪРЛЯ целта
            mn = 50.0 * S_SL
            L.append(f"Риск ${balance:g}@{risk_pct:g}%: под мин. лот — най-малкото е <b>0.01 лот</b> "
                     f"(50 oz), което рискува −${mn:.2f} = {_rp(mn):.1f}% (над целта — намали или пропусни)")
        else:
            L.append(f"Риск ${balance:g}@{risk_pct:g}%: <b>{oz/5000.0:.2f} лот</b> ({oz:.0f} oz) → макс −${risk_amt:.2f}")
    if direction == "short":
        L.append("<i>Шорт е непотвърден исторически — малък размер.</i>")
    L += ["─────────────────",
          f"<i>цена от бар {_sofia(str(bar_ts)) if bar_ts is not None else '?'} София · {VERSION} · хартия · не е фин. съвет</i>"]
    return "\n".join(L)


def _exit_msg(kind, tr, price_hit, when, via, gap, spot=None, next_line="", dec=2):
    """Изход v5: час на РЕАЛНИЯ удар, готови числа, какво остава, двете сметки."""
    d = tr["direction"].upper(); e = tr["entry"]
    sym = tr.get("sym", "XAUUSD"); metal = "ЗЛАТО" if sym == "XAUUSD" else "СРЕБРО"
    lv = tr["levels"]; hit = tr.get("hit", {})
    sign = 1 if tr["direction"] == "long" else -1
    dol = (price_hit - e) * sign
    if abs(dol) < 0.005:                 # безрисков стоп на входа → «0.00», не «-0.00»
        dol = 0.0
    via_txt = {"бар": f"ударен в {_sofia(when)} София (по бара)",
               "спот": f"ударен СЕГА ({_sofia(when)} София, по живия спот)",
               "време": "времеви изход"}.get(via, via)
    gap_txt = " · <b>изпълнено с гап</b> — реалната цена прескочи нивото" if gap else ""
    heads = {"tp1": "✅ ТП1 ПОСТИГНАТ", "tp2": "✅✅ ТП2 ПОСТИГНАТ", "tp3": "🏆 ТП3 — ПЪЛЕН ТЕЙК",
             "sl": "🛑 СТОП", "flip": "🔄 ПОСОКАТА СЕ ОБЪРНА — затворено", "time": "⏰ ВРЕМЕВИ ИЗХОД"}
    opened_txt = f" <i>(сделка от {_sofia(tr['opened'])} София)</i>" if tr.get("opened") else ""   # Г7
    L = [f"{heads.get(kind, kind)} · {metal} {d}{opened_txt}", "─────────────────",
         f"{via_txt}{gap_txt}",
         f"Вход <code>{_fmt(e, dec)}</code> → <code>{_fmt(price_hit, dec)}</code> = <b>{dol:+.2f}$/oz</b>"]
    if kind == "tp1":
        L.append(f"→ Премести стопа на <code>{_fmt(e, dec)}</code> (входа) — безрискова сделка.")
        L.append(f"Остават: ТП2 <code>{_fmt(lv['tp2'], dec)}</code> · ТП3 <code>{_fmt(lv['tp3'], dec)}</code>")
    elif kind == "tp2":
        L.append(f"→ 2/3 прибрани. Остава: ТП3 <code>{_fmt(lv['tp3'], dec)}</code> (стопът стои на входа).")
    elif kind in ("tp3", "sl", "flip", "time"):
        # двете сметки (Ф9.6-предварително): цяла позиция + съветът 1/3
        thirds = 0.0
        parts = {"tp1": lv["tp1"], "tp2": lv["tp2"]}
        n_hit = 0
        for k2, px in parts.items():
            if hit.get(k2) and k2 != kind:
                thirds += (px - e) * sign / 3.0; n_hit += 1
        thirds += dol * (3 - n_hit) / 3.0
        L.append(f"Сметка: цяла позиция <b>{dol:+.2f}$/oz</b> · по съвета 1/3 на ТП ≈ <b>{thirds:+.2f}$/oz</b>")
        if kind == "sl" and any(hit.get(k2) for k2 in ("tp1", "tp2")):
            L.append("<i>(преди стопа удари " + ", ".join(k2.upper() for k2 in ("tp1", "tp2") if hit.get(k2)) + " — затова 1/3 сметката е по-добра)</i>")
    if spot:
        L.append(f"Спот сега: <code>{_fmt(spot['mid'], dec)}</code>")
    if next_line:
        L.append(f"<b>НОВО ВЛИЗАНЕ:</b> {next_line}")
    L.append(f"<i>{VERSION} · хартия · не е съвет</i>")
    return "\n".join(L)


def _ma_alert_msg(direction, ma_name, price, mb, macro):
    dcol = "🟢" if direction == "long" else "🔴"
    verb = "ОТСКОК от" if direction == "long" else "ОТХВЪРЛЯНЕ от"
    lv = _levels(round(price, 2), direction)
    L = [f"{dcol} <b>ИНФО-АЛАРМА · {verb} {ma_name.upper()}</b> (злато)",
         "─────────────────",
         f"Цена <code>{_fmt(price)}</code> докосна {ma_name.upper()} и се {'отблъсна' if direction=='long' else 'отхвърли'}.",
         f"Исторически: <b>{mb['win']}%</b> ({mb['net']:+}$/oz, n={mb['n']})",
         f"Ориентир при вход: ТП1 <code>{_fmt(lv['tp1'])}</code> · СТОП <code>{_fmt(lv['sl'])}</code>",
         "<i>ИНФОРМАТИВНА аларма — ботът НЕ я следи като сделка. Не е съвет.</i>"]
    return "\n".join(L)


def _weekly(path, date=None, notes=None):
    try:
        p = Path(path)
        w = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        if w and date and w.get("week_of"):                    # Ф8.7: остарял контекст
            try:
                age = (pd.Timestamp(date) - pd.Timestamp(w["week_of"])).days
                if age > 8:
                    if notes is not None:
                        notes.append(f"седмичният контекст е на {age} дни — скрит")
                    return None
            except Exception:
                pass
        return w
    except Exception:
        return None


def _daily_ctx(path, date, notes):
    """Ф4: дневният контекст (Кибер Алфа / анализ на деня). Валиден за ДНЕС —
    Б8: сравнява с КАЛЕНДАРНАТА дата ИЛИ датата на бара (рано сутрин барът още е вчерашен)."""
    try:
        p = Path(path)
        if not p.exists():
            return None
        d = json.loads(p.read_text(encoding="utf-8"))
        cal = str(datetime.now(timezone.utc).date())
        if str(d.get("date")) not in (str(date), cal):
            notes.append("дневният контекст е за друга дата — пропуснат")
            return None
        return d
    except Exception:
        notes.append("дневният контекст не се чете — пропуснат")
        return None


def _event_shield(ctx, now_utc):
    """Ф4.3: (активен_щит, етикет). Щит ±20 мин около събитие impact=high;
    етикет и за предстоящо събитие до 60 мин (само предупреждение)."""
    if not ctx:
        return False, None
    from zoneinfo import ZoneInfo
    try:
        now_s = datetime.fromisoformat(str(now_utc)).replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Europe/Sofia"))
        for ev in ctx.get("events", []):
            t = str(ev.get("time_sofia", ""))
            if ":" not in t:
                continue
            hh, mm = t.split(":")[:2]
            evt = now_s.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            dmin = (now_s - evt).total_seconds() / 60
            hi = str(ev.get("impact", "")).lower() == "high"
            if hi and -20 <= dmin <= 20:
                return True, f"{t} {ev.get('name', 'събитие')}"
            if hi and -60 <= dmin < -20:
                return False, f"предстои {t} {ev.get('name', 'събитие')}"
        return False, None
    except Exception:
        return False, None


def _digest_msg(out, date, trade, s_trade, spot_g, spot_s, guard, weekly_part=False):
    """Ф5+Ф8.4: вечерна равносметка (и жизнен пулс). Петък → +седмичен раздел."""
    def _rows(fname, pred):
        f = out / fname
        if not f.exists():
            return []
        rows = []
        for ln in f.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
                if pred(r):
                    rows.append(r)
            except Exception:
                pass
        return rows
    today_runs = _rows("live_journal.jsonl", lambda r: r.get("date") == date)
    sent_today = _rows("sent_log.jsonl", lambda r: str(r.get("utc", ""))[:10] == date)
    kinds = {}
    for r in sent_today:
        k = r.get("tag", "?").split(":")[0]
        kinds[k] = kinds.get(k, 0) + 1
    L = [f"🌙 <b>ВЕЧЕРНА РАВНОСМЕТКА · {date}</b>", "─────────────────",
         f"Ботът е ЖИВ: {len(today_runs)} пускания днес · пратени {len(sent_today)} съобщения"
         + (f" ({', '.join(f'{k}×{v}' for k, v in kinds.items())})" if kinds else "")]
    for nm, tr, sp, dec in (("Злато", trade, spot_g, 2), ("Сребро", s_trade, spot_s, 3)):
        if tr:
            pl = ((sp["mid"] - tr["entry"]) if tr["direction"] == "long" else (tr["entry"] - sp["mid"])) if sp else None
            hits = ", ".join(k.upper() for k in ("tp1", "tp2") if tr.get("hit", {}).get(k)) or "още нищо"
            L.append(f"{nm}: {tr['direction'].upper()} от <code>{tr['entry']:,.{dec}f}</code> · ударени: {hits}"
                     + (f" · в момента {pl:+.2f}$/oz" if pl is not None else ""))
        else:
            L.append(f"{nm}: няма отворена сделка")
    # Д1: злато+сребро в ЕДНА посока = корелиран двоен риск (~3.5-4%, не 2%+2%)
    if trade and s_trade and trade["direction"] == s_trade["direction"]:
        L.append(f"⚠️ <b>Двете сделки са {trade['direction'].upper()}</b> — злато и сребро вървят заедно "
                 f"(corr ~0.8) → реалният риск е ~2× един залог, не два независими. Малък размер.")
    stops = guard.get("long", 0) + guard.get("short", 0) + guard.get("s_long", 0) + guard.get("s_short", 0)
    if stops:
        L.append(f"Стопове днес: {stops} (пазачът пази при 2 в посока)")
    if weekly_part:
        week_runs = _rows("sent_log.jsonl", lambda r: True)[-500:]
        wk = {}
        for r in week_runs:
            d = str(r.get("utc", ""))[:10]
            if d and (pd.Timestamp(date) - pd.Timestamp(d)).days < 5:
                k = r.get("tag", "?").split(":")[0]; wk[k] = wk.get(k, 0) + 1
        L += ["─────────────────", "📅 <b>СЕДМИЦАТА:</b> " + (", ".join(f"{k}×{v}" for k, v in wk.items()) or "тиха")]
    nxt = "понеделник" if weekly_part else "утре"      # Г8: петък → понеделник (събота няма карта)
    L.append(f"<i>Следваща дневна карта: {nxt} сутрин · {VERSION}</i>")   # Г6: без фалшивия точен час
    return "\n".join(L)


def _status_msg(board, new_dir, trade, s_trade, spot_g, spot_s, basis_g, basis_s, guard, shield, date, macro):
    """Ф9.8: статус-карта при поискване (ръчно пускане със status=yes)."""
    L = [f"ℹ️ <b>СТАТУС · {date} · {_sofia()} София</b>", "─────────────────",
         f"Посока: {new_dir or 'няма'} · съгласие: " + "/".join(f"{d}:{t}" for _, d, _, t, _ in board[:1])
         + f" · макро {sum(macro.values())}/3" + (" · US-ЩИТ активен" if shield else "")]
    for nm, tr, sp, dec in (("🥇", trade, spot_g, 2), ("🥈", s_trade, spot_s, 3)):
        if tr:
            lv = tr["levels"]; hit = tr.get("hit", {})
            def hm(k): return "✅" if hit.get(k) else f"<code>{lv[k]:,.{dec}f}</code>"
            pl = ((sp["mid"] - tr["entry"]) if tr["direction"] == "long" else (tr["entry"] - sp["mid"])) if sp else None
            L.append(f"{nm} {tr['direction'].upper()} от <code>{tr['entry']:,.{dec}f}</code> · ТП1 {hm('tp1')} ТП2 {hm('tp2')} ТП3 {hm('tp3')} СТОП <code>{lv['sl']:,.{dec}f}</code>"
                     + (f" · сега {pl:+.2f}$/oz" if pl is not None else ""))
        else:
            L.append(f"{nm} няма отворена сделка")
    if spot_g:
        L.append(f"Спот злато <code>{spot_g['mid']:,.2f}</code> (базис {basis_g:+.2f})"
                 + (f" · сребро <code>{spot_s['mid']:,.3f}</code>" if spot_s else ""))
    L.append(f"<i>{VERSION} · хартия · не е съвет</i>")
    return "\n".join(L)


# ---------- следене v5: спот-леджър, барове през базиса + жив спот ----------
def track_trade(trade, bars, basis, now_price, now_utc, spot=None):
    """bars = фючърсни 5м (пълният път, ~10 мин назад), превеждани в спот
    чрез базиса. spot = живата цена (моментално, Ф7.1). Гап → реална цена.
    Връща (trade|None, events); event = (kind, price, when, via, gap)."""
    events = []
    if trade is None:
        return None, events
    since = pd.Timestamp(trade.get("checked", trade["opened"]))
    lv = trade["levels"]; d = trade["direction"]
    idx = bars.index if bars is not None else []
    processed = []                                   # M1: следим кои барове реално обходихме
    for ts in idx:
        if ts <= since:
            continue
        hi = float(bars.loc[ts, "High"]) - basis
        lo = float(bars.loc[ts, "Low"]) - basis
        op = float(bars.loc[ts, "Open"]) - basis
        if pd.isna(hi) or pd.isna(lo) or pd.isna(op):  # M2: бар с NaN OHLC крие удар → пропусни
            continue
        processed.append(ts)
        sl_hit = (lo <= lv["sl"]) if d == "long" else (hi >= lv["sl"])
        # BE-стоп (sl=вход след ТП1) НЕ бива да пали на бара, който УДАРИ ТП1, при
        # преразглеждане (M1 оставя последния бар преразглеждаем) — иначе широк ТП1-бар
        # с фитил под входа затваря фалшиво печелившата сделка на нула.
        if sl_hit and lv["sl"] == trade["entry"] and trade.get("be_since") and str(ts) <= trade["be_since"]:
            sl_hit = False
        if sl_hit:                                   # консервативно: стопът първи
            gap = (op <= lv["sl"]) if d == "long" else (op >= lv["sl"])
            px = round(op, 3) if gap else lv["sl"]
            events.append(("sl", px, str(ts), "бар", gap)); trade["status"] = "closed_sl"
            break
        for k in ("tp1", "tp2", "tp3"):
            if not trade["hit"].get(k):
                tp_hit = (hi >= lv[k]) if d == "long" else (lo <= lv[k])
                if tp_hit:
                    gap = (op >= lv[k]) if d == "long" else (op <= lv[k])
                    px = round(op, 3) if gap else lv[k]
                    trade["hit"][k] = True; events.append((k, px, str(ts), "бар", gap))
                    if k == "tp1":                        # картата обещава «стоп на входа» → ПРАВИМ го
                        lv["sl"] = trade["entry"]         # иначе изходната сметка лъже (безрисково ≠ −$20)
                        trade["be_since"] = str(ts)       # BE-стопът важи от СЛЕДВАЩ бар (не този)
                    if k == "tp3":
                        trade["status"] = "closed_tp3"
        if trade.get("status", "open") != "open":
            break
    # Ф7.1 · МОМЕНТАЛНО: живият спот СЕГА (баровете са до 10-15 мин назад)
    if trade.get("status", "open") == "open" and spot:
        p = spot["mid"]
        if (p <= lv["sl"]) if d == "long" else (p >= lv["sl"]):
            events.append(("sl", lv["sl"], now_utc, "спот", False)); trade["status"] = "closed_sl"
        else:
            for k in ("tp1", "tp2", "tp3"):
                if not trade["hit"].get(k):
                    if (p >= lv[k]) if d == "long" else (p <= lv[k]):
                        trade["hit"][k] = True; events.append((k, lv[k], now_utc, "спот", False))
                        if k == "tp1":                    # стоп на входа (както картата казва)
                            lv["sl"] = trade["entry"]
                            trade["be_since"] = now_utc   # BE-стопът важи от следващ бар/тик
                        if k == "tp3":
                            trade["status"] = "closed_tp3"
    if trade.get("status", "open") == "open":
        age = (pd.Timestamp(now_utc) - pd.Timestamp(trade["opened"])).days
        if age >= 30:
            events.append(("time", now_price, now_utc, "време", False)); trade["status"] = "closed_time"
    # M1: за ОТВОРЕНА сделка НЕ напредвай checked отвъд ПРЕДПОСЛЕДНИЯ обходен бар —
    # последният може да е още оформящ се (yfinance връща частичния бар); остави го
    # преразглеждаем следващия рън, когато е завършен с пълния си диапазон. Идемпотентно:
    # маркиран ТП се пропуска (if not hit), а СТОП затваря сделката (не се пре-следи).
    if trade["status"] == "open":
        if len(processed) >= 2:
            trade["checked"] = str(processed[-2])
        # 0-1 нови барове → не мърдай checked (преразгледай ги наново следващия рън)
    elif processed:
        trade["checked"] = str(processed[-1])         # затворена — сделката тъй или иначе се трие
    return (None if trade["status"] != "open" else trade), events


def _migrate_trade(trade, basis, dec=2, notes=None):
    """v4 сделка (фючърсни нива) → спот-леджър: изместване с базиса, еднократно.
    Б5: мигрира САМО при ПОТВЪРДЕН базис (≠0). При базис 0 (спотът недостъпен този
    рън) отлага — иначе би маркирала «spot» с фючърсни нива необратимо."""
    if trade is None or trade.get("ledger") == "spot":
        return trade
    if not basis:                                        # базисът не е сиден този рън → чакай
        if notes is not None:
            notes.append("миграция на сделката отложена — базисът още не е потвърден")
        return trade
    if not trade.get("v2"):
        trade["checked"] = trade["opened"]; trade["v2"] = True
    trade["entry"] = round(trade["entry"] - basis, dec)
    trade["levels"] = {k: round(v - basis, dec) for k, v in trade["levels"].items()}
    trade["ledger"] = "spot"
    return trade


# ---------- пощенска кутия (Ф8.1): съобщение не се губи никога ----------
def _send_raw(text):
    tok = os.environ.get("TELEGRAM_TOKEN"); ch = os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not ch:
        return "DRY_RUN (няма токен)"
    url = f"https://api.telegram.org/bot{tok}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": ch, "text": text[:4000], "parse_mode": "HTML"}).encode()
    last = ""
    for _ in range(2):                                    # 2 опита на пускане
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15) as r:
                return f"SENT ({r.status})"
        except urllib.error.HTTPError as e:               # HTTP статус от Телеграм
            # 429 (rate-limit при catch-up burst), 408 (timeout), 425 (too-early) = МЕКИ →
            # ретрай вечно. Инак 3 поредни 429 триеха реална карта с ПЕРФЕКТЕН HTML (🔴).
            if e.code in (429, 408, 425) or e.code >= 500:
                last = f"SEND_FAILED: HTTP {e.code} (rate/timeout/server)"
                import time; time.sleep(3)
            elif 400 <= e.code < 500:                      # 400/403/404/413 = истински «отровни»
                return f"HARD_FAIL:{e.code}"               # (развален HTML/забранен/твърде голям)
            else:
                last = f"SEND_FAILED: HTTP {e.code}"
                import time; time.sleep(3)
        except Exception as e:                            # мрежа/таймаут: МЕК провал → ретрай вечно
            last = f"SEND_FAILED: {str(e)[:80]}"
            import time; time.sleep(3)
    return last


POISON_HARD_FAILS = 3     # Б6: толкова ТВЪРДИ (4xx) провала = отровно (развален HTML) → хвърли
def _outbox_flush(out_dir, new_msgs, statuses, dry=False):
    """Стари неизпратени първо, после новите. Провалените остават за следващия рън.
    Връща set() с ТАГОВЕТЕ, реално пратени този рън (за да гейтнем записа — Б1).
    Б6: всяко съобщение носи first_ts + attempts (за журнал) + hard_fails; отровно се
    хвърля САМО при hard_fails≥3 (твърди 4xx). Мек/429/мрежов провал → ретрай вечно."""
    ob_f = out_dir / "outbox.jsonl"
    now_iso = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
    pending = []
    if ob_f.exists():
        for ln in ob_f.read_text(encoding="utf-8").splitlines():
            try:
                pending.append(json.loads(ln))
            except Exception:
                pass
    for t, m in new_msgs:
        pending.append({"tag": t, "text": m, "first_ts": now_iso, "attempts": 0})
    # НАХОДКА B: signal/s-signal = «намерение да отвориш сделка СЕГА». Пренесен от минал рън
    # и НЕ регенериран този рън → условията са се сменили (щит/пауза/уикенд/F1) → изхвърли го,
    # инак картата стига до човека, но сделка НЕ се отваря/следи (осиротяла карта).
    fresh_tags = {t for t, _ in new_msgs}
    pending = [m for m in pending
               if not (m["tag"] in ("signal", "s-signal") and m["tag"] not in fresh_tags
                       and m.get("first_ts", now_iso) < now_iso)]
    # R1: дедуп по таг за ПРЕПОВТАРЯЩИТЕ се карти (signal/s-signal/digest/status) —
    # при срив на Телеграм не трупай N копия; пази само НАЙ-НОВОТО (последната цена).
    DEDUP = ("signal", "s-signal", "digest", "status")
    seen_last = {}
    for i, msg in enumerate(pending):
        if msg["tag"] in DEDUP:
            seen_last[msg["tag"]] = i          # последният индекс за тоя таг
    pending = [m for i, m in enumerate(pending)
               if m["tag"] not in DEDUP or seen_last[m["tag"]] == i]
    remaining = []; sent_tags = set()
    for msg in pending:
        msg.setdefault("first_ts", now_iso); msg["attempts"] = msg.get("attempts", 0) + 1
        # ОТРОВНО = само ТВЪРДИ провали (развален HTML, 4xx); мрежов срив НЕ брои →
        # легитимен изход не се хвърля при дълъг Телеграм срив (краен-случай находка).
        if msg.get("hard_fails", 0) >= 3:
            statuses.append(f"{msg['tag']}=ОТРОВНО-ХВЪРЛЕНО (развален HTML)")
            continue
        if dry:
            statuses.append(f"{msg['tag']}=DRY"); sent_tags.add(msg["tag"]); continue
        st = _send_raw(msg["text"])
        statuses.append(f"{msg['tag']}={st}")
        if st.startswith("SENT"):
            sent_tags.add(msg["tag"])
            with (out_dir / "sent_log.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"utc": now_iso, "tag": msg["tag"], "text": msg["text"]},
                                    ensure_ascii=False) + "\n")
        elif st.startswith("HARD_FAIL"):
            msg["hard_fails"] = msg.get("hard_fails", 0) + 1
            remaining.append(msg)                         # ще опита още 2 пъти, после отровно
        elif not st.startswith("DRY_RUN"):
            remaining.append(msg)                         # мек провал → ретрай вечно (не брои за отровно)
    ob_f.write_text("\n".join(json.dumps(m, ensure_ascii=False) for m in remaining), encoding="utf-8")
    return sent_tags


# ================================================================== MAIN ===
def main():
    ap = argparse.ArgumentParser(description=f"AERO LIVE bot {VERSION}")
    ap.add_argument("--out", default="live"); ap.add_argument("--stats", default="backtest_stats.json")
    ap.add_argument("--balance", type=float, default=float(os.environ.get("BALANCE", 1000)))   # Ф8.6
    ap.add_argument("--risk", type=float, default=float(os.environ.get("RISK_PCT", 2)))
    ap.add_argument("--send", action="store_true"); ap.add_argument("--force", action="store_true")
    ap.add_argument("--weekly", default="weekly_context.json")
    ap.add_argument("--daily", default="daily_context.json")                                   # Ф4
    ap.add_argument("--status", action="store_true")                                           # Ф9.8
    args = ap.parse_args()
    out = Path(args.out); (out / "data").mkdir(parents=True, exist_ok=True)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="minutes")
    notes = []

    import time
    print(f"AERO {VERSION} · дърпам дневни данни...")
    gold_d = _yf("GC=F", "3y", "1d"); time.sleep(1.2)
    gdx_d = _yf("GDX", "2y", "1d"); time.sleep(1.2)
    dxy_d = _yf("DX-Y.NYB", "2y", "1d"); time.sleep(1.2); rr = _rates()
    for d in (gold_d, gdx_d, dxy_d):
        d.index = d.index.normalize()
    # Ф9.1 · ЗАМРАЗЕНИ РЕФЕРЕНЦИИ (F19-Т1: 39% от стъпките сменяха клас!):
    # средните/макрото се смятат до ВЧЕРАШНИЯ завършен ден — както в backtest-а.
    today_n = pd.Timestamp(datetime.now(timezone.utc).date())
    def _hist(df):
        return df.iloc[:-1] if len(df) > 1 and df.index[-1] >= today_n else df
    gold_h, gdx_h, dxy_h = _hist(gold_d), _hist(gdx_d), _hist(dxy_d)
    # Б4: недостатъчна история → NaN средни → фалшив ПРЕМИУМ на боклук-данни. Въздържане.
    enough_history = len(gold_h) >= 200
    if not enough_history:
        notes.append(f"недостатъчна история ({len(gold_h)} дневни бара < 200) — сигналът е ненадежден, въздържане")
    macro = _macro(gold_h, gdx_h, dxy_h, rr); refs = _refs(gold_h)
    regime = _regime(gold_h, gold_today=gold_d)
    regime["streaks"] = _streaks(gold_h, gdx_h, dxy_h, rr)

    # Ф7.2 · ОПТИМИЗАЦИЯ: 2 интрадей пакета вместо 6. Всички ТФ се смятат от
    # 1м (7д) + 5м (60д) поток — _scores ползва само ПОСЛЕДНИЯ бар на всеки ТФ,
    # а 15м/30м/1час/4час барове = ресемпъл на 5м (същите UTC граници като Yahoo).
    # Проверено бит-идентично срещу старите отделни пакети преди качване.
    frames = {"1ден": gold_d}
    m1 = m5 = None
    print("дърпам 1мин (7d)...")
    try:
        m1 = _yf("GC=F", "7d", "1m")
    except Exception as e:
        print(f"  1мин пропуснат ({type(e).__name__})")
    time.sleep(1.2)
    print("дърпам 5м (60d)...")
    try:
        m5 = _yf("GC=F", "60d", "5m")
    except Exception as e:
        print(f"  5м пропуснат ({type(e).__name__})")
    time.sleep(1.2)
    src = m5 if m5 is not None else m1                    # резерва: 1м покрива 7 дни
    frames["1мин"] = m1 if m1 is not None else m5
    frames["5м"] = m5 if m5 is not None else m1
    for lbl, rule in (("15м", "15min"), ("30м", "30min"), ("1час", "60min"), ("4час", "4h")):
        try:
            frames[lbl] = src.resample(rule).agg(Open=("Open", "first"), High=("High", "max"),
                                                 Low=("Low", "min"), Close=("Close", "last")).dropna() \
                          if src is not None else None
        except Exception:
            frames[lbl] = None

    fine = frames.get("1мин") if frames.get("1мин") is not None else frames.get("5м")
    bar_price = float(fine["Close"].iloc[-1]) if fine is not None else float(gold_d["Close"].iloc[-1])
    bar_ts = fine.index[-1] if fine is not None else None
    try:                                                 # W-провали: повреден stats да НЕ убива бота тихо
        stats = json.loads(Path(args.stats).read_text(encoding="utf-8")) if Path(args.stats).exists() else {}
    except Exception:
        stats = {}; notes.append("backtest_stats.json не се чете — работя без историческите числа")

    # датата: САМО НАПРЕД (Ф8.2/П9)
    meta = _load_state(out / "meta.json", {})
    date_raw = str(gold_d.index[-1].date())
    date = max(date_raw, meta.get("date", date_raw))
    meta["date"] = date
    # Ф8.8: месечна ротация на журнала и следата
    mon = date[:7]
    if meta.get("month") and meta["month"] != mon:
        arch = out / "archive"; arch.mkdir(exist_ok=True)
        for fn in ("live_journal.jsonl", "sent_log.jsonl"):
            f = out / fn
            if f.exists():
                try:
                    f.rename(arch / f"{fn.rsplit('.', 1)[0]}-{meta['month']}.jsonl")
                except Exception:
                    pass
    meta["month"] = mon
    weekend = _market_closed(now_utc)                    # A3: по UTC-час, не по деня

    # A6: застоял бар — данните стари, а ботът жив (празник/тънка сесия)
    bar_age_min = None
    if bar_ts is not None:
        try:
            bar_age_min = round((pd.Timestamp(now_utc) - pd.Timestamp(bar_ts)).total_seconds() / 60, 1)
        except Exception:
            pass
    stale_bar = bar_age_min is not None and bar_age_min > 30 and not weekend
    if stale_bar:
        notes.append(f"застоял бар: {bar_age_min:.0f} мин стар (празник/тънка сесия?)")

    # спот + базис + санити (Ф8.3 / Ф9.2 / Ф9.7 / A1 / A4 / A5)
    # РЕД: суров спот → базис (детекцията на роловър иска суровия!) → санити срещу бар−базис
    rng_g = _bar_range(fine)                             # A4: диапазон за динамичния праг
    raw_g = _spot("XAU/USD", market_closed=weekend)
    jump_g = abs(raw_g["mid"] - meta["last_spot_g"]) if (raw_g and meta.get("last_spot_g")) else None  # T3
    if raw_g:
        meta["last_spot_g"] = raw_g["mid"]
    basis_g = _basis_update(meta, "basis_g", raw_g, bar_price, notes, cap=40.0, now_utc=now_utc)
    spot_g = _spot_sane(raw_g, bar_price - basis_g, 8.0, bar_rng=rng_g, spot_jump=jump_g)
    spot_rejected_g = bool(raw_g is not None and spot_g is None)   # A2: суровият беше жив, санитито го отряза
    sd = s5 = spot_s = None; basis_s = meta.get("basis_s", 0.0)
    print(f"  спот: злато {spot_g['mid'] if spot_g else '— (санити/недостъпен)'} · базис {basis_g:+.2f}"
          + (f" · бар {bar_age_min:.0f}мин" if bar_age_min else ""))

    # бърз пазар (за съвета)
    fast_g = None
    try:
        if fine is not None and len(fine) > 11:
            d10 = abs(float(fine["Close"].iloc[-1]) - float(fine["Close"].iloc[-11]))
            fast_g = round(d10, 1) if d10 >= 10 else None
    except Exception:
        pass

    # щит: US-прозорецът (ET) + събитие от дневния контекст (Ф4.3)
    daily_ctx = _daily_ctx(args.daily, date, notes)
    ev_shield, ev_label = _event_shield(daily_ctx, now_utc)
    shield = _in_shield(now_utc) or ev_shield
    guard = _load_state(out / "guard.json", {})
    if guard.get("date") != date:
        guard = {"date": date, "long": 0, "short": 0, "s_long": 0, "s_short": 0}

    # цената за човека: живият спот; резерва — барът минус базиса
    price_user = spot_g["mid"] if spot_g else round(bar_price - basis_g, 2)

    # === 1) СЛЕДЕНЕ (спот-леджър) ===
    tr_f = out / "open_trade.json"
    trade = _load_state(tr_f, None)
    trade = _migrate_trade(trade, basis_g, notes=notes)
    exit_msgs = []          # (tag, text, kind, direction)
    # A2/Б3: в какъв режим следим — с барове или само спот (тихо влошаване)
    track_mode = "bars+spot" if frames.get("5м") is not None else ("spot-only" if spot_g else "skipped")
    if track_mode != "bars+spot" and trade:
        notes.append(f"следене {track_mode} — 5м потокът липсва")
    if trade:
        trade_obj = copy.deepcopy(trade)                   # Д3: снимка, която track_trade няма да мутира
        trade, events = track_trade(trade, frames.get("5м"), basis_g, price_user, now_utc, spot=spot_g)
        cum_hit = dict(trade_obj["hit"])                   # попадения от МИНАЛИ рънове
        for kind, px, when, via, gap in events:
            if kind in ("tp1", "tp2", "tp3"):              # това попадение стана ТОЗИ рън → трупай
                cum_hit[kind] = True
            # F3: брой само РЕАЛЕН стоп; безрисковият (на входа, след ТП1) е печеливш изход
            if kind == "sl" and abs(px - trade_obj["entry"]) > 0.05:
                guard[trade_obj["direction"]] = guard.get(trade_obj["direction"], 0) + 1
            # краен-случай: подай снимка на КУМУЛАТИВНИТЕ попадения ДО този изход (не застоялата
            # отпреди ръна) → 1/3 сметката е вярна и при ТП1+ТП2+СТОП в ЕДИН рън (catch-up burst).
            obj = dict(trade_obj); obj["hit"] = dict(cum_hit)
            exit_msgs.append(("exit:" + kind, (kind, obj, px, when, via, gap), kind, trade_obj["direction"]))

    # === 2) СИГНАЛ на 7-те ТФ (ядрото — непипнато) ===
    board = []
    for lbl, *_ in TFS:
        df = frames.get(lbl)
        if df is None or len(df) == 0:
            board.append((lbl, "wait", 0, "weak", "ЧАКАЙ")); continue
        ls, ss, _c = _scores(df, refs, macro)
        board.append((lbl,) + _resolve(ls, ss, macro))
    actionable = [b for b in board if b[1] != "wait" and b[3] != "weak"] if enough_history else []
    rank = {"premium": 3, "strong": 2, "medium": 1, "weak": 0}
    best = max(board, key=lambda x: (rank[x[3]], x[2])) if actionable else board[0]
    new_dir = best[1] if actionable else None
    agree_n = sum(1 for b in board if b[1] == new_dir and b[3] != "weak") if new_dir else 0

    # обръщане: САМО ПРЕМИУМ насрещен затваря сделката (F19-Т3: −0.31 срещу −0.42)
    if trade and new_dir and trade["direction"] != new_dir and best[3] == "premium":
        exit_msgs.append(("exit:flip", ("flip", dict(trade), price_user, now_utc, "спот" if spot_g else "бар", False),
                          "flip", trade["direction"]))
        trade = None

    # === 3) БЕЗ СПАМ + защити (Ф2 / Ф9.3) ===
    weekly = _weekly(args.weekly, date=date, notes=notes)
    last = _load_state(out / "last_sent.json", {})
    key = date + "|" + ";".join(f"{l}:{d}:{t}" for l, d, s, t, _ in board if t != "weak" and d != "wait")
    mins_since = None
    if last.get("sent_utc"):
        try:
            mins_since = (pd.Timestamp(now_utc) - pd.Timestamp(last["sent_utc"])).total_seconds() / 60
        except Exception:
            pass
    tier_up = new_dir and rank.get(best[3], 0) > rank.get(last.get("tier", "weak"), 0) and new_dir == last.get("dir")
    cool_ok = (mins_since is None or mins_since >= 45
               or (new_dir is not None and new_dir != last.get("dir") and mins_since >= 15)
               or tier_up)                                # ъпгрейд на класа минава паузата (Ф9.3)
    should_sig = args.force or (bool(actionable) and (last.get("key") != key or tier_up) and cool_ok)

    # ре-влизане след приключена сделка — по F18 правилата
    closed_kinds = [k for _, _, k, _ in exit_msgs if k in ("tp3", "sl", "time", "flip")]
    reentry = False
    if closed_kinds and actionable and trade is None:
        ok_re, why_re = _reentry_verdict(new_dir, regime["streaks"].get(new_dir, 0), shield, guard.get(new_dir, 0))
        if ok_re and cool_ok:
            should_sig = True; reentry = True
        else:
            reentry = False
            # НАХОДКА 2: сделката приключи (вкл. флип), но ре-влизането е ОТКАЗАНО (F18)
            # → НЕ пращай нова карта на насрещната посока (иначе журналът си противоречи).
            should_sig = False
            notes.append(f"ре-влизане отказано: {why_re}" if why_re else "ре-влизане: пауза")
    # нов вход в US-щита за шорт → отлага се (картата ще дойде след прозореца)
    if should_sig and new_dir == "short" and shield and trade is None:
        should_sig = False
        notes.append(f"шорт карта отложена: US-щит ({_shield_sofia_label()})")
    if should_sig and new_dir and guard.get(new_dir, 0) >= 2 and trade is None:
        should_sig = False
        notes.append("карта спряна: стоп-пазач (2 стопа днес)")
    if should_sig and weekend:
        should_sig = False
        notes.append("уикенд — картите почиват до понеделник")
    # F1 (🔴): ОТВОРЕНА сделка + НЕПРЕМИУМ насрещен борд (флипът на 1005 не пали) →
    # ЗАДРЪЖ старата, НЕ отваряй насрещна. Иначе живата позиция се презаписва ТИХО,
    # без изходно съобщение — потребителят никога не научава изхода ѝ.
    if should_sig and trade is not None and new_dir and trade["direction"] != new_dir:
        should_sig = False
        notes.append(f"насрещен непремиум {new_dir} при отворена {trade['direction']} — задържам старата, без нова карта")

    streak_n = regime["streaks"].get(new_dir, 0) if new_dir else 0
    advice_txt, _adv_ok = _advice_entry(new_dir, streak_n, stats, fast_g, shield, guard.get(new_dir or "", 0),
                                        sym="XAUUSD", stale_price=(spot_g is None)) if new_dir else ("", False)

    # честота: информативна «НЕ/ИЗЧАКАЙ» карта (adv_ok=False, сделка НЕ се отваря) да НЕ минава
    # по бързата 15-мин flip-лента — само по пълната 45-мин пауза. Инак на хаотичен ден бордът
    # флика посока и трупа до ~4 «не влизай» карти/час. Реалните входове (adv_ok) пазят flip-лентата.
    if should_sig and not args.force and not _adv_ok and not tier_up \
       and not (mins_since is None or mins_since >= 45):
        should_sig = False
        notes.append("информативна «НЕ» карта по flip-лентата — заглушена (не е реален вход)")

    sig_payload = None
    if should_sig and actionable:
        entry_user = _entry_side(spot_g, new_dir) if spot_g else price_user
        lv_user = _levels(round(entry_user, 2), new_dir)
        sig_payload = (entry_user, lv_user)

    # === 4) MA-аларми (инфо, без следене — Н2 етикет) ===
    ma_f = out / "ma_alerts.json"
    ma_sent = _load_state(ma_f, {})
    ma_alerts = []
    for mkey, flag in (regime.get("ma") or {}).items():
        if not flag:
            continue
        dirn, ma_name = mkey.split("_", 1)
        tag = f"{date}|{mkey}"
        if ma_sent.get(tag):
            continue
        mb = stats.get("ma_bounce", {}).get(dirn, {}).get(ma_name, {})
        if mb.get("n"):
            ma_alerts.append((tag, _ma_alert_msg(dirn, ma_name, price_user, mb, macro)))

    # === 5) 🥈 СРЕБРО — същият конвейер, изолиран ===
    silver_new_msgs = []    # (tag, text)
    s_tr_f = out / "silver_trade.json"; s_state_f = out / "silver_sent.json"
    silver_trade_new = None; s_key = None; s_dir = None; s_tk = None; silver_ok = False; basis_s = meta.get("basis_s", 0.0)
    try:
        print("дърпам сребро (SI=F)...")
        sdd = _yf("SI=F", "2y", "1d"); time.sleep(1.2)
        s5 = _yf("SI=F", "60d", "5m")
        sdd.index = sdd.index.normalize()
        s_bar = float(s5["Close"].iloc[-1])
        rng_s = _bar_range(s5)
        raw_s = _spot("XAG/USD", market_closed=weekend)
        jump_s = abs(raw_s["mid"] - meta["last_spot_s"]) if (raw_s and meta.get("last_spot_s")) else None
        if raw_s:
            meta["last_spot_s"] = raw_s["mid"]
        basis_s = _basis_update(meta, "basis_s", raw_s, s_bar, notes, cap=3.0, now_utc=now_utc)
        spot_s = _spot_sane(raw_s, s_bar - basis_s, 0.30, bar_rng=rng_s, spot_jump=jump_s)
        s_price_user = spot_s["mid"] if spot_s else round(s_bar - basis_s, 3)
        s_refs = _refs(sdd)
        ls_s, ss_s, _ = _scores(s5, s_refs, macro)
        s_dir, s_score, s_tk, s_tn = _resolve(ls_s, ss_s, macro)
        s_trade = _load_state(s_tr_f, None)
        s_trade = _migrate_trade(s_trade, basis_s, dec=3, notes=notes)
        s_exits = []
        if s_trade:
            s_obj = copy.deepcopy(s_trade)                 # Д3: истинска снимка
            s_trade, s_events = track_trade(s_trade, s5, basis_s, s_price_user, now_utc, spot=spot_s)
            s_cum = dict(s_obj["hit"])                      # попадения от МИНАЛИ рънове
            for kind, px, when, via, gap in s_events:
                if kind in ("tp1", "tp2", "tp3"):          # това попадение стана ТОЗИ рън
                    s_cum[kind] = True
                gk = "s_" + s_obj["direction"]
                if kind == "sl" and abs(px - s_obj["entry"]) > 0.01:   # F3: безрисков стоп не се брои
                    guard[gk] = guard.get(gk, 0) + 1
                _so = dict(s_obj); _so["hit"] = dict(s_cum)  # кумулативна снимка ДО този изход (burst-фикс)
                s_exits.append((kind, _so, px, when, via, gap))
        if s_trade and s_dir not in ("wait",) and s_trade["direction"] != s_dir and s_tk == "premium":
            s_exits.append(("flip", dict(s_trade), s_price_user, now_utc, "спот" if spot_s else "бар", False))
            s_trade = None
        s_actionable = s_dir != "wait" and s_tk != "weak"
        s_last = _load_state(s_state_f, {})
        s_key = f"{date}|{s_dir}:{s_tk}"
        s_mins = None
        if s_last.get("sent_utc"):
            try:
                s_mins = (pd.Timestamp(now_utc) - pd.Timestamp(s_last["sent_utc"])).total_seconds() / 60
            except Exception:
                pass
        s_tier_up = s_actionable and rank.get(s_tk, 0) > rank.get(s_last.get("tier", "weak"), 0) and s_dir == s_last.get("dir")
        s_cool = (s_mins is None or s_mins >= 45 or (s_dir != s_last.get("dir") and s_mins >= 15) or s_tier_up)
        s_closed = any(k in ("tp3", "sl", "time", "flip") for k, *_ in s_exits)
        s_guard_n = guard.get("s_" + s_dir, 0) if s_dir in ("long", "short") else 0
        s_should = args.force or (s_actionable and s_cool and (s_last.get("key") != s_key or s_tier_up))   # НАХОДКА 3
        s_reentry = False        # F19-Т2: СРЕБРОТО ТЪРГУВА САМО ДНЕВНАТА КАРТА — без ре-влизания
        if s_should and s_dir == "short" and shield and s_trade is None:
            s_should = False; notes.append("сребро шорт карта отложена: US-щит")
        if s_should and s_guard_n >= 2 and s_trade is None:
            s_should = False; notes.append("сребро карта спряна: стоп-пазач")
        if s_should and weekend:
            s_should = False; notes.append("сребро: уикенд")
        # F1 (🔴): отворена сребърна сделка + непремиум насрещен → задръж старата, без нова
        if s_should and s_trade is not None and s_dir in ("long", "short") and s_trade["direction"] != s_dir:
            s_should = False
            notes.append(f"сребро: насрещен непремиум {s_dir} при отворена {s_trade['direction']} — задържам")
        # изходни съобщения за среброто (с решение за ново влизане)
        for kind, s_obj, px, when, via, gap in s_exits:
            nl = ""
            if kind in ("tp3", "sl", "time", "flip"):
                nl = "НЕ — среброто търгува само дневната карта (сутрин); ре-влизанията не издържаха теста (F19)."
            silver_new_msgs.append(("s-exit:" + kind, _exit_msg(kind, s_obj, px, when, via, gap, spot=spot_s, next_line=nl, dec=3)))
        if s_should:
            s_entry_user = _entry_side(spot_s, s_dir) if spot_s else s_price_user
            s_lv_user = _levels_silver(round(s_entry_user, 3), s_dir)
            s_streak = regime["streaks"].get(s_dir, 0)
            s_advice, s_adv_ok = _advice_entry(s_dir, s_streak, stats, None, shield, s_guard_n,
                                               sym="XAGUSD", stale_price=(spot_s is None))
            s_open = s_trade if (s_trade and s_trade["direction"] == s_dir) else None
            silver_new_msgs.append(("s-signal", _sig_msg(
                s_dir, s_score, 1, s_tn, spot_s, s_bar, s5.index[-1], s_lv_user,
                s_entry_user, s_advice, macro, s_streak, regime, stats, args.balance, args.risk,
                weekly=None, reentry=s_reentry, open_trade=s_open, sym="XAGUSD", dec=3, adv_ok=s_adv_ok)))
            if s_open is None and s_adv_ok:               # НАХОДКА 1: следи сделка само при съвет ДА
                # Б1: НЕ пишем сребърна сделка/състояние тук — чак след потвърдено пращане (7в)
                silver_trade_new = {"direction": s_dir, "entry": round(s_entry_user, 3), "opened": now_utc,
                                    "checked": now_utc, "levels": s_lv_user, "hit": {}, "status": "open",
                                    "v2": True, "ledger": "spot", "tier": s_tk, "date": date, "sym": "XAGUSD"}
        print(f"  сребро: {s_dir} {s_score}/8 {s_tk} · спот {s_price_user}")
        # Реконсилиация на СЛЕДЕНАТА сделка — БЕЗУСЛОВНО (огледало на златото §8; поправя
        # сребро-сирака: затворена сделка + неуспяла нова карта → старата НЕ оставаше на диска
        # и се пре-следеше всеки рън = дублирани изходи + фалшив стоп-пазач).
        if s_trade:                                        # още отворена → запиши прогреса
            s_tr_f.write_text(json.dumps(s_trade, ensure_ascii=False), encoding="utf-8")
        elif s_tr_f.exists() and (s_exits or silver_trade_new is None):
            s_tr_f.unlink()          # затворена този рън (изходът е в кутията) ИЛИ няма нова сделка
        silver_ok = True                                   # Б3: стигнахме дотук без грешка
    except Exception as e:
        print(f"  сребро пропуснато ({type(e).__name__}: {str(e)[:80]})")
        notes.append(f"сребро пропуснато: {type(e).__name__}")   # Б3: вече видимо в журнала

    # === 6) СГЛОБЯВАНЕ НА СЪОБЩЕНИЯТА (злато) ===
    new_msgs = []           # (tag, text) — редът = хронология: изходи → карта
    for tag, payload, kind, dirn in exit_msgs:
        k, tro, px, when, via, gap = payload
        nl = ""
        if k in ("tp3", "sl", "time", "flip"):
            if actionable and trade is None and new_dir:
                ok_re, why_re = _reentry_verdict(new_dir, regime["streaks"].get(new_dir, 0), shield, guard.get(new_dir, 0))
                # Г3: «идва след паузата» САМО при истинска пауза (ok_re=True). Ако ре-влизането
                # е ОТКАЗАНО (F18/щит) → падни в else и кажи честната причина, не лъжлива «карта».
                if k == "flip" and not should_sig and ok_re:
                    nl = f"обърна се на силен {new_dir.upper()} — новата карта идва след паузата (до 45 мин)"
                else:
                    nl = "ДА — нова карта идва." if (ok_re and should_sig) else f"НЕ — {why_re or 'изчакай следващия ясен сигнал'}"
            else:
                nl = "НЕ — няма активен сигнал." if not actionable else ""
        new_msgs.append((tag, _exit_msg(k, tro, px, when, via, gap, spot=spot_g, next_line=nl)))
    new_msgs += silver_new_msgs
    for tag, m in ma_alerts:
        new_msgs.append(("ma:" + tag.split("|")[1], m))
        ma_sent[tag] = True
    open_tr = None; pending_trade = None
    if sig_payload and should_sig:
        entry_user, lv_user = sig_payload
        open_tr = trade if (trade and trade["direction"] == new_dir) else None
        extra = []
        if daily_ctx and daily_ctx.get("gold_view"):
            extra.append(f"днес: {daily_ctx['gold_view']}")
        if ev_label:
            extra.append(("⚠ ЩИТ: " if ev_shield else "⚠ ") + ev_label)
        new_msgs.append(("signal", _sig_msg(new_dir, best[2], agree_n, best[4], spot_g, bar_price, bar_ts,
                                            lv_user, entry_user, advice_txt, macro, streak_n, regime, stats,
                                            args.balance, args.risk, weekly=weekly, reentry=reentry,
                                            open_trade=open_tr, extra_ctx=" · ".join(extra) if extra else None,
                                            adv_ok=_adv_ok)))
        # Б1: НЕ пишем сделка/състояние ТУК — чак СЛЕД потвърдено пращане.
        # НАХОДКА 1: следим сделка САМО ако съветът е ДА (_adv_ok). При «НЕ/ИЗЧАКАЙ»
        # картата е информативна — не отваряме сделка, за която сме казали да не влизаш.
        if open_tr is None and new_dir and _adv_ok:
            pending_trade = {"direction": new_dir, "entry": round(entry_user, 2), "opened": now_utc, "checked": now_utc,
                             "levels": lv_user, "hit": {}, "status": "open", "v2": True, "ledger": "spot",
                             "tier": best[3], "date": date}

    # === 6б) ВЕЧЕРНА РАВНОСМЕТКА + ПУЛС (Ф5/Ф8.4) и СТАТУС (Ф9.8) ===
    from zoneinfo import ZoneInfo
    sof_now = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/Sofia"))
    want_digest = sof_now.hour >= 21 and meta.get("digest") != date and not weekend
    if want_digest:
        s_tr_now = _load_state(s_tr_f, None)
        new_msgs.append(("digest", _digest_msg(out, date, trade, s_tr_now, spot_g, spot_s, guard,
                                               weekly_part=(sof_now.weekday() == 4))))
        # Д3: meta["digest"] се маркира СЛЕД потвърдено пращане (виж 7б)
    if args.status or os.environ.get("STATUS_CARD") == "yes":
        s_tr_now = _load_state(s_tr_f, None)
        new_msgs.append(("status", _status_msg(board, new_dir, trade, s_tr_now, spot_g, spot_s,
                                               basis_g, basis_s, guard, shield, date, macro)))

    # === 7) ПРАЩАНЕ през пощенската кутия (Ф8.1) ===
    statuses = []
    sent_tags = _outbox_flush(out, new_msgs, statuses, dry=not args.send)
    if not new_msgs and not statuses:
        statuses.append("тихо (без събития)")

    if want_digest and "digest" in sent_tags:            # Д3: маркирай чак след пращане
        meta["digest"] = date

    # === 7б) Б1: сделка/състояние се пишат САМО след ПОТВЪРДЕНО пращане на картата ===
    if should_sig and "signal" in sent_tags:
        (out / "last_sent.json").write_text(json.dumps({"key": key, "date": date, "sent_ok": True,
                                                        "dir": new_dir, "tier": best[3], "sent_utc": now_utc}),
                                            encoding="utf-8")
        if pending_trade is not None:
            trade = pending_trade                          # отваряме сделката чак сега
            statuses.append("trade=OPENED")
    elif should_sig:
        statuses.append("signal НЕ пратен — сделка НЕ отворена (ще опита пак)")

    # === 7в) Б1 за СРЕБРОТО: сребърна сделка/състояние също само след пращане ===
    if silver_trade_new is not None or s_key is not None:
        if "s-signal" in sent_tags:
            if s_key:
                s_state_f.write_text(json.dumps({"key": s_key, "date": date, "sent_ok": True, "dir": s_dir,
                                                 "tier": s_tk, "sent_utc": now_utc}), encoding="utf-8")
            if silver_trade_new is not None:
                s_tr_f.write_text(json.dumps(silver_trade_new, ensure_ascii=False), encoding="utf-8")
                statuses.append("s-trade=OPENED")
        elif silver_trade_new is not None:
            statuses.append("s-signal НЕ пратен — сребърна сделка НЕ отворена")

    # === 8) ЗАПИС на състоянието ===
    if trade:
        tr_f.write_text(json.dumps(trade, ensure_ascii=False), encoding="utf-8")
    elif tr_f.exists() and (exit_msgs or new_dir is None):
        tr_f.unlink()
    ma_sent = {k: v for k, v in ma_sent.items() if k.startswith(date)}
    ma_f.write_text(json.dumps(ma_sent), encoding="utf-8")
    (out / "guard.json").write_text(json.dumps(guard), encoding="utf-8")
    (out / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    run_ended = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
    with (out / "live_journal.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"run_utc": now_utc, "run_ended": run_ended, "date": date, "v": VERSION,
                             "bar": round(bar_price, 2), "bar_ts": str(bar_ts), "bar_age_min": bar_age_min,
                             "spot": (spot_g or {}).get("mid"), "spot_age_sec": (raw_g or {}).get("age_sec"),
                             "spot_src": (spot_g or {}).get("src"), "spot_rejected": spot_rejected_g,
                             "spread": round(spot_g["ask"] - spot_g["bid"], 3) if spot_g else None,
                             "basis": basis_g, "shield": shield, "stale_bar": stale_bar,
                             "track_mode": track_mode, "silver_ok": silver_ok,
                             "trade": ({"dir": trade["direction"], "entry": trade["entry"], "tier": trade.get("tier")}
                                       if trade else None),
                             "board": {l: [d, s, t] for l, d, s, t, _ in board},
                             "exits": [k for _, _, k, _ in exit_msgs],
                             "notes": notes, "status": statuses}, ensure_ascii=False) + "\n")

    print("=" * 60)
    print(f"XAUUSD спот {price_user} · бар {bar_price} · базис {basis_g:+.2f} · {date} · макро {sum(macro.values())}/3"
          + (" · US-ЩИТ" if shield else ""))
    for l, d, s, t, _ in board:
        print(f"  {l:>5}: {d:>5} {s}/8 {t}")
    if notes:
        print("БЕЛЕЖКИ:", " | ".join(notes))
    print(f"[LIVE {date} {VERSION}] посока: {new_dir or '—'} · {' · '.join(statuses)}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        print("ГРЕШКА В БОТА:\n" + traceback.format_exc())
        try:
            _send_raw(f"⚠️ <b>AERO бот · временен проблем</b>\n<code>{type(e).__name__}: {str(e)[:250]}</code>\n"
                      f"<i>Ще опита пак на следващото пускане.</i>")
        except Exception:
            pass
        raise SystemExit(0)
