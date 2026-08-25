import io, hashlib

p = "selftest.py"
src = io.open(p, encoding="utf-8", newline="").read()
assert "П18" not in src, "П18 вече е вътре — не дублирай"
LN = src.split("\n")
# котва: редът на БАРИЕРАТА е уникален; вмъкваме над разделителя точно над него
hit = [i for i, l in enumerate(LN) if "БАРИЕРАТА СТОЕШЕ В СРЕДАТА" in l]
assert len(hit) == 1, f"котвата не е уникална: {len(hit)}"
top = hit[0] - 1
assert LN[top].startswith("# ═"), f"над котвата не е разделител: {LN[top][:40]!r}"

block = '''# ═══════════════════════════════════════════════════════════════════════
# П18 · ОДИТ-15: ГЕЙТЪТ НЯМАШЕ ТРАЙНА СЛЕДА.
# `macro` и `board` се пишат в дневника (ОДИТ-5), а САМАТА ПРИСЪДА — не.
# Затова «защо отказа този шорт на 23.07» се четеше по археология в текста
# на картите — а старите карти дори не носят причината.
# Рискът от такава добавка е ЕДИН: двете места да съдят по различни правила.
# Затова съответствието `_cell_name` ↔ `_advice_entry` се проверява с
# ИЗПЪЛНЕНИЕ (уникално нето на клетка), не с греп.
# ═══════════════════════════════════════════════════════════════════════
_BS18 = json.loads(open("backtest_stats.json", encoding="utf-8").read())
_CELLS18 = {"day1": 1.11, "fresh": 2.22, "mixed": 3.33, "stale": 4.44}


def _stats18():
    """Изкуствени клетки: всяка с УНИКАЛНО нето → по текста се познава коя е ползвана."""
    d = {"fresh": {"long": {}, "short": {}}}
    for c, v in _CELLS18.items():
        for dr in ("long", "short"):
            d["fresh"][dr][c] = {"n": 500, "win": 70, "net": v, "lo": v - 0.2, "hi": v + 0.2}
    return d


# --- 1 · имената на кофите покриват ВСЕКИ стрийк ---
for _s18, _want in ((0, "mixed"), (1, "day1"), (2, "fresh"), (3, "fresh"),
                    (4, "stale"), (5, "stale"), (9, "stale"), (40, "stale")):
    ck(f"П18 стрийк {_s18} → кофа «{_want}»", lb._cell_name(_s18) == _want)

# --- 2 · СЪОТВЕТСТВИЕ по ИЗПЪЛНЕНИЕ: гейтът наистина съди по тази кофа ---
_st18 = _stats18()
for _s18 in (0, 1, 2, 3, 4, 5, 9):
    for _d18 in ("long", "short"):
        _txt18, _ok18 = lb._advice_entry(_d18, _s18, _st18, None, False, 0)
        _cell18 = lb._cell_name(_s18)
        _mine = f"{_CELLS18[_cell18]:+}$/oz"
        _other = [f"{v:+}$/oz" for c, v in _CELLS18.items() if c != _cell18]
        ck(f"П18 {_d18}/стрийк{_s18}: гейтът цитира кофа «{_cell18}»",
           _mine in _txt18 and not any(o in _txt18 for o in _other))

# --- 3 · ЖИВИЯТ рън записва присъдата в дневника ---
# Синтетичният борд стои на «wait» → `gate` излиза None и важните твърдения
# НЕ БИХА СЕ ИЗПЪЛНИЛИ — точно това е «празно зелено». Затова посоката се
# налага през `_resolve`, за да мине наистина пълният път.
_c18, _s18s, _t18 = _run_main(spot=_SP)
ck("П18 рънът минава до края с новия запис", _c18 == 0)
_j18 = [json.loads(x) for x in
        (_t18 / "live_journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
ck("П18 дневникът НОСИ ключа за присъдата", "gate" in _j18[0])
ck("П18 без посока присъдата е None, а ключът пак стои", _j18[0].get("gate", "ЛИПСВА") is None)


def _run_dir18(force_dir):
    """Налага посока през `_resolve`, за да се изпълни ПЪЛНИЯТ запис на присъдата."""
    _orig = lb._resolve
    lb._resolve = lambda ls, ss, macro: (force_dir, 7, "premium", "ПРЕМИУМ")
    try:
        c, s, t = _run_main(spot=_SP)
    finally:
        lb._resolve = _orig
    j = [json.loads(x) for x in
         (t / "live_journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    _sh4.rmtree(t, ignore_errors=True)
    return c, j[0]


for _d18 in ("long", "short"):
    _c, _rec18 = _run_dir18(_d18)
    _g18 = _rec18.get("gate")
    ck(f"П18 {_d18}: рънът минава до края", _c == 0)
    ck(f"П18 {_d18}: присъдата НЕ е празна, когато има посока", isinstance(_g18, dict))
    ck(f"П18 {_d18}: носи посока/стрийк/кофа/ДА-НЕ/причина",
       bool(_g18) and all(k in _g18 for k in ("dir", "streak", "cell", "ok", "why")))
    ck(f"П18 {_d18}: записаната посока е точно тази", bool(_g18) and _g18["dir"] == _d18)
    ck(f"П18 {_d18}: кофата СЪВПАДА със стрийка в същия запис",
       bool(_g18) and _g18["cell"] == lb._cell_name(_g18["streak"]))
    ck(f"П18 {_d18}: «ok» е булево (не текст, не None)",
       bool(_g18) and isinstance(_g18["ok"], bool))
    ck(f"П18 {_d18}: причината е непразен текст",
       bool(_g18) and isinstance(_g18["why"], str) and len(_g18["why"]) > 3)
    # присъдата в дневника трябва да е СЪЩАТА, която гейтът връща за тези входове
    _t18x, _ok18x = lb._advice_entry(_d18, _g18["streak"], _BS18, None, _rec18.get("shield", False), 0,
                                     sym="XAUUSD", stale_price=(_rec18.get("spot") is None))
    ck(f"П18 {_d18}: записаното «ok» СЪВПАДА с това, което гейтът връща",
       bool(_g18) and _g18["ok"] == bool(_ok18x))
    ck(f"П18 {_d18}: записаната причина СЪВПАДА с текста на гейта",
       bool(_g18) and _g18["why"] == _t18x)

# --- 4 · ДОБАВКА, НЕ ЗАМЯНА: старият запис е непокътнат ---
for _k18 in ("run_utc", "date", "v", "bar", "spot", "basis", "macro", "macro_raw",
             "board", "trade", "exits", "notes", "status", "shield", "track_mode"):
    ck(f"П18 старият ключ «{_k18}» още стои в дневника", _k18 in _j18[0])
ck("П18 бордът още е по 7 рамки", len(_j18[0].get("board") or {}) == 7)
_sh4.rmtree(_t18, ignore_errors=True)


'''

LN[top:top] = block.rstrip("\n").split("\n") + ["", ""]
src = "\n".join(LN)
io.open(p, "wb").write(src.encode("utf-8"))
print("selftest.py:", len(src.split("\n")), "реда · sha",
      hashlib.sha256(src.encode()).hexdigest()[:14])
