import io, hashlib

p = "selftest.py"
src = io.open(p, encoding="utf-8", newline="").read()
assert "ОДИТ-15/б" not in src, "тестовете вече са вътре"

anchor = "# --- 4 · ДОБАВКА, НЕ ЗАМЯНА: старият запис е непокътнат ---"
assert src.count(anchor) == 1

block = '''# --- 3б · ОДИТ-15/б: КОЙ ПЛАСТ реши. Първата версия на записа слагаше кофата
# ДОРИ когато решението е дошло от стоп-пазача, щита или старата цена — тоест
# преди клетката изобщо да бъде погледната. Хванато на ЖИВ рън: v6.2 записа
# `cell: mixed`, а истинската причина беше «спотът недостъпен».
_TR = {}
lb._advice_entry("long", 1, _BS18, None, False, 2, trace=_TR)
ck("П18б стоп-пазачът се отчита като стоп-пазач", _TR.get("by") == "стоп-пазач")
_TR = {}
lb._advice_entry("short", 1, _BS18, None, True, 0, trace=_TR)
ck("П18б US-щитът се отчита като щит", _TR.get("by") == "US-щит")
_TR = {}
lb._advice_entry("long", 1, _BS18, None, False, 0, stale_price=True, trace=_TR)
ck("П18б старата цена се отчита като стара цена", _TR.get("by") == "стара цена")
for _s18b in (0, 1, 2, 4):
    for _d18b in ("long", "short"):
        _TR = {}
        lb._advice_entry(_d18b, _s18b, _BS18, None, False, 0, trace=_TR)
        ck(f"П18б {_d18b}/стрийк{_s18b} без пречки → решава КЛЕТКАТА",
           _TR.get("by") == "клетка")
# ранните пластове НЕ докладват клетка — иначе броенето по кофи мешка чужди откази
for _kw in ({"guard_n": 2}, {"shield": True}, {"stale_price": True}):
    _TR = {}
    lb._advice_entry("short", 1, _BS18, None, _kw.get("shield", False),
                     _kw.get("guard_n", 0), stale_price=_kw.get("stale_price", False), trace=_TR)
    ck(f"П18б ранен пласт {list(_kw)[0]} НЕ се представя за клетка", _TR.get("by") != "клетка")
# обратна съвместимост: без trace нищо не се променя
_a18b, _o18b = lb._advice_entry("short", 0, _BS18, None, False, 0)
_TR = {}
_a18c, _o18c = lb._advice_entry("short", 0, _BS18, None, False, 0, trace=_TR)
ck("П18б `trace` НЕ променя нито текста, нито присъдата",
   _a18b == _a18c and _o18b == _o18c)
ck("П18б без `trace` гейтът не гърми (старите викания са цели)", isinstance(_a18b, str))

# и в ЖИВИЯ запис
for _d18 in ("long", "short"):
    _c, _rec18b = _run_dir18(_d18)
    _g18b = _rec18b.get("gate") or {}
    ck(f"П18б {_d18}: записът казва КОЙ пласт е решил", isinstance(_g18b.get("by"), str))
    ck(f"П18б {_d18}: «by» е един от познатите пластове",
       _g18b.get("by") in ("клетка", "стоп-пазач", "US-щит", "стара цена"))
    ck(f"П18б {_d18}: причината съответства на пласта",
       (_g18b.get("by") == "стара цена") == ("цената е ~10-15 мин стара" in _g18b.get("why", "")))

'''

src = src.replace(anchor, block + anchor, 1)
io.open(p, "wb").write(src.encode("utf-8"))
print(f"selftest.py: {len(src.split(chr(10)))} реда · sha "
      f"{hashlib.sha256(src.encode('utf-8')).hexdigest()[:14]}")
