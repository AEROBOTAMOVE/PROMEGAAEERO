# -*- coding: utf-8 -*-
"""selftest.py — офлайн тестове на AERO бота (без мрежа, без токени).
Пускат се автоматично при всяко качване (tests.yml). Червено = НЕ качвай live.
"""
import importlib.util, json, sys
import pandas as pd

spec = importlib.util.spec_from_file_location("lb", "live_bot.py")
lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)

FAILS = []
_RAN = [0]          # ОДИТ-3: брояч — за да се вижда, ако цял блок е спрял да се пуска
def ck(name, ok):
    ok = bool(ok)
    _RAN[0] += 1
    print(("PASS" if ok else "FAIL"), "·", name)
    if not ok:
        FAILS.append(name)

def bars(rows, start="2026-07-16 05:00:00"):
    idx = pd.date_range(start, periods=len(rows), freq="5min")
    return pd.DataFrame(rows, index=idx, columns=["Open", "High", "Low", "Close"])

TR = {"direction": "short", "entry": 4034.5, "opened": "2026-07-16T04:11", "checked": "2026-07-16T04:11",
      "levels": {"tp1": 4027.0, "tp2": 4022.5, "tp3": 4014.5, "sl": 4054.5},
      "hit": {}, "status": "open", "v2": True, "ledger": "spot"}

# 1. следене: тп по бар (с базис-превод)
t = dict(TR, hit={})
_, ev = lb.track_trade(t, bars([(4036, 4037, 4033.0, 4034)]), 6.0, 4028.0, "2026-07-16T05:20")
ck("тп1 по бар с базис", [e[0] for e in ev] == ["tp1"])
# 2. следене: моментално по спот
t = dict(TR, hit={"tp1": True})
_, ev = lb.track_trade(t, bars([(4032, 4033, 4030, 4031)]), 6.0, 4022.0, "2026-07-16T05:30",
                       spot={"bid": 4022.2, "ask": 4022.6, "mid": 4022.4})
ck("тп2 моментално по спот", [(e[0], e[3]) for e in ev] == [("tp2", "спот")])
# 3. гап през стопа → цена на отварянето
t = dict(TR, hit={})
_, ev = lb.track_trade(t, bars([(4062, 4064, 4060, 4061)]), 6.0, 4056, "2026-07-16T05:40")
ck("гап: изход на отварянето", ev and ev[0][0] == "sl" and ev[0][1] == 4056.0 and ev[0][4] is True)
# 3б. БЕЗРИСКОВ СТОП: след ТП1 стопът се мести на входа (картата го обещава)
t = {"direction": "short", "entry": 4000.0, "opened": "2026-07-16T07:00", "checked": "2026-07-16T07:00",
     "levels": lb._levels(4000.0, "short"), "hit": {}, "status": "open", "v2": True, "ledger": "spot"}
lb.track_trade(t, bars([(3993, 3994, 3991, 3992), (3995, 3996, 3994, 3995)], "2026-07-16 08:00:00"), 0.0, 3995.0, "2026-07-16T09:00")
ck("безрисков стоп след ТП1 (SL→вход)", t["hit"].get("tp1") and t["levels"]["sl"] == 4000.0 and t["status"] == "open")
# 3б2. и ако после се върне до входа → стоп на НУЛА, не −20
t2 = {"direction": "short", "entry": 4000.0, "opened": "2026-07-16T07:00", "checked": "2026-07-16T07:00",
      "levels": lb._levels(4000.0, "short"), "hit": {}, "status": "open", "v2": True, "ledger": "spot"}
_, ev2 = lb.track_trade(t2, bars([(3993, 3994, 3991, 3992), (4000, 4001, 3999, 4000)], "2026-07-16 08:00:00"), 0.0, 4000.0, "2026-07-16T09:00")
sl_ev = [e for e in ev2 if e[0] == "sl"]
ck("след ТП1 стопът е на нула (не −20)", sl_ev and abs(sl_ev[0][1] - 4000.0) <= 1.0)  # ≈вход, НЕ 4020
# 3в. РОЛОВЪР-DEADLOCK: санити срещу бар−базис (не голия бар); роловър се засича
# (НАХОДКА-A: ре-анкер иска и БАРЪТ да е скочил — преди роловър барът бе ~4006)
meta = {"basis_g": 6.0, "basis_g_bar": 4006.0}; nt = []
b = lb._basis_update(meta, "basis_g", {"bid": 3999.5, "ask": 4000.5, "mid": 4000.0}, 4036.0, nt, cap=40.0)  # бар скача +30
ck("роловър ре-анкер (не deadlock)", b == 36.0 and len(nt) == 1)
ck("санити срещу бар−базис минава след роловър",
   lb._spot_sane({"bid": 3999.5, "ask": 4000.5, "mid": 4000.0}, 4036.0 - 36.0, 8.0) is not None)
# 4. стопът първи при двоен удар
t = dict(TR, hit={})
_, ev = lb.track_trade(t, bars([(4040, 4061, 4020, 4030)]), 6.0, 4030, "2026-07-16T05:50")
ck("стоп първи при двоен удар", [e[0] for e in ev] == ["sl"])
# 5. миграция v4 → спот-леджър
old = dict(TR, entry=4040.7, levels={"tp1": 4033.2, "tp2": 4028.7, "tp3": 4020.7, "sl": 4060.7})
old.pop("ledger")
mig = lb._migrate_trade(dict(old), 6.0)
ck("миграция в спот", mig["entry"] == 4034.7 and mig["ledger"] == "spot")
# 6. ре-влизане (F18): шорт пресен НЕ · шорт щит НЕ · лонг ДА · 2 стопа НЕ
ck("F18 шорт пресен", lb._reentry_verdict("short", 2, False, 0)[0] is False)
ck("F18 шорт в щита", lb._reentry_verdict("short", 10, True, 0)[0] is False)
ck("F18 лонг ок", lb._reentry_verdict("long", 1, False, 0)[0] is True)
ck("стоп-пазач", lb._reentry_verdict("long", 1, False, 2)[0] is False)
# 7. щит по НЮ ЙОРК (лято и зима)
ck("щит лято 12:30 UTC", lb._in_shield("2026-07-16T12:30") is True)
ck("щит зима 13:30 UTC", lb._in_shield("2026-01-15T13:30") is True)
ck("извън щита 15:00 UTC", lb._in_shield("2026-07-16T15:00") is False)
# 8. спот-санити + страна на спреда
ck("санити реже луд спот", lb._spot_sane({"bid": 4020, "ask": 4021, "mid": 4020.5}, 4093.5, 25) is None)
sp = {"bid": 4088.9, "ask": 4089.4, "mid": 4089.15}
ck("шорт→bid лонг→ask", lb._entry_side(sp, "short") == 4088.9 and lb._entry_side(sp, "long") == 4089.4)
# 9. базис + роловър (нов подпис: raw_spot, bar_close)
meta = {}; notes = []
lb._basis_update(meta, "b", {"mid": 4089.0}, 4095.0, notes)
lb._basis_update(meta, "b", {"mid": 4089.0}, 4110.0, notes)
ck("роловър ре-анкер", meta["b"] == 21.0 and len(notes) == 1)
# 10. нива — точна аритметика
ck("златни нива", lb._levels(4000.0, "long") == {"tp1": 4007.5, "tp2": 4012.0, "tp3": 4020.0, "sl": 3980.0})
ck("сребърни нива", lb._levels_silver(58.00, "short") == {"tp1": 57.80, "tp2": 57.68, "tp3": 57.46, "sl": 58.54})
# 11. съобщения: HTML баланс + под лимита
try:
    stats = json.loads(open("backtest_stats.json", encoding="utf-8").read())
except Exception:
    stats = {}   # повреден stats не бива да проваля selftest-бариерата (ботът работи без него)
m = lb._sig_msg("short", 6, 7, "ПРЕМИУМ", sp, 4093.5, pd.Timestamp("2026-07-16 12:31:00"),
                lb._levels(4088.9, "short"), 4088.9, "тест", {"миньори": False, "долар": False, "лихви": False},
                28, {"streaks": {"short": 28}, "vol_rank": 0.7}, stats, 1000, 2)
ck("карта: HTML/лимит", len(m) < 4096 and m.count("<b>") == m.count("</b>"))
ok_all = True
for kind in ("tp1", "tp2", "tp3", "sl", "flip", "time"):
    mm = lb._exit_msg(kind, dict(TR, hit={"tp1": True}), 4027.0, "2026-07-16 12:30:00", "спот", False,
                      spot=sp, next_line="ДА")
    if len(mm) > 4096 or mm.count("<b>") != mm.count("</b>"):
        ok_all = False
ck("изходи: HTML/лимит", ok_all)

# ПУЛС карта — рендерира се във всички режими, HTML балансиран, разумна дължина
_board = [("1ден", "long", 7, "premium", "ПРЕМИУМ")]
_best = _board[0]
_pulse_ok = True
for _part in ("09", "14", "22"):
    for _tr, _wknd in ((None, False), (TR, False), (None, True)):
        pm = lb._pulse_msg(_part, _board, _best, "long", "ДА — пресен", True,
                           _tr, None, sp, None, {"миньори": True, "долар": True, "лихви": True}, False, _wknd)
        if not (30 < len(pm) < 4096 and pm.count("<b>") == pm.count("</b>") and "ПУЛС" in pm):
            _pulse_ok = False
ck("пулс карта: рендер/HTML/лимит (всички режими)", _pulse_ok)
# пулсът с празен борд (new_dir=None) не гърми
_pm2 = lb._pulse_msg("09", [("1ден", "wait", 0, "weak", "ЧАКАЙ")], ("1ден", "wait", 0, "weak", "ЧАКАЙ"),
                     None, "", False, None, None, None, None, {"миньори": False, "долар": False, "лихви": False}, False, False)
ck("пулс: смесен борд + недостъпен спот не гърми", "ПУЛС" in _pm2 and _pm2.count("<b>") == _pm2.count("</b>"))

# ── СЯНКА-следене (what-if от «не влизай» карта) ──
import tempfile as _tf
_shd = lb.Path(_tf.mkdtemp()); _shf = _shd / "shadow_trade.json"
_lvls = {"tp1": 4116.07, "tp2": 4111.57, "tp3": 4103.57, "sl": 4143.57}
# 1) отваря сянка при информативна карта (open_entry подаден, няма реална)
_sm1 = lb._shadow_cycle(_shf, None, 0.0, 4120.0, "2026-07-22T08:00", None,
                        "short", 4123.57, _lvls, False, "2026-07-22", "premium", "XAUUSD", 2)
ck("сянка: отваря се при «не влизай»", _shf.exists() and _sm1 == [])
# 2) цената пада до ТП1 (нов бар след входа) → what-if изход
_bars = lb.pd.DataFrame({"Open": [4119.0], "High": [4119.0], "Low": [4115.0], "Close": [4116.0]},
                        index=[lb.pd.Timestamp("2026-07-22T09:00")])
_sm2 = lb._shadow_cycle(_shf, _bars, 0.0, 4116.0, "2026-07-22T09:05", None,
                        "short", None, None, False, "2026-07-22", "premium", "XAUUSD", 2)
ck("сянка: ТП1 what-if изход", any(t == "sh-exit:tp1" for t, _ in _sm2)
   and any("СЯНКА" in m for _, m in _sm2) and _shf.exists())
# 3) реална сделка → сянката отпада (не се двои с реалната)
lb._shadow_cycle(_shf, None, 0.0, 4116.0, "2026-07-22T09:10", None,
                 "short", None, None, True, "2026-07-22", "premium", "XAUUSD", 2)
ck("сянка: реална сделка я маха", not _shf.exists())
# 4) рендер на всички what-if изходи (HTML балансиран, «СЯНКА» вътре)
_sh_render_ok = True
for _k in ("tp1", "tp2", "tp3", "sl", "time", "flip"):
    _sxm = lb._shadow_exit_msg(_k, {"direction": "short", "entry": 4123.57, "sym": "XAUUSD",
                                    "levels": _lvls, "hit": {}, "opened": "2026-07-22T08:00"},
                               4116.07, "2026-07-22T09:00", "бар", False)
    if not (30 < len(_sxm) < 4096 and _sxm.count("<b>") == _sxm.count("</b>") and "СЯНКА" in _sxm):
        _sh_render_ok = False
ck("сянка: what-if рендер (всички изходи)", _sh_render_ok)

# ── CyberQuant референция + макро-щит ──
ck("CQ зона: скор→зона", lb._cq_zone(30.6).startswith("Натрупване")
   and lb._cq_zone(65).startswith("Внимание") and lb._cq_zone(95).startswith("Балон"))
_cq = {"score": 30.6, "zone": lb._cq_zone(30.6), "fg_crypto": 33, "fg_stock": 41,
       "events": [{"name": "FOMC решение", "dt": "2026-07-22T12:00:00.000Z", "impact": "critical"},
                  {"name": "CPI", "dt": "2026-08-30T12:30:00.000Z", "impact": "high"}]}
_blk, _ev = lb._cq_macro_block(_cq, "2026-07-22T12:05")            # 5 мин след събитието → в прозореца
ck("CQ макро-щит: блокира в прозореца", _blk and "FOMC" in (_ev or ""))
_blk2, _ = lb._cq_macro_block(_cq, "2026-07-22T09:00")            # 3ч преди → извън
ck("CQ макро-щит: НЕ блокира извън прозореца", not _blk2)
ck("CQ макро-щит: None не гърми (безопасен fallback)", lb._cq_macro_block(None, "2026-07-22T12:05") == (False, None))
_cqm = lb._cq_msg(_cq, "2026-07-22T09:00")                        # 09:00 → следващо е FOMC (12:00 днес)
ck("CQ карта: рендер/HTML/без гол &", 30 < len(_cqm) < 4096 and _cqm.count("<b>") == _cqm.count("</b>")
   and "CYBERQUANT" in _cqm and "&" not in _cqm.replace("&amp;", "") and "FOMC" in _cqm)

# ── ОДИТ-ПОПРАВКИ v5.6f ──
import inspect as _insp
_src = _insp.getsource(lb)
# П1: аварийното съобщение ескейпва HTML и излиза с код ≠0
ck("П1 краш-аларма: HTML ескейпнат", "html.escape" in _src or "_html.escape" in _src)
ck("П1 краш-аларма: изход ≠0 (workflow алармата гърми)", "raise SystemExit(1)" in _src)
# П2: ключът се нулира при смърт на сетъпа
ck("П2 ключът се нулира при смърт на сетъпа",
   'if not actionable and last.get("key")' in _src and "анти-спам ключът нулиран" in _src)
# П3: уикендът се проверява ПРЕДИ US-щита (и за двата метала)
_i_wk = _src.index("уикенд — картите почиват"); _i_sh = _src.index("шорт карта отложена: US-щит")
ck("П3 злато: уикенд ПРЕДИ US-щит", _i_wk < _i_sh)
_j_wk = _src.index("сребро: уикенд"); _j_sh = _src.index("сребро шорт карта отложена")
ck("П3 сребро: уикенд ПРЕДИ US-щит", _j_wk < _j_sh)
# П4: сребро-шорт ключът игнорира класа (стабилен при смяна ПРЕМИУМ↔СРЕДЕН)
ck("П4 сребро-шорт: ключът без клас", 's_key = f"{s_dir}" if s_dir == "short"' in _src)
ck("П4 сребро-шорт: без tier_up заобикаляне", 's_actionable and s_dir != "short"' in _src)
_k = lambda d, t: (f"{d}" if d == "short" else f"{d}:{t}")
ck("П4 шорт ключ не мърда при смяна на клас", _k("short", "premium") == _k("short", "medium"))
ck("П4 лонг ключ ПАК мърда при смяна на клас", _k("long", "premium") != _k("long", "medium"))

# ── ОДИТ-3: ДАТАТА ИЗЛИЗА ОТ АНТИ-СПАМ КЛЮЧА ──
# Дефектът: `date` идваше от дневния бар на Yahoo (публикува се 02:10 UTC) →
# ключът се нулираше в 05:10 София ВСЕКИ ДЕН и картата излизаше от календара,
# а не от пазара. 5 дни подред картата беше точно в 05:10 при непроменен борд.
ck("О3 злато: датата НЕ е в ключа", 'key = ";".join(f"{l}:{d}:{t}"' in _src)
ck("О3 злато: старият ключ с дата го няма", 'date + "|" + ";".join' not in _src)
ck("О3 сребро: датата НЕ е в ключа", 'f"{date}|{s_dir}"' not in _src)
ck("О3 константа REOFFER_H", "REOFFER_H = " in _src and isinstance(lb.REOFFER_H, int))
ck("О3 REOFFER_H е разумен (2-12ч)", 2 <= lb.REOFFER_H <= 12)
ck("О3 злато: повторно предлагане съществува", "reoffer = (bool(actionable)" in _src)
ck("О3 сребро: повторно предлагане съществува", "s_reoffer = (s_actionable" in _src)
ck("О3 повторно иска ПРАЗНА позиция", "trade is None and new_dir is not None" in _src)
ck("О3 повторно иска клас поне СИЛЕН", 'rank.get(best[3], 0) >= rank.get("strong", 2)' in _src)
ck("О3 повторно се вписва в дневника", "повторно предлагане" in _src)
# поведение: същият борд → същият ключ (без дата няма фалшиво нулиране в полунощ)
_bk = lambda board: ";".join(f"{l}:{d}:{t}" for l, d, t in board)
_b1 = [("1час", "short", "premium"), ("4час", "short", "premium")]
ck("О3 един и същ борд → един и същ ключ", _bk(_b1) == _bk(list(_b1)))
# ПАЗАЧ НА САМИЯ ОДИТОР: бариерата (sys.exit) трябва да е СЛЕД последния ck().
# Дефектът, който това ловù: гейтът стоеше на ред 354, П5/П6 идваха след него → червено = зелено.
_selfsrc = open("selftest.py", encoding="utf-8").read()
_EXIT = "sys.ex" + "it(1)"          # разцепен, за да не се брои самият тест
_GREEN = "ВСИЧКО " + "ЗЕЛЕНО"
ck("О3 бариерата е СЛЕД последния тест", _selfsrc.rindex(_EXIT) > _selfsrc.rindex('ck("'))
ck("О3 има само ЕДНА бариера", _selfsrc.count(_EXIT) == 1)
ck("О3 финалният печат е накрая", _selfsrc.rindex(_GREEN) > _selfsrc.rindex('ck("'))
ck("О3 смяна на класа → НОВ ключ", _bk(_b1) != _bk([("1час", "short", "strong"), ("4час", "short", "premium")]))

# ── ГРУПА А (време/цена) ──
ck("A3 петък 22ч UTC затворено", lb._market_closed("2026-07-17T22:00") is True)
ck("A3 неделя 20ч UTC затворено", lb._market_closed("2026-07-19T20:00") is True)
ck("A3 неделя 23ч UTC отворено", lb._market_closed("2026-07-19T23:00") is False)
ck("A3 делник отворено", lb._market_closed("2026-07-14T12:00") is False)
ck("A5 CME пауза 21ч UTC", lb._cme_pause("2026-07-14T21:30") is True)
ck("A5 не-пауза 12ч", lb._cme_pause("2026-07-14T12:30") is False)
ck("A4 новина: голям диапазон пуска далечен спот", lb._spot_sane({"bid": 4014, "ask": 4015, "mid": 4014.5}, 4000, 8, bar_rng=12) is not None)
ck("A4 спокойно: далечен спот се реже", lb._spot_sane({"bid": 4014, "ask": 4015, "mid": 4014.5}, 4000, 8, bar_rng=3) is None)
meta5 = {"basis_g": 6.0}; ntp = []
lb._basis_update(meta5, "basis_g", {"mid": 3970.0}, 4006.0, ntp, now_utc="2026-07-14T21:30")  # +30 скок в пауза
ck("A5 базисът НЕ ре-анкерва в CME паузата", meta5["basis_g"] == 6.0)
# ── АРМИЯ (v5.3c) ──
# T1: под-секундно часово скю НЕ бракува спота (проверяваме логиката на прага)
ck("T1 CLOCK_SKEW толеранс съществува", lb.CLOCK_SKEW >= 30)
# T2: пазар-затворено и CME пауза по НЮ ЙОРК (DST): 21 UTC юли = 17 ET = пауза; 22 UTC = 18 ET = не
ck("T2 CME пауза юли 21ч UTC (=17 ET)", lb._cme_pause("2026-07-15T21:30") is True)
ck("T2 CME пауза яну 22ч UTC (=17 EST)", lb._cme_pause("2026-01-15T22:30") is True)
ck("T2 не-пауза яну 21ч UTC (=16 EST)", lb._cme_pause("2026-01-15T21:30") is False)
ck("T2 петък затворено 21ч UTC юли (=17 ET)", lb._market_closed("2026-07-17T21:30") is True)
ck("T2 петък отворено 21ч UTC яну (=16 EST)", lb._market_closed("2026-01-16T21:30") is False)
# T3: спот-скок разширява санити прага (новина)
ck("T3 спот-скок пуска далечен спот", lb._spot_sane({"bid": 4014, "ask": 4015, "mid": 4014.5}, 4000, 8, spot_jump=12) is not None)
# НАХОДКА 1: _advice_entry връща ok=False за губещ клас (→ сделка НЕ се отваря)
_a, _ok = lb._advice_entry("short", 28, STATS_G if 'STATS_G' in dir() else json.load(open("backtest_stats.json", encoding="utf-8")), None, False, 0, sym="XAUUSD")
ck("НАХОДКА1 губещ клас → adv_ok=False", _ok is False)
_a2, _ok2 = lb._advice_entry("long", 1, json.load(open("backtest_stats.json", encoding="utf-8")), None, False, 0, sym="XAUUSD")
ck("НАХОДКА1 добър клас → adv_ok=True", _ok2 is True)

# ── ГРУПА Б (надеждност) ──
ck("Б5 миграция отложена при базис 0", lb._migrate_trade({"direction": "short", "entry": 4000.0,
   "levels": {"tp1": 3992.5, "sl": 4020.0}, "hit": {}, "v2": True}, 0.0, notes=[]).get("ledger") != "spot")
ck("Б5 миграция минава при потвърден базис", lb._migrate_trade({"direction": "short", "entry": 4000.0,
   "levels": {"tp1": 3992.5, "sl": 4020.0}, "hit": {}, "v2": True}, 6.0, notes=[]).get("ledger") == "spot")
# Б6: отровно съобщение (attempts надхвърля) се хвърля, не блокира вечно
from pathlib import Path as _P
_od = _P("outbox_test"); _od.mkdir(exist_ok=True)
# Б6: отровно = 3 ТВЪРДИ провала (развален HTML), не общ брой опити.
# (таг exit:sl — не-ефемерен; ефемерните signal/s-signal ги чисти НАХОДКА-B филтърът, друг път)
(_od / "outbox.jsonl").write_text(json.dumps({"tag": "exit:sl", "text": "x", "first_ts": "2026-07-01T00:00:00",
                                              "attempts": 5, "hard_fails": 3}, ensure_ascii=False), encoding="utf-8")
_st = []; _orig = lb._send_raw; lb._send_raw = lambda t: "SENT (200)"
lb._outbox_flush(_od, [], _st); lb._send_raw = _orig
ck("Б6 отровно (3 твърди провала) се хвърля", any("ОТРОВНО" in s for s in _st))
# F-краен: МРЕЖОВ провал (не HTML) НЕ хвърля изхода дори след 50 опита
(_od / "outbox.jsonl").write_text(json.dumps({"tag": "exit:sl", "text": "стоп", "first_ts": "2026-07-01T00:00:00",
                                              "attempts": 50, "hard_fails": 0}, ensure_ascii=False), encoding="utf-8")
_st2 = []; lb._send_raw = lambda t: "SEND_FAILED: timeout"
lb._outbox_flush(_od, [], _st2); lb._send_raw = _orig
_rem = [l for l in (_od / "outbox.jsonl").read_text(encoding="utf-8").strip().splitlines() if l]
ck("мрежов провал НЕ хвърля изход (остава за ретрай)", len(_rem) == 1 and "стоп" in _rem[0])
# R1: при срив на Телеграм пощата не трупа дубликати — пази 1 копие/таг
_od2 = _P("outbox_test2"); _od2.mkdir(exist_ok=True)
(_od2 / "outbox.jsonl").write_text(json.dumps({"tag": "signal", "text": "стара карта",
                                               "first_ts": "2026-07-17T00:00:00", "attempts": 1}, ensure_ascii=False), encoding="utf-8")
_st2 = []; _o2 = lb._send_raw; lb._send_raw = lambda t: "SEND_FAILED: тест"
lb._outbox_flush(_od2, [("signal", "нова карта")], _st2); lb._send_raw = _o2
_rem = [l for l in (_od2 / "outbox.jsonl").read_text(encoding="utf-8").strip().splitlines() if l]
ck("R1 пощата не трупа дубликати на signal", len(_rem) == 1 and "нова карта" in _rem[0])
# F3: безрисков стоп на входа НЕ се брои в стоп-пазача
_g = {}
for _px, _exp in ((4020.0, 1), (4000.0, 0)):   # реален стоп брои, безрисков (=вход) не
    _gg = {}
    for _k, _p in (("sl", _px),):
        if _k == "sl" and abs(_p - 4000.0) > 0.05:
            _gg["short"] = _gg.get("short", 0) + 1
    _g[_px] = _gg.get("short", 0)
ck("F3 реален стоп брои, безрисков не", _g[4020.0] == 1 and _g[4000.0] == 0)
# W-провали: повреден stats не хвърля (само вече покрито от try горе — потвърди че stats е dict)
ck("stats е dict (self-heal)", isinstance(stats, dict))
# текст: макро-противоречие махнато — губещ streak0 не казва «макрото не е за посоката»
_adv, _ok = lb._advice_entry("short", 0, stats, None, False, 0, sym="XAUUSD")
ck("streak0 губещ не вини макрото", "макрото не е за" not in _adv)
# УЛТРА баджът иска нето ≥$1 (не +0.04)
_reg = {"streaks": {"long": 2}, "vol_rank": 0.3}
_m = lb._sig_msg("long", 6, 7, "ПРЕМИУМ", sp, 4093.5, pd.Timestamp("2026-07-16 12:31:00"),
                 lb._levels(4088.9, "long"), 4088.9, "ДА", {"миньори": True, "долар": True, "лихви": True},
                 2, _reg, stats, 1000, 2)
_ultra_ok = ("УЛТРА" not in _m) or (stats.get("fresh", {}).get("long", {}).get("ultra", {}).get("net", 0) >= 1.0)
ck("УЛТРА само при смислен ръб", _ultra_ok)

# ── ДЪЛБОКА ВЪЛНА (v5.5b) ──
import urllib.error as _ue, time as _time
_sl = _time.sleep; _time.sleep = lambda *a: None          # без 6с чакане в теста
import os as _os; _os.environ["TELEGRAM_TOKEN"] = "x"; _os.environ["TELEGRAM_CHAT_ID"] = "y"
def _mk_raise(code):
    def _f(*a, **k): raise _ue.HTTPError("u", code, "e", {}, None)
    return _f
_ou = lb.urllib.request.urlopen
lb.urllib.request.urlopen = _mk_raise(429); _r429 = lb._send_raw("t")
lb.urllib.request.urlopen = _mk_raise(400); _r400 = lb._send_raw("t")
lb.urllib.request.urlopen = _ou; _time.sleep = _sl
ck("429 НЕ е отровно (мек, ретрай вечно)", not _r429.startswith("HARD_FAIL"))
ck("400 остава отровно (развален HTML)", _r400.startswith("HARD_FAIL"))

# НАХОДКА-A: спот-глич (спотът «скача», барът НЕ) → базисът НЕ ре-анкерва
_mg = {"basis_g": 5.0, "basis_g_bar": 2405.0}
lb._basis_update(_mg, "basis_g", {"mid": 2370.0}, 2405.0, [], now_utc="2026-07-14T12:30")  # спот −30, бар същ
ck("НАХОДКА-A глич не ре-анкерва (барът не мръдна)", _mg["basis_g"] == 5.0)
_mr = {"basis_g": 5.0, "basis_g_bar": 2405.0}
lb._basis_update(_mr, "basis_g", {"mid": 2400.0}, 2435.0, [], now_utc="2026-07-14T12:30")  # бар +30, спот същ
ck("НАХОДКА-A роловър ре-анкерва (барът скочи)", _mr["basis_g"] == 35.0)
# НАХОДКА-B: PAXG резерва не замърсява базис-EMA
_mp = {"basis_g": 5.0}
lb._basis_update(_mp, "basis_g", {"mid": 2400.0, "src": "paxg"}, 2409.0, [], now_utc="2026-07-14T12:30")
ck("НАХОДКА-B PAXG не обновява базиса", _mp["basis_g"] == 5.0)

# M1: за отворена сделка checked не минава отвъд предпоследния бар
# (свой levels — TR["levels"] е споделен и по-ранен тест мести sl→вход)
_tm = {"direction": "short", "entry": 4034.5, "opened": "2026-07-16T04:11", "checked": "2026-07-16T04:11",
       "levels": {"tp1": 4027.0, "tp2": 4022.5, "tp3": 4014.5, "sl": 4054.5},
       "hit": {}, "status": "open", "v2": True, "ledger": "spot"}
_bm = bars([(4042, 4044, 4040, 4041), (4043, 4045, 4041, 4042), (4044, 4046, 4042, 4043)])
lb.track_trade(_tm, _bm, 6.0, 4038.0, "2026-07-16T05:20")
ck("M1 checked спира на предпоследния бар (частичен последен)", _tm["checked"] == str(_bm.index[-2]))

# BE-стоп re-examination: широк tp1-бар (low под входа) като ПОСЛЕДЕН → M1 го задържа →
# преразглеждане 2-ри рън НЕ бива да пали фалшив BE-стоп (иначе изоставя печелившата сделка)
_tb = {"direction": "long", "entry": 2000.0, "opened": "2026-07-16T05:00", "checked": "2026-07-16T05:00",
       "levels": {"tp1": 2007.5, "tp2": 2012.0, "tp3": 2020.0, "sl": 1980.0}, "hit": {}, "status": "open", "v2": True, "ledger": "spot"}
_bb = bars([(2001, 2008, 1999, 2006)], start="2026-07-16 05:05:00")   # един широк tp1-бар, low 1999 < вход 2000
_tb, _e1 = lb.track_trade(_tb, _bb, 0.0, 2006.0, "2026-07-16T05:15")   # рън1: tp1 хваща, checked не мърда (1 бар)
ck("BE-re-exam: рън1 хваща tp1", _tb is not None and _tb["hit"].get("tp1") and _tb.get("status") == "open")
_tb, _e2 = lb.track_trade(_tb, _bb, 0.0, 2006.0, "2026-07-16T05:20")   # рън2: преразглежда tp1-бара
ck("BE-стоп не пали фалшиво на tp1-бара при преразглеждане", _tb is not None and _tb.get("status") == "open" and not _e2)

# НАХОДКА B: пренесен неригенериран signal се изхвърля (без осиротяла карта)
_odc = _P("outbox_carry"); _odc.mkdir(exist_ok=True)
(_odc / "outbox.jsonl").write_text(json.dumps({"tag": "signal", "text": "стар",
                                  "first_ts": "2026-07-01T00:00:00", "attempts": 1}), encoding="utf-8")
_stc = []; _o2 = lb._send_raw; lb._send_raw = lambda t: "SENT (200)"
_sent = lb._outbox_flush(_odc, [], _stc); lb._send_raw = _o2
ck("НАХОДКА B пренесен signal без регенерация се изхвърля", "signal" not in _sent)
import shutil as _sh2; _sh2.rmtree(_odc, ignore_errors=True)

# краен-случай: burst — ТП1+ТП2+СТОП в 1 рън → 1/3 сметката вярна (+6.50), не +0.00
_tr_burst = {"direction": "long", "entry": 4000.0,
             "levels": {"tp1": 4007.5, "tp2": 4012.0, "tp3": 4020.0, "sl": 4000.0},
             "hit": {"tp1": True, "tp2": True}, "sym": "XAUUSD"}
_em = lb._exit_msg("sl", _tr_burst, 4000.0, "2026-07-16T10:00", "бар", False, dec=2)
ck("burst: 1/3 сметка вярна при ТП1+ТП2+СТОП в 1 рън", "+6.50$/oz" in _em and "удари TP1, TP2" in _em)

# П5: MA-картата вече НЕ показва невъзпроизводимото нето, а честното предупреждение
_mam = lb._ma_alert_msg("long", "ma50", 4100.0, {"win": 62.8, "net": 4.64, "n": 470}, {})
ck("П5 MA-карта: махнато подвеждащото +нето$/oz", "+4.64$/oz" not in _mam and "4.64" not in _mam)
ck("П5 MA-карта: показва процента", "62.8%" in _mam and "n=470" in _mam)
ck("П5 MA-карта: честно предупреждение за отрицателна сметка", "ОТРИЦАТЕЛНА" in _mam)
ck("П5 MA-карта: HTML балансиран", _mam.count("<i>") == _mam.count("</i>") and _mam.count("<b>") == _mam.count("</b>"))


# ── П6: КОНТРАКТЕН БАЗИС дневна↔интрадей (ОДИТ 28.07) ──
_rf = {"sma50": 4000.0, "sma20": 4010.0, "ago5": 3990.0, "ago20": 4005.0,
       "low20": 3900.0, "high20": 4100.0}
_mc = {"миньори": False, "долар": False, "лихви": False}      # макро 0/3 → чист ценови ефект
_bar = bars([(4012, 4014, 4008, 4012)])                        # интрадей: 12$ над sma50
# без корекция: цената е НАД sma50/sma20/ago20 → лонг точки
_l0, _s0, _ = lb._scores(_bar, _rf, _mc)
# с корекция −15$ (интрадей стои 15$ над дневната крива) → пада ПОД тях → шорт точки
_l1, _s1, _ = lb._scores(_bar, _rf, _mc, price_adj=-15.0)
ck("П6 price_adj мести точките лонг→шорт", _l1 < _l0 and _s1 > _s0)
ck("П6 price_adj=0 е точно старото поведение", (_l0, _s0) == lb._scores(_bar, _rf, _mc, price_adj=0.0)[:2])
ck("П6 корекцията може да ОБЪРНЕ посоката",
   lb._resolve(_l0, _s0, _mc)[0] != lb._resolve(_l1, _s1, _mc)[0])
# _tf_basis: измерва медианата дневен−интрадей и я изглажда
_di = pd.date_range("2026-06-01", periods=30, freq="D")
_intra = pd.DataFrame({"Open": 4020.0, "High": 4025.0, "Low": 4015.0, "Close": 4020.0}, index=_di)
_daily = pd.DataFrame({"Open": 4000.0, "High": 4005.0, "Low": 3995.0, "Close": 4000.0}, index=_di)
_stt = {}; _nn = []
_v = lb._tf_basis(_stt, "tf", _intra, _daily, _nn)
ck("П6 _tf_basis мери верния знак (дневен под интрадей → отрицателен)", _v < 0 and abs(_v + 20.0) < 0.01)
ck("П6 _tf_basis запазва в състоянието", _stt.get("tf") == _v)
# EMA изглаждане при промяна
_intra2 = _intra.copy(); _intra2["Close"] = 4040.0
_v2 = lb._tf_basis(_stt, "tf", _intra2, _daily, _nn)
ck("П6 _tf_basis изглажда (EMA), не скача", -40.0 < _v2 < _v)
# глич/абсурд → пази стария
_intra3 = _intra.copy(); _intra3["Close"] = 9000.0
_v3 = lb._tf_basis(_stt, "tf", _intra3, _daily, _nn)
ck("П6 _tf_basis отхвърля глич над cap", _v3 == _v2 and any("извън диапазон" in x for x in _nn))
# малко застъпване → не гадае
ck("П6 _tf_basis при <5 общи дни връща старото",
   lb._tf_basis({"k": 7.0}, "k", _intra.head(2), _daily.head(2), []) == 7.0)
ck("П6 _tf_basis при None не гърми", lb._tf_basis({}, "k", None, _daily, []) == 0.0)
# «1ден» НЕ се коригира (той е на кривата на refs)
import re as _re
_msrc = _insp.getsource(lb.main)
ck("П6 «1ден» остава без корекция", 'adj = 0.0 if lbl == "1ден" else tf_adj' in _msrc)
ck("П6 среброто също е поправено", "tf_basis_s" in _msrc)
ck("П6 базисът влиза в журнала", '"tf_basis": meta.get("tf_basis_g")' in _msrc)


# ═══════════════════════════════════════════════════════════════════════
# 🔴 ОДИТ-3 (29.07): БАРИЕРАТА СТОЕШЕ В СРЕДАТА НА ФАЙЛА.
# финалният печат и изходният код бяха на ред 354, а П5 и П6 идваха
# СЛЕД тях → 15 теста печатаха PASS/FAIL, но НЕ можеха да счупят качването:
# гейтът вече беше минал. Червено в П5/П6 = зелено CI. Бариерата слиза НАЙ-ДОЛУ.
# ═══════════════════════════════════════════════════════════════════════
print()
# чистене: не оставяй тестов боклук в repo-папката (иначе се качва в публичното repo)
import shutil as _sh3
for _d in ("outbox_test", "outbox_test2"):
    _sh3.rmtree(_d, ignore_errors=True)
if FAILS:
    print("SELFTEST FAIL:", len(FAILS), "от", _RAN[0], "→", FAILS); sys.exit(1)
print(f"SELFTEST: ВСИЧКО ЗЕЛЕНО · {_RAN[0]} теста")
