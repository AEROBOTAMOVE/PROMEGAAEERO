import io, json, sys, hashlib

s = io.open("live_bot.py", encoding="utf-8", newline="").read()
assert "NEAR_HIGH_DD20" not in s, "кръпката вече е вътре"
ops = []


def rep(old, new, why):
    global s
    c = s.count(old)
    if c != 1:
        print(f"  ✗ СПИРАМ «{why}»: {c} съвпадения за {old[:70]!r}")
        sys.exit(1)
    s = s.replace(old, new, 1)
    ops.append(why)


# ── 1 · прагът ────────────────────────────────────────────────────────────
rep("MIN_N = 100      # В4: под толкова сделки процентът е шум → не се цитира",
    '''MIN_N = 100      # В4: под толкова сделки процентът е шум → не се цитира
# ── ОДИТ-16 (05.08) · «ШОРТ ДО ВЪРХА». ДОПЪЛНИТЕЛНА КЛЕТКА — НИЩО НЕ СЕ МАХА. ────────
# И четирите шорт-клетки са ОТКАЗ (нето ≤0 или нулата е в интервала) → ботът НИКОГА не
# отваря шорт. Форуърдът 21.07-04.08 показа обратното: 24 от 29 сенки бяха шортове и
# донесоха +41$/oz хипотетично. Мерено на същите 114813 сделки, вътре в `fresh`
# (стрийк 2-3) има ЕДНА подклетка с истински ръб — когато златото затваря БЛИЗО ДО
# ВЪРХА СИ, НЕ когато пада.
#   n=779 · 39 карти-дни за 20г (~2/год) · 86.8% · +5.05$/oz · 95% [+2.62..+7.29]
#   четвъртини +5.88(122) / +7.84(242) / +2.33(192) / +3.90(223) — 4/4, всяка с n≥100
#   само-напред (4 среза): +4.89 · +6.28 · +7.06 · +6.00 — 4/4
#   клъстер-нула, 20000 тегления по 39 дни: нула −0.70, max +4.51 → P(≥цел)=0.00000
#   615 правила претърсени вътре в `fresh`; минават 6 — и шестте са СЪЩОТО семейство
#   с ДВА пълни спреда: +4.38 [+1.95..+6.62] · 0 от 39 нови дни съвпадат със сегашните
# СПАДЪТ СЕ МЕРИ ВЪРХУ GC=F — серията, която ботът дърпа. Върху СПОТ числото е ДРУГО
# (медианна разлика 0.49 п.п., p90 2.13) → прагът НЕ се пренася между двете серии.
# ПЛАТО, не ръб: 0.75%→+6.57 · 1.0%→+6.91 · 1.5%→+5.05 · 2.0%→+3.76 · 2.5%→+2.03(шум).
# 1.5% е НАЙ-МАЛКИЯТ праг, при който ВСЯКА четвъртина има n≥100 (В4) и е положителна.
# ЧЕСТНО ОЧАКВАНЕ ИЗВЪН ИЗВАДКАТА: ~+3.0$/oz, не +5.05 — прагът е избран след търсене.
# ИЗКЛЮЧВАТЕЛ: махни ключа `near_high` от backtest_stats.json → клетката умира моментално,
# без пипане на код и без качване.
NEAR_HIGH_DD20 = 0.015''',
    "прагът NEAR_HIGH_DD20")

# ── 2 · подписът: нов аргумент С ПОДРАЗБИРАНЕ ─────────────────────────────
rep('def _advice_entry(direction, streak_n, stats, fast, shield, guard_n, sym="XAUUSD", stale_price=False, trace=None):',
    'def _advice_entry(direction, streak_n, stats, fast, shield, guard_n, sym="XAUUSD",\n'
    '                  stale_price=False, dd20=None, trace=None):',
    "подпис + dd20=None")

# ── 3 · seg_near в ДВАТА клона ────────────────────────────────────────────
rep('        seg_mixed = fr.get("mixed") or seg_stale\n        src = "пресен ден-" + str(streak_n)',
    '        seg_mixed = fr.get("mixed") or seg_stale\n'
    '        seg_near = fr.get("near_high") or {}          # ОДИТ-16; липсва → мъртва клетка\n'
    '        src = "пресен ден-" + str(streak_n)',
    "seg_near · злато")
rep('        seg_mixed = sv.get("mixed") or seg_stale      # ОДИТ-8: среброто няма разделена кофа\n        src = "сребро пресен"',
    '        seg_mixed = sv.get("mixed") or seg_stale      # ОДИТ-8: среброто няма разделена кофа\n'
    '        seg_near = {}                                 # ОДИТ-16: среброто НЯМА такова измерване\n'
    '        src = "сребро пресен"',
    "seg_near · сребро")

# ── 4 · самата клетка ─────────────────────────────────────────────────────
rep("    if 1 <= streak_n <= 3:\n        seg = seg_fresh\n",
    '''    if 1 <= streak_n <= 3:
        seg = seg_fresh
        # ── ОДИТ-16 · «ШОРТ ДО ВЪРХА». Единственото, което този клон може да направи, е да
        # превърне ОТКАЗ в ПУСКАНЕ, и то САМО за ЗЛАТО-ШОРТ при стрийк 2-3. Днес този
        # случай е БЕЗУСЛОВЕН ОТКАЗ (short/fresh: n=5162, нето −0.71, нулата е в интервала)
        # → нищо съществуващо не се отнема. Няма ли `near_high` в stats (стар файл) или
        # няма dd20 (стар извикващ) → клонът МЪЛЧИ и ботът е точно какъвто беше.
        # Стои СЛЕД стоп-пазача, щита и старата цена — те продължават да го бият.
        if (is_gold and direction == "short" and 2 <= streak_n <= 3
                and dd20 is not None and np.isfinite(dd20) and dd20 < NEAR_HIGH_DD20
                and seg_near.get("n", 0) >= MIN_N and seg_near.get("net", 0) > 0
                and not _noise(seg_near)):
            _by("клетка")
            return (f"ДА — шорт при злато ДО ВЪРХА СИ ({dn}; спад от 20-дневния връх "
                    f"{100 * dd20:.2f}% < {100 * NEAR_HIGH_DD20:.1f}%)"
                    + _pct(seg_near, "връх-шорт") + _fast(fast)), True
''',
    "клетката «шорт до върха»")

# ── 5 · пресмятането на спада (само от ЗАВЪРШЕНИ дни) ────────────────────
rep("    gold_h, gdx_h, dxy_h = _hist(gold_d), _hist(gdx_d), _hist(dxy_d)",
    '''    gold_h, gdx_h, dxy_h = _hist(gold_d), _hist(gdx_d), _hist(dxy_d)
    # ОДИТ-16: спад от 20-дневния връх ПО ЗАТВАРЯНИЯ, само от ЗАВЪРШЕНИ дни (gold_h, не
    # gold_d — иначе днешният незавършен бар мърда числото в рамките на деня и клетката
    # би се съдила с друга геометрия от мерената). Прозорецът ВКЛЮЧВА последното затваряне.
    dd20_g = None
    try:
        _c20 = gold_h["Close"].dropna()
        if len(_c20) >= 20:
            _hi20 = float(_c20.tail(20).max()); _last20 = float(_c20.iloc[-1])
            if np.isfinite(_hi20) and np.isfinite(_last20) and _last20 > 0:
                dd20_g = (_hi20 - _last20) / _last20
    except Exception:
        dd20_g = None''',
    "пресмятане на dd20_g")

# ── 6 · подаване при викането (само добавен keyword) ─────────────────────
rep('''                                        sym="XAUUSD", stale_price=(spot_g is None),
                                        trace=_gate_trace) if new_dir else ("", False)''',
    '''                                        sym="XAUUSD", stale_price=(spot_g is None),
                                        dd20=dd20_g,
                                        trace=_gate_trace) if new_dir else ("", False)''',
    "подаване на dd20")

# ── 7 · записът в дневника носи и спада (проверимост, чл.1) ──────────────
rep('''                                       "by": _gate_trace.get("by"),''',
    '''                                       "by": _gate_trace.get("by"),
                                       "dd20": (None if dd20_g is None else round(dd20_g, 5)),''',
    "dd20 в дневника")

# ── версия ────────────────────────────────────────────────────────────────
rep('VERSION = "v6.2a"', 'VERSION = "v6.3"', "версия → v6.3")

io.open("live_bot.py", "wb").write(s.encode("utf-8"))

# ── 8 · клетката в backtest_stats.json ───────────────────────────────────
p = "backtest_stats.json"
raw = io.open(p, encoding="utf-8", newline="").read()
st = json.loads(raw)
sh = st["fresh"]["short"]
assert "near_high" not in sh, "ключът вече е вътре"
sh["near_high"] = {"win": 86.8, "net": 5.05, "n": 779, "дни": 39, "lo": 2.62, "hi": 7.29}
io.open(p, "wb").write((json.dumps(st, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
ops.append("near_high в backtest_stats.json")

print(f"ПРИЛОЖЕНИ {len(ops)}:")
for o in ops:
    print(f"  ✓ {o}")
print(f"\nlive_bot.py {len(s.split(chr(10)))} реда · sha {hashlib.sha256(s.encode()).hexdigest()[:14]}")
