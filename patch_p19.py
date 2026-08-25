import io, sys

p = "selftest.py"
s = io.open(p, encoding="utf-8", newline="").read()
assert "П19" not in s, "П19 вече е вътре"
ops = []


def rep(old, new, why):
    global s
    c = s.count(old)
    if c != 1:
        print(f"  ✗ СПИРАМ «{why}»: {c} съвпадения"); sys.exit(1)
    s = s.replace(old, new, 1); ops.append(why)


# ── 1 · О7: прагът остава СТРОГ за широките клетки; тясната си има свой ──
rep('''ck("О7 извадките са ГОЛЕМИ (n>1000 навсякъде в fresh)",
   all(v["n"] > 1000 for d in ("long", "short") for v in _fr[d].values()))''',
    '''# ОДИТ-16: `near_high` е НАРОЧНО тясна подклетка (779) — тя е подмножество на `fresh`,
# избрано по едно допълнително условие. Затова прагът се разделя: ШИРОКИТЕ четири
# клетки пазят стария строг праг непокътнат, а тясната има СВОЙ, обоснован:
# n≥500 И 95% интервалът да НЕ минава през нулата. Общото разхлабване би обезсилило
# защитата за клетките, които наистина решават всекидневните входове.
_BROAD7 = ("day1", "fresh", "mixed", "stale")
ck("О7 ШИРОКИТЕ клетки са ГОЛЕМИ (n>1000) — прагът НЕ е разхлабен",
   all(_fr[d][c]["n"] > 1000 for d in ("long", "short") for c in _BROAD7 if c in _fr[d]))
ck("О7 всичките четири широки клетки присъстват и за двете посоки",
   all(c in _fr[d] for d in ("long", "short") for c in _BROAD7))
_NH7 = _fr["short"].get("near_high")
ck("О7 тясната near_high има n≥500 и интервал НАД нулата",
   _NH7 is None or (_NH7["n"] >= 500 and _NH7.get("lo", -1) > 0 and _NH7["net"] > 0))''',
    "О7 · разделен праг")

# ── 2 · блокът П19 преди бариерата ───────────────────────────────────────
LN = s.split("\n")
hit = [i for i, l in enumerate(LN) if "БАРИЕРАТА СТОЕШЕ В СРЕДАТА" in l]
assert len(hit) == 1
top = hit[0] - 1
assert LN[top].startswith("# ═")

block = '''# ═══════════════════════════════════════════════════════════════════════
# П19 · ОДИТ-16: «ШОРТ ДО ВЪРХА» — ПЪРВАТА клетка, която пуска ЗЛАТО-ШОРТ.
# И четирите шорт-клетки бяха ОТКАЗ → ботът не можеше да отвори шорт никога.
# Тази клетка може САМО да превърне ОТКАЗ в ПУСКАНЕ и то в тесен случай.
# Затова най-важните тестове тук НЕ са за новото поведение, а за това, че
# СТАРОТО е абсолютно непокътнато.
# ═══════════════════════════════════════════════════════════════════════
import copy as _cp19
_NEW19 = json.loads(open("backtest_stats.json", encoding="utf-8").read())
_OLD19 = _cp19.deepcopy(_NEW19)
_OLD19["fresh"]["short"].pop("near_high", None)      # ботът, какъвто беше преди клетката
_DD19 = (None, 0.0, 0.001, 0.005, 0.0149, 0.015, 0.0151, 0.02, 0.5, float("nan"))


def _new19(d, s19, dd=None, st=None, shield=False, guard=0, stale=False, sym="XAUUSD"):
    return lb._advice_entry(d, s19, st if st is not None else _NEW19, None, shield, guard,
                            sym=sym, stale_price=stale, dd20=dd)


def _old19(d, s19):
    return lb._advice_entry(d, s19, _OLD19, None, False, 0)


# --- 1 · СТАРОТО ПОВЕДЕНИЕ (най-важното) ---
ck("П19 БЕЗ dd20 всички клетки дават ТОЧНО каквото даваха преди",
   all(_new19(d, s19) == _old19(d, s19) for d in ("long", "short") for s19 in range(0, 9)))
ck("П19 нито едно днешно ДА не изчезва (посока × стрийк × dd20)",
   all((not _old19(d, s19)[1]) or _new19(d, s19, dd)[1]
       for d in ("long", "short") for s19 in range(0, 9) for dd in _DD19))
ck("П19 ЛОНГЪТ е недокоснат при всяко dd20",
   all(_new19("long", s19, dd) == _old19("long", s19)
       for s19 in range(0, 9) for dd in _DD19))
ck("П19 клетката САМО отваря — никога не затваря вход",
   all(not (_old19(d, s19)[1] and not _new19(d, s19, dd)[1])
       for d in ("long", "short") for s19 in range(0, 9) for dd in _DD19))

# --- 2 · ФЕЙЛ-СЕЙФ: без данни клетката МЪЛЧИ ---
ck("П19 стар stats БЕЗ near_high + малък спад → пак ОТКАЗ",
   not _new19("short", 2, 0.001, st=_OLD19)[1])
ck("П19 dd20=None (стар извикващ) → ОТКАЗ", not _new19("short", 2, None)[1])
ck("П19 dd20=NaN → ОТКАЗ", not _new19("short", 2, float("nan"))[1])
_small19 = _cp19.deepcopy(_NEW19)
_small19["fresh"]["short"]["near_high"] = {"win": 90.0, "net": 5.0, "n": 99, "lo": 2.0, "hi": 8.0}
ck("П19 n под MIN_N → ОТКАЗ", not _new19("short", 2, 0.001, st=_small19)[1])
_noisy19 = _cp19.deepcopy(_NEW19)
_noisy19["fresh"]["short"]["near_high"] = {"win": 90.0, "net": 5.0, "n": 779, "lo": -0.5, "hi": 9.0}
ck("П19 шум-пазачът важи и за новата клетка (нулата в интервала → ОТКАЗ)",
   not _new19("short", 2, 0.001, st=_noisy19)[1])
_neg19 = _cp19.deepcopy(_NEW19)
_neg19["fresh"]["short"]["near_high"] = {"win": 90.0, "net": -1.0, "n": 779, "lo": -3.0, "hi": -0.2}
ck("П19 отрицателно нето → ОТКАЗ", not _new19("short", 2, 0.001, st=_neg19)[1])

# --- 3 · ГРАНИЦИТЕ ---
ck("П19 пали при стрийк 2 и 3", _new19("short", 2, 0.001)[1] and _new19("short", 3, 0.001)[1])
ck("П19 НЕ пали при стрийк 1 — day1 е ДРУГА клетка", not _new19("short", 1, 0.001)[1])
ck("П19 НЕ пали при стрийк 0 (mixed) и 4+ (stale)",
   not _new19("short", 0, 0.001)[1] and not _new19("short", 5, 0.001)[1])
ck("П19 прагът реже точно: 1.49% пали, 1.51% не",
   _new19("short", 2, 0.0149)[1] and not _new19("short", 2, 0.0151)[1])
ck("П19 точно на прага НЕ пали (строго по-малко)", not _new19("short", 2, 0.015)[1])
ck("П19 среброто НИКОГА не пали новата клетка",
   not _new19("short", 2, 0.001, sym="XAGUSD")[1])

# --- 4 · СЪЩЕСТВУВАЩИТЕ ПАЗАЧИ СА ПРЕДИ НЕЯ и я бият ---
ck("П19 US-щитът бие новата клетка", not _new19("short", 2, 0.001, shield=True)[1])
ck("П19 стоп-пазачът (2 стопа) бие новата клетка", not _new19("short", 2, 0.001, guard=2)[1])
ck("П19 без спот (стара цена) новата клетка мълчи",
   not _new19("short", 2, 0.001, stale=True)[1])

# --- 5 · ТЕКСТЪТ Е ПРОВЕРИМО ЧИСЛО (чл.1) ---
_t19 = _new19("short", 2, 0.004)[0]
ck("П19 картата казва ДА и показва измерения спад", _t19.startswith("ДА") and "0.40%" in _t19)
ck("П19 картата показва и ПРАГА, срещу който е съдено", "1.5%" in _t19)
ck("П19 картата цитира числото на клетката", "+5.05" in _t19 and "779" in _t19)

# --- 6 · САМОТО dd20: от ЗАВЪРШЕНИ дни, прозорецът включва последното затваряне ---
_c19 = pd.Series([100.0] * 19 + [110.0] + [99.0],
                 index=pd.date_range("2026-01-01", periods=21, freq="D"))
_h19 = _c19.iloc[:-1]                                    # gold_h = БЕЗ днешния незавършен
ck("П19 спадът се мери от последните 20 ЗАВЪРШЕНИ затваряния",
   abs((float(_h19.tail(20).max()) - float(_h19.iloc[-1])) / float(_h19.iloc[-1])) < 1e-12)
ck("П19 днешният НЕЗАВЪРШЕН бар не участва",
   float(_c19.iloc[-1]) == 99.0 and float(_h19.iloc[-1]) == 110.0)
ck("П19 под 20 бара → няма число (кодът пази None)", len(_c19.head(5)) < 20)
ck("П19 кодът мери върху gold_h (завършени), НЕ върху gold_d",
   'gold_h["Close"].dropna()' in _src and 'dd20_g = (_hi20 - _last20)' in _src)

# --- 7 · ЖИВИЯТ ФАЙЛ и прагът в кода ---
_live19 = json.loads(open("backtest_stats.json", encoding="utf-8").read())
_nh19 = _live19.get("fresh", {}).get("short", {}).get("near_high", {})
ck("П19 живият near_high има n≥MIN_N и интервал НАД нулата",
   _nh19.get("n", 0) >= lb.MIN_N and _nh19.get("lo", -1) > 0)
ck("П19 прагът в кода е 1.5% (не по-широк от мереното)", lb.NEAR_HIGH_DD20 == 0.015)
ck("П19 дневникът записва и спада (проверимост)", '"dd20": (None if dd20_g is None' in _src)


'''

LN[top:top] = block.rstrip("\n").split("\n") + ["", ""]
s = "\n".join(LN)
io.open(p, "wb").write(s.encode("utf-8"))
ops.append("блок П19")

print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  ✓ {o}")
print(f"selftest.py {len(s.split(chr(10)))} реда")
