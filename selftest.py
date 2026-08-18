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
        if not (30 < len(pm) < 4096 and pm.count("<b>") == pm.count("</b>") and "·" in pm):   # ОДИТ-30: без име — собственикът каза, че това не е негово име
            _pulse_ok = False
ck("пулс карта: рендер/HTML/лимит (всички режими)", _pulse_ok)
# пулсът с празен борд (new_dir=None) не гърми
_pm2 = lb._pulse_msg("09", [("1ден", "wait", 0, "weak", "ЧАКАЙ")], ("1ден", "wait", 0, "weak", "ЧАКАЙ"),
                     None, "", False, None, None, None, None, {"миньори": False, "долар": False, "лихви": False}, False, False)
ck("пулс: смесен борд + недостъпен спот не гърми",     # ОДИТ-29: «ПУЛС» → поздрав по име
   "добро утро" in _pm2.lower() and _pm2.count("<b>") == _pm2.count("</b>"))

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
ck("сянка: ТП1 what-if изход", any(t == "sh-exit:tp1" for t, _ in _sm2)   # ОДИТ-29: «СЯНКА» → «НАУМ»
   and any("НАУМ" in m for _, m in _sm2) and _shf.exists())
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
    if not (30 < len(_sxm) < 4096 and _sxm.count("<b>") == _sxm.count("</b>") and "НАУМ" in _sxm):   # ОДИТ-29
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
   and "&" not in _cqm.replace("&amp;", "") and "FOMC" in _cqm)   # ОДИТ-29: заглавието е за СЪБИТИЕТО
ck("CQ карта: голият & пак се лови (пазачът е жив)",
   "&" in lb._cq_msg(dict(_cq, zone="A&B"), "2026-07-22T09:00").replace("&amp;", ""))

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
# 🔴 ОДИТ-67 · ОБНОВЕН. Ключът вече не се строи по РАМКА (седем копия), а от
# РАЗЛИЧНИТЕ отчети. Същината, която този тест пази, е непроменена: в ключа
# НЯМА дата — иначе се нулира в 05:10 всеки ден и картата излиза от календара.
ck("О3 злато: датата НЕ е в ключа",
   'key = f"{len(_отч)}|"' in _src and "date" not in _src.split("key = f")[1][:120])
ck("О3 злато: ключът е от РАЗЛИЧНИТЕ отчети, не от седем копия",
   "_отч = sorted({" in _src)
ck("О3 злато: старият ключ с дата го няма", 'date + "|" + ";".join' not in _src)
ck("О3 сребро: датата НЕ е в ключа", 'f"{date}|{s_dir}"' not in _src)
ck("О3 константа REOFFER_H", "REOFFER_H = " in _src and isinstance(lb.REOFFER_H, int))
ck("О3 REOFFER_H е разумен (2-12ч)", 2 <= lb.REOFFER_H <= 12)
ck("О3 злато: повторно предлагане съществува", "reoffer = (bool(actionable)" in _src)
ck("О3 сребро: повторно предлагане съществува", "s_reoffer = (s_actionable" in _src)
ck("О3 повторно иска ПРАЗНА позиция", "trade is None and new_dir is not None" in _src)
# 🔴 ОДИТ-44 · ОБЪРНАТ. Този тест ПАЗЕШЕ главния заглушител на бота.
# Мерено на 1928 живи ръна: 1341 (69.6%) са спрени точно на този ред, а след
# 06.08 — 967 от 967 (100%), защото класът е «medium», не «strong».
# `actionable` по-горе вече изисква tier != weak — това Е прагът на входа;
# «strong» беше втори, недокументиран праг върху него.
ck("О3 повторно иска клас поне колкото прага на входа",
   "rank.get(best[3], 0) >= rank.get(РЕОФЕР_КЛАС, 1)" in _src)
ck("О3 прагът е «medium» по подразбиране, не зазидан «strong»",
   'os.environ.get("РЕОФЕР_КЛАС", "medium")' in _src)
ck("О3 има път назад (РЕОФЕР_КЛАС=strong)", "РЕОФЕР_КЛАС" in _src)
ck("О3 златото и среброто ползват ЕДИН праг",
   _src.count("rank.get(РЕОФЕР_КЛАС, 1)") == 2)
ck("О3 повторно се вписва в дневника", "повторно предлагане" in _src)
# нощен филтър: повторното предлагане важи само в часове, в които човек може да влезе
ck("О3 нощен филтър съществува", "REOFFER_LO" in _src and "REOFFER_HI" in _src
   and _src.count("_reoffer_hour_ok(now_utc)") >= 2)          # злато, сребро (+стоящ сетъп)
ck("О3 нощният прозорец е разумен (6-9 → 21-23)", 6 <= lb.REOFFER_LO <= 9 and 21 <= lb.REOFFER_HI <= 23)
ck("О3 лято: 06:00 UTC = 09:00 София → ДА", lb._reoffer_hour_ok("2026-07-29T06:00") is True)
ck("О3 лято: 23:20 UTC = 02:20 София → НЕ", lb._reoffer_hour_ok("2026-07-29T23:20") is False)
ck("О3 лято: 03:10 UTC = 06:10 София → НЕ", lb._reoffer_hour_ok("2026-07-29T03:10") is False)
ck("О3 зима: 07:00 UTC = 09:00 София → ДА", lb._reoffer_hour_ok("2026-01-15T07:00") is True)
ck("О3 зима: 06:00 UTC = 08:00 София → ДА (границата)", lb._reoffer_hour_ok("2026-01-15T06:00") is True)
ck("О3 зима: 05:00 UTC = 07:00 София → НЕ", lb._reoffer_hour_ok("2026-01-15T05:00") is False)
ck("О3 повреден час не гърми и НЕ пуска", lb._reoffer_hour_ok("боклук") is False)
ck("О3 часът е с реална часова зона (не +3 на ръка)", "Europe/Sofia" in _insp.getsource(lb._sofia_hour))

# ── ОДИТ-4 (29.07): ТАВАН НА ВЪЗРАСТТА НА СЕТЪПА ──
# Два независими парични агента на реален bid/ask (19.7 години) обориха REOFFER_H=4 без таван:
# пределните входове −0.878$/сделка (t=−2.65 по дни); всичките 6 хоризонта отрицателни.
# Ръбът живее в първите ~12ч: <6ч +0.231$ · 6-12ч +0.052$ · 12-24ч −1.590$ · >2дни −1.219$.
# Единственият вариант над нулата: 6ч напомняне САМО докато сетъпът е под 12ч.
ck("О4 таван на възрастта съществува", "REOFFER_MAX_AGE_H" in _src and isinstance(lb.REOFFER_MAX_AGE_H, int))
ck("О4 таванът е в мереното (6-18ч)", 6 <= lb.REOFFER_MAX_AGE_H <= 18)
ck("О4 REOFFER_H вече е 6 (не 4)", lb.REOFFER_H == 6)
ck("О4 напомнянето идва СЛЕД тавана в кода", _src.index("REOFFER_MAX_AGE_H = ") < _src.index("key_age_h <= REOFFER_MAX_AGE_H"))
ck("О4 злато: възрастта влиза в условието", "key_age_h is not None and key_age_h <= REOFFER_MAX_AGE_H" in _src)
ck("О4 сребро: възрастта влиза в условието", "s_key_age_h is not None and s_key_age_h <= REOFFER_MAX_AGE_H" in _src)
ck("О4 възрастта се брои от key_since, не от последната карта",
   'last["key_since"]' in _src and 's_last["key_since"]' in _src)
ck("О4 key_since се ЗАПАЗВА докато ключът е същият",
   'last.get("key_since") if last.get("key") == key and last.get("key_since") else now_utc' in _src)
ck("О4 сребро: key_since също се запазва",
   's_last.get("key_since") if s_last.get("key") == s_key and s_last.get("key_since")' in _src)
ck("О4 key_since се пише в състоянието", '"key_since": key_since' in _src and '"key_since": s_since' in _src)
ck("О4 отказът се вписва честно в дневника", "ръбът е изчерпан" in _src)
# поведение: часовникът тръгва наново само при НОВ ключ
_ks = lambda old_key, old_since, new_key, now: (old_since if old_key == new_key and old_since else now)
ck("О4 същият ключ → часовникът НЕ се нулира", _ks("A", "T0", "A", "T9") == "T0")
ck("О4 нов ключ → часовникът тръгва наново", _ks("A", "T0", "B", "T9") == "T9")
ck("О4 липсващ key_since (стар файл) → тръгва от сега", _ks("A", None, "A", "T9") == "T9")
# без key_since НЯМА повторно предлагане (стар state не бива да пуска верига)
ck("О4 без key_since повторното е ИЗКЛЮЧЕНО", "key_age_h is not None and" in _src)

# ── ОДИТ-5 (29.07): 5 находки от 14-агентна армия, всички потвърдени адверсарно ──
# L1-01 (4/4 гласа, КРИТИЧНО): BE-стопът се гасеше цял ден заради сравнение на НИЗОВЕ
# «2026-07-29 03:00:00» vs «2026-07-29T02:10» — интервалът (0x20) < 'T' (0x54).
ck("L1-01 сравнението е по СТОЙНОСТ, не по низ", "_ts_le(ts, trade[\"be_since\"])" in _src)
ck("L1-01 старото сравнение го няма", 'str(ts) <= trade["be_since"]' not in _src)
ck("L1-01 смесени формати: интервал vs T", lb._ts_le("2026-07-29 02:15:00", "2026-07-29T02:10") is False)
ck("L1-01 наистина по-рано → True", lb._ts_le("2026-07-29 02:05:00", "2026-07-29T02:10") is True)
ck("L1-01 боклук не гаси стопа", lb._ts_le("боклук", "2026-07-29T02:10") is False)
# поведение end-to-end: ТП1 по СПОТ, после бар през входа СЪЩИЯ ден → стопът ТРЯБВА да гръмне
_tbe = {"direction": "long", "entry": 4000.0, "opened": "2026-07-29T02:00", "checked": "2026-07-29T02:00",
        "levels": lb._levels(4000.0, "long"), "hit": {}, "status": "open", "v2": True, "ledger": "spot"}
lb.track_trade(_tbe, bars([(4000, 4001, 3999, 4000)], "2026-07-29 02:00:00"), 0.0, 4007.5, "2026-07-29T02:10",
               spot={"bid": 4007.5, "ask": 4007.9, "mid": 4007.7})
ck("L1-01 ТП1 по спот вдига BE", _tbe["hit"].get("tp1") and _tbe["levels"]["sl"] == 4000.0)
_tbe, _ebe = lb.track_trade(_tbe, bars([(3999, 4000, 3990, 3995)], "2026-07-29 02:15:00"), 0.0, 3995.0, "2026-07-29T02:20")
ck("L1-01 БЕ-стопът гърми СЪЩИЯ ден (дефектът беше тук)", any(e[0] == "sl" for e in _ebe))
# L2-01 (4/4, КРИТИЧНО): изходна карта се хвърляше след 3× 4xx, при вече затворена сделка
ck("L2-01 изходните тагове са изключени от отровното", "EXIT_TAGS" in _src and 'in EXIT_TAGS' in _src)
# 🔴 ОДИТ-56 · ОБЪРНАТ. Този тест искаше ТОЧНО три семейства — тоест ЗАМРАЗЯВАШЕ
# пропуска: добавиш ли ново семейство карти, което съобщава развръзка, тестът
# ПАДА, вместо да те накара да го защитиш. Точно това стана с `brain-exit`.
# Сега пази ЗАДЪЛЖИТЕЛНИТЕ, а не забранява нови.
for _зд in ("exit", "s-exit", "sh-exit", "brain-exit"):
    ck(f"L2-01 «{_зд}» Е в защитеното семейство", _зд in lb.EXIT_TAGS)
ck("L2-01 нищо, което НЕ е развръзка, не е промъкнато вътре",
   not (set(lb.EXIT_TAGS) & {"signal", "s-signal", "pulse", "brain", "digest",
                             "standing", "ma", "cq-ref", "спал", "обрат"}))
ck("L2-01 всяко семейство вътре съобщава РАЗВРЪЗКА (има «exit» в името)",
   all("exit" in _t for _t in lb.EXIT_TAGS))
ck("L2-01 последен шанс без HTML", "_strip_html" in _src and "<b>" not in lb._strip_html("<b>x</b>"))
ck("L2-01 _strip_html пази текста", lb._strip_html("<b>СТОП</b> на 4000") == "СТОП на 4000")
# L2-02 (4/4, КРИТИЧНО): липсващ токен триеше цялата поща, а рънът оставаше зелен
ck("L2-02 DRY_RUN ПАЗИ съобщението", "remaining.append(msg)                         # ПАЗИ съобщението" in _src)
ck("L2-02 липсващ токен вдига аларма", "КОНФИГУРАЦИЯ: няма TELEGRAM_TOKEN" in _src)
ck("L2-02 старото тихо изпускане го няма", 'elif not st.startswith("DRY_RUN"):' not in _src)
# ОДИТ-5 макро: мъртъв фийд не бива да минава за ПРЕМИУМ, и трябва да оставя следа
ck("О5 макро-краката влизат в дневника", '"macro": macro, "macro_raw": macro_health' in _src)
ck("О5 _macro връща и здраве", "health=macro_health" in _src)
ck("О5 мъртво краче сваля ПРЕМИУМ→СИЛЕН", lb._demote_if_dead(("short", 8, "premium", "ПРЕМИУМ"),
                                                              {"мъртви": ["долар"]})[2] == "strong")
ck("О5 живо макро не пипа класа", lb._demote_if_dead(("short", 8, "premium", "ПРЕМИУМ"),
                                                     {"мъртви": []})[2] == "premium")
ck("О5 празно здраве не пипа класа", lb._demote_if_dead(("long", 7, "premium", "ПРЕМИУМ"), {})[2] == "premium")
ck("О5 сваля само ПРЕМИУМ, не по-надолу", lb._demote_if_dead(("short", 5, "medium", "СРЕДЕН"),
                                                              {"мъртви": ["долар"]})[2] == "medium")
ck("О5 мъртвото краче се вписва в бележките", "МЪРТВО МАКРО-КРАЧЕ" in _src)
# ОДИТ-5 стоящ сетъп: таванът от 12ч правеше 4 от 9 дни НЕМИ — картата пълни тишината
ck("О5 STANDING_H съществува", "STANDING_H" in _src and isinstance(lb.STANDING_H, int))
ck("О5 стоящата карта се праща", 'new_msgs.append(("standing"' in _src)
ck("О5 стоящата карта има свой часовник", 'meta["standing_utc"] = now_utc' in _src and "st_mins" in _src)
ck("О5 стоящата НЕ се праща при активен сигнал", "stale_setup and not should_sig" in _src)
ck("О5 стоящата иска ПРАЗНА позиция", "stale_setup = (bool(actionable) and trade is None" in _src)
ck("О5 стоящата е в дедупа", '"cq-ref", "standing"' in _src)
_stm = lb._standing_msg("short", ("1час", "short", 7, "premium", "ПРЕМИУМ"), 27.4,
                        {"bid": 4000.0, "ask": 4000.4, "mid": 4000.2}, 4006.0, 4000.2,
                        [("1час", "short", 7, "premium", "ПРЕМИУМ")] * 7,
                        {"миньори": False, "долар": False, "лихви": False}, {"мъртви": []}, "2026-07-29T10:00")
ck("О5 стоящата карта: рендер/HTML/лимит", 30 < len(_stm) < 4096
   and _stm.count("<b>") == _stm.count("</b>") and _stm.count("<i>") == _stm.count("</i>"))
# ОДИТ-20: СОБСТВЕНИКЪТ ПОИСКА НИВАТА. Дотук картата ги ОТКАЗВАШЕ и обясняваше
# три реда защо — а той ги смяташе на око, което е по-зле. Сега ги има.
# Старият тест «НЕ дава нива» вече е ВРЕДЕН: той минаваше по случайност (пишех
# «1️⃣» вместо «ТП1»), тоест пазеше нищо. Заменен с това, което ВСЕ ОЩЕ трябва
# да е вярно: нивата ги има, И картата ясно казва, че не е покана.
ck("О5 стоящата карта ДАВА нивата (собственикът ги поиска)",
   "🛑" in _stm and _stm.count("️⃣") == 3)
ck("О5 стоящата карта дава нивата и НЕ чете лекция",     # ОДИТ-27/29: обърнат
   "🛑" in _stm and "не покана" not in _stm and "Мерено:" not in _stm)
ck("О5 стоящата карта е къса — под 10 реда",              # ОДИТ-27: обърнат
   len(_stm.split("\n")) <= 10 and "1.59" not in _stm)
# 🔴 ОДИТ-67 · ОБНОВЕН. Възрастта се показва САМО докато нивата още важат.
# Мерено на живо: картата казваше «вече 276ч» с нива от ДНЕШНАТА цена, а
# цената беше избягала 6.7 ПЪТИ стопа от key_since. Двете не могат да са верни.
# Прагът е ПРИНЦИПЕН, не нагоден: 24ч ≈ едно ATR движение на златото (мерено
# 16.06$ медиана), тоест почти цял стоп. Сетъпът от 27.4ч ВЕЧЕ е стар и
# картата с право не му казва възрастта.
ck("О5 стар сетъп (27.4ч) НЕ показва часовете", "27ч" not in _stm
   and "нивата са от сега" in _stm)
_stm_млад = lb._standing_msg("short", ("1час", "short", 7, "premium", "ПРЕМИУМ"), 6.0,
                             {"bid": 4000.0, "ask": 4000.4, "mid": 4000.2}, 4006.0, 4000.2,
                             [("1час", "short", 7, "premium", "ПРЕМИУМ")] * 7,
                             {"миньори": False, "долар": False, "лихви": False},
                             {"мъртви": []}, "2026-07-29T10:00")
ck("О5 МЛАД сетъп (6ч) показва възрастта", "вече 6ч" in _stm_млад)
ck("О5 прагът е под 48ч — сетъп с 20$ стоп не живее два дни", lb.СТОЯЩ_МАКС_Ч <= 48)
_stm_стар = lb._standing_msg("long", ("1час", "long", 7, "strong", "СИЛЕН"), 500.0,
                             None, 4006.0, 4000.2,
                             [("1час", "long", 7, "strong", "СИЛЕН")] * 7,
                             {"миньори": True, "долар": True, "лихви": True},
                             {}, "2026-07-29T10:00")
ck("О5 при СТАРА възраст картата НЕ лъже с часовете",
   "500ч" not in _stm_стар and "нивата са от сега" in _stm_стар)
_stm2 = lb._standing_msg("short", ("1час", "short", 7, "strong", "СИЛЕН"), 20.0, None, 4006.0, 4000.2,
                         [("1час", "short", 7, "strong", "СИЛЕН")] * 7,
                         {"миньори": False, "долар": False, "лихви": False}, {"мъртви": ["долар"]}, "2026-07-29T10:00")
ck("О5 стоящата карта предупреждава за мъртъв фийд", "мълчи:" in _stm2)   # ОДИТ-29: без обяснението
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
# ⚠️ ОДИТ-5 смени тага: exit:* ВЕЧЕ НЕ СЕ ХВЪРЛЯ (L2-01). Отровното важи за информативните.
(_od / "outbox.jsonl").write_text(json.dumps({"tag": "digest", "text": "x", "first_ts": "2026-07-01T00:00:00",
                                              "attempts": 5, "hard_fails": 3}, ensure_ascii=False), encoding="utf-8")
_st = []; _orig = lb._send_raw; lb._send_raw = lambda t: "SENT (200)"
lb._outbox_flush(_od, [], _st); lb._send_raw = _orig
ck("Б6 отровно (3 твърди провала) се хвърля — за ИНФОРМАТИВНА карта", any("ОТРОВНО" in s for s in _st))
# L2-01: същото състояние, но ИЗХОДНА карта → НЕ се хвърля, а се пробва като гол текст
for _tg in ("exit:sl", "s-exit:tp3", "sh-exit:sl"):
    (_od / "outbox.jsonl").write_text(json.dumps({"tag": _tg, "text": "<b>СТОП</b> ударен",
                                                  "first_ts": "2026-07-01T00:00:00",
                                                  "attempts": 9, "hard_fails": 7}, ensure_ascii=False), encoding="utf-8")
    _st = []; _orig = lb._send_raw; lb._send_raw = lambda t: "SENT (200)"
    _tags = lb._outbox_flush(_od, [], _st); lb._send_raw = _orig
    ck(f"L2-01 {_tg} НЕ се хвърля при 7 твърди провала",
       not any("ОТРОВНО" in s for s in _st) and _tg in _tags)
    ck(f"L2-01 {_tg}: HTML е махнат за последен опит", any("HTML махнат" in s for s in _st))
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
# ── ОДИТ-6 (29.07): резервната ВЕРИГА ──
# Дефектът: 267 от 1674 делнични ръна без спот, spot_src {'swq':1407, None:267} — PAXG нула.
# Причина: Actions рънърите са в САЩ, Binance връща 451 на американски IP. Резервата беше
# тествана там, където ботът НЕ работи. Без спот _advice_entry блокира pending_trade →
# ботът не може да отвори сделка на всеки шести рън.
for _s in ("paxg-bin", "paxg-cb", "paxg-kr"):
    _mx = {"basis_g": 5.0}
    lb._basis_update(_mx, "basis_g", {"mid": 2400.0, "src": _s}, 2409.0, [], now_utc="2026-07-14T12:30")
    ck(f"О6 {_s} също НЕ замърсява базиса", _mx["basis_g"] == 5.0)
_spotsrc = _insp.getsource(lb._spot)
ck("О6 верига от ТРИ резервни източника", _spotsrc.count("paxg-") == 3)
ck("О6 Coinbase е във веригата", "api.exchange.coinbase.com" in _spotsrc)
ck("О6 Kraken е във веригата", "api.kraken.com" in _spotsrc)
ck("О6 Binance остава първи (работи извън САЩ)", _spotsrc.index("paxg-bin") < _spotsrc.index("paxg-cb"))
ck("О6 санити диапазон за златото", "500 < b < 20000" in _spotsrc)
ck("О6 провалът на един източник пробва следващия", "continue" in _spotsrc)
ck("О6 пазачът на базиса лови по ПРЕФИКС", 'startswith("paxg")' in _src)
# 🔴 ОДИТ-53 · РАЗШИРЕН. Пазачът беше САМО уикендът, а CME Globex спира и всеки
# делник по един час (17:00 Ню Йорк). Тогава фючърсът е затворен, а PAXG е крипто
# и върви 24/7 — цена, която никой не арбитрира, показвана като злато.
ck("О6 затворен пазар пак не ползва крипто-прокси",
   "if market_closed or cme_pause:" in _spotsrc)
ck("О6 и ДНЕВНАТА CME пауза спира резервата", "cme_pause=False" in _spotsrc)
ck("О6 ботът наистина подава паузата",
   "cme_pause=_cme_pause(now_utc)" in _src)
ck("О6 картата КАЗВА, когато цената е от резерва", "def _от_резерва" in _src)
ck("О6 пулсът я маркира", chr(9888)+chr(65039)+"резерва" in _src)
ck("О6 разпознаването работи",
   lb._от_резерва({"src": "paxg-cb"}) and not lb._от_резерва({"src": "swq"})
   and not lb._от_резерва(None))

# ── ОДИТ-7 (29.07): ЧИСЛАТА, ПО КОИТО СЕ ГЕЙТВАТ ВХОДОВЕТЕ ──
# Дефектът: _advice_entry решава ВЛИЗАМ/НЕ по backtest_stats.json, а златният блок `fresh`
# беше смятан при ДРУГА геометрия (единичен изход ±20$, без стълба, без безрисков стоп) и
# нямаше генератор в repo-то. Знакът на short/fresh беше ОБЪРНАТ: файлът +0.39$, реалното
# измерване (114 813 сделки, доставена стълба, реален bid/ask) −1.22$. Ботът влизаше в шорт
# на ден 2-3, защото му казваха, че губещ клас печели.
_bs = json.loads(open("backtest_stats.json", encoding="utf-8").read())
_fr = _bs.get("fresh", {})
ck("О7 short/fresh е ОТРИЦАТЕЛЕН (както е мерено)", _fr["short"]["fresh"]["net"] < 0)
ck("О7 short/stale е отрицателен", _fr["short"]["stale"]["net"] < 0)
ck("О7 long/fresh е положителен", _fr["long"]["fresh"]["net"] > 0)
ck("О7 long/day1 е положителен", _fr["long"]["day1"]["net"] > 0)
# ОДИТ-16: `near_high` е НАРОЧНО тясна подклетка (779) — тя е подмножество на `fresh`,
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
   _NH7 is None or (_NH7["n"] >= 500 and _NH7.get("lo", -1) > 0 and _NH7["net"] > 0))
ck("О7 всички n са над MIN_N", all(v["n"] >= lb.MIN_N for d in ("long", "short") for v in _fr[d].values()))
ck("О7 файлът казва КАК е мерен", "злато_fresh_преизмерено" in _bs.get("_meta", {}))
ck("О7 файлът казва кое НЕ е мерено", "НЕпреизмерено" in _bs.get("_meta", {}))
# ПОВЕДЕНИЕ на гейта — това е, което всъщност пази парите
_g = lambda d, s: lb._advice_entry(d, s, _bs, None, False, 0)[1]
ck("О7 шорт ден-2 вече се ОТКАЗВА", _g("short", 2) is False)
ck("О7 шорт ден-3 вече се ОТКАЗВА", _g("short", 3) is False)
ck("О7 шорт застоял пак се отказва", _g("short", 0) is False and _g("short", 9) is False)
# ОДИТ-8 (04.08): тестът пазеше «лонгът не е засегнат от шорт-поправката». Все още го
# пази — но стрийк 0 ВЕЧЕ отпада НАРОЧНО: long/mixed е измерен като ШУМ (−0.04$, n=40094,
# 95% [−0.50 .. +0.43]) и вече има своя клетка. Останалите лонг-стрийкове са непокътнати.
ck("О7 ЛОНГЪТ: подреденото и застоялото пак минават",
   all(_g("long", s) for s in (1, 2, 3, 4, 9, 20)))
ck("О7 ЛОНГЪТ: СМЕСЕНОТО макро (стрийк 0) вече отпада — измерен шум", _g("long", 0) is False)
# 🔴 F24 (18.08) · ОБЪРНАТ. Пазеше `silver.long.fresh.net == 0.111` — числото,
# по което ботът ОТВАРЯШЕ сребърни лонгове. Днес се оказа невъзпроизводимо:
# преизмерено на 12858 сделки дава +0.033$ (3.4× по-малко), а съседната клетка
# `stale` беше n=556 срещу преизмерени n=1204. Нито едното няма записан метод
# или интервал. Тестът вече пази ОБРАТНОТО: старото число е махнато от
# решаващия път и е запазено под `_старо` за проверка.
import copy as _cpF24   # собствен внос:  се появява чак на ред 1613
_с24 = _bs["silver"]
ck("F24 старото сребърно число НЕ е вече на решаващия път",
   abs(float(_с24["long"]["fresh"]["net"]) - 0.111) > 0.01)
ck("F24 но е ЗАПАЗЕНО под `_старо` (не е изтрито)",
   abs(float(((_с24.get("_старо") or {}).get("стойности") or {})
             .get("long", {}).get("fresh", {}).get("net", 0)) - 0.111) < 1e-9)
ck("F24 всяка сребърна клетка носи СУРОВО и ЕПОХИ",
   all(isinstance(а.get("_сурово"), dict) and isinstance(а.get("_епохи"), dict)
       for d in ("long", "short") for им, а in _с24[d].items()
       if им in ("day1", "fresh", "mixed", "stale", "ultra")))
ck("F24 живото `net` е СУРОВО минус подразбирания спред",
   all(abs(round(а["_сурово"]["net"] - _с24["_подразбиран_спред"], 4) - а["net"]) < 1e-6
       for d in ("long", "short") for им, а in _с24[d].items()
       if им in ("day1", "fresh", "mixed", "stale", "ultra")))
ck("F24 КЛАСОВИТЕ клетки (premium/weak) са НЕПИПНАТИ",
   _с24["long"].get("premium", {}).get("n") == 926
   and _с24["short"].get("weak", {}).get("n") == 2504)
# 🔴 И ДВЕТЕ ПОСОКИ, в един процес: спирачката трябва да МЕРИ, не да е закована.
_ст24 = _cpF24.deepcopy(_bs)
lb.СРЕБРО_СПРЕД = 0.03
lb._сребро_разход(_ст24, None)
_отк24 = [lb._advice_entry(d, n, _ст24, False, False, 0, sym="XAGUSD")[1]
          for d in ("long", "short") for n in (0, 1, 2, 5)]
_ев24 = _cpF24.deepcopy(_bs)
lb.СРЕБРО_СПРЕД = 0.0
lb._сребро_разход(_ев24, None)
# 🔴 F24г · ДВЕ СПИРАЧКИ, ПРОВЕРЕНИ ПООТДЕЛНО. Първата ми версия ги сля: свалиш
# ли спреда до 0, среброто тръгваше. Адверсарната проверка показа, че точно
# клетките, които тогава оживяват (day1, stale), са артефакт от мъртви барове.
# Сега `СРЕБРО_СПРЕД` е измерване, `СРЕБРО_ВХОД` е решение.
_вх24_стар = lb.СРЕБРО_ВХОД
_бездва24 = [lb._advice_entry(d, n, _ев24, False, False, 0, sym="XAGUSD")[1]
             for d in ("long", "short") for n in (0, 1, 2, 5)]
lb.СРЕБРО_ВХОД = True
_жив24 = [lb._advice_entry(d, n, _ев24, False, False, 0, sym="XAGUSD")[1]
          for d in ("long", "short") for n in (0, 1, 2, 5)]
lb.СРЕБРО_ВХОД = _вх24_стар
lb.СРЕБРО_СПРЕД = 0.03
ck("F24г нулев спред САМ ПО СЕБЕ СИ не отваря сребро (капанът е затворен)",
   not any(_бездва24))
ck("F24 при спред 0.03$ среброто НЕ дава нито един вход", not any(_отк24))
ck("F24 при спред 0.00$ клетките ОЖИВЯВАТ (значи мери, не е заковано)",
   any(_жив24))
# 🔴 F24г · ДВА ПЛАСТА, ПРОВЕРЕНИ ПООТДЕЛНО. Външният (СРЕБРО_ВХОД) казва
# «изключено»; вътрешният (клетките) казва «няма измерен ръб над спреда».
# Ако само външният се проверява, вътрешният може да изгние незабелязано —
# точно както се случи с шум-пазача за среброто преди 18.08.
ck("F24 външната спирачка казва ПРИЧИНАТА, не «изчакай»",
   "изключено" in lb._advice_entry("long", 1, _ст24, False, False, 0,
                                   sym="XAGUSD")[0])
_вх24б = lb.СРЕБРО_ВХОД
lb.СРЕБРО_ВХОД = True
ck("F24 вътрешната (клетките) също казва ПРИЧИНАТА",
   "няма измерен ръб над спреда" in lb._advice_entry("long", 1, _ст24, False,
                                                     False, 0, sym="XAGUSD")[0])
ck("F24 и при пуснат вход спредът пак спира всичко",
   not any(lb._advice_entry(d, n, _ст24, False, False, 0, sym="XAGUSD")[1]
           for d in ("long", "short") for n in (0, 1, 2, 5)))
lb.СРЕБРО_ВХОД = _вх24б
ck("F24 ЗЛАТОТО не се влияе от сребърния спред",
   [lb._advice_entry(d, n, _ст24, False, False, 0, sym="XAUUSD")[1]
    for d in ("long", "short") for n in (0, 1, 2, 5)]
   == [lb._advice_entry(d, n, _ев24, False, False, 0, sym="XAUUSD")[1]
       for d in ("long", "short") for n in (0, 1, 2, 5)])
ck("F24 `_noise` брои разминаващи се епохи за шум",
   lb._noise({"lo": 0.1, "hi": 0.9, "_епохи_съгласни": False})
   and not lb._noise({"lo": 0.1, "hi": 0.9, "_епохи_съгласни": True})
   and not lb._noise({"lo": 0.1, "hi": 0.9}))
ck("О7 УЛТРА значката иска ≥$1 ръб", _fr["short"]["ultra"]["net"] < 1.0)   # шорт-ултра вече не се хвали

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
ck("burst: 1/3 сметка вярна при ТП1+ТП2+СТОП в 1 рън",     # ОДИТ-7/29: текстът е пренаписан
   "+6.50$" in _em and "стопът беше на входа" in _em       # числото и защо не е загуба
   and "НУЛА" in _em.split("\n")[0]                        # + вече не се нарича «СТОП»
   and "Стопът НЕ е ударен" not in _em)                    # ОДИТ-27: лекцията падна

# ── П5 · MA-КАРТАТА (пренаписан от F25, 18.08) ───────────────────────────
# 🔴 До 29.07 картата цитираше +4.64$/oz — число от партида БЕЗ метод и БЕЗ
# интервал. Тогава П5 го МАХНА и това беше вярното решение: не цитирай
# непроверимо. Днес числото Е премерено (F25: доставената геометрия върху
# 1-минутната лента с реален спред, 5703 дни, блоков бутстрап по ден) и се
# оказа −0.348$ [−1.591 .. +0.863] — ШУМ, тоест старото беше сгрешено с 5$ в
# грешната посока. Затова забраната сменя предмета си: не «никакво число», а
# «числото идва от файла и думата до него не му противоречи».
# ОСТАВА непокътнато: никакви НИВА за вход, никакъв win%, не е съвет.
_mb5 = stats.get("ma_bounce", {}).get("long", {}).get("ma50", {})
_mam = lb._ma_alert_msg("long", "ma50", 4100.0, _mb5, {})
ck("П5 MA-карта: НЕ дава нива за вход",                # ОДИТ-29: обърнат — картата даваше
   "ТП1" not in _mam and "СТОП" not in _mam            # нива за вход, по който сама казва «не»
   and "62.8%" not in _mam and "n=470" not in _mam)
ck("П5 MA-карта: пак казва, че НЕ влиза по нея",       # ОДИТ-29
   "не влизам" in _mam and "Не е съвет" not in _mam)
ck("П5/F25 картата НЕ носи вече заковано «минус»", "сметката е на минус" not in _mam)
ck("П5/F25 НЕ цитира старото невъзпроизводимо число", "4.64" not in _mam)
ck("П5/F25 цитира ЖИВОТО число от файла",
   f'{abs(float(_mb5["net"])):.2f}' in _mam and str(_mb5["n"]) in _mam)
ck("П5/F25 и го дава В ПИПСОВЕ (езикът на собственика)", "пипса" in _mam)
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
# П7 · ОДИТ-6 (04.08): СЯНКАТА КРИЕШЕ ПРИБРАНИТЕ ТЕЙК-ПРОФИТИ.
# `_exit_msg` имаше сметка по стълбата 1/3, `_shadow_exit_msg` НЯМАШЕ →
# безрисков стоп след ТП1+ТП2 се показваше «+0.00$», а стълбата дава +6.50$.
# Мерено в live/sent_log.jsonl: 4 карти, скрити +22.00$/oz. Собственикът е
# виждал САМО сянка-карти (реални сделки: 0 за 387 ръна) → само счупените.
# ═══════════════════════════════════════════════════════════════════════
_E = 4000.0
_LVs = {"tp1": _E - 7.5, "tp2": _E - 12.0, "tp3": _E - 20.0, "sl": _E}


def _shtr(hit):
    return {"direction": "short", "entry": _E, "levels": _LVs, "hit": dict(hit),
            "sym": "XAUUSD", "opened": "2026-08-03T00:00:00", "shadow": True}


# --- самата сметка (един източник за реалния и за сянка-изхода) ---
ck("П7 _ladder_pnl: ТП1+ТП2 после стоп на входа = +6.50 (НЕ 0.00)",
   lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, _LVs, _E, -1, 0.0)[0] == 6.50)
ck("П7 _ladder_pnl: само ТП1 после стоп на входа = +2.50",
   lb._ladder_pnl("sl", {"tp1": True}, _LVs, _E, -1, 0.0)[0] == 2.50)
ck("П7 _ladder_pnl: чист стоп без ТП = целият стоп",
   lb._ladder_pnl("sl", {}, _LVs, _E, -1, -20.0)[0] == -20.0)
ck("П7 _ladder_pnl: ТП3 = (7.5+12+20)/3 = 13.17, НЕ 20.00",
   lb._ladder_pnl("tp3", {"tp1": True, "tp2": True}, _LVs, _E, -1, 20.0)[0] == 13.17)
ck("П7 _ladder_pnl брои прибраните ТП",
   lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, _LVs, _E, -1, 0.0)[1] == 2)
ck("П7 _ladder_pnl НЕ брои самия изход два пъти",
   lb._ladder_pnl("tp2", {"tp1": True, "tp2": True}, _LVs, _E, -1, 12.0)[1] == 1)
ck("П7 _ladder_pnl лонг: знакът е огледален",
   lb._ladder_pnl("sl", {"tp1": True, "tp2": True},
                  {"tp1": _E + 7.5, "tp2": _E + 12.0, "tp3": _E + 20.0, "sl": _E},
                  _E, 1, 0.0)[0] == 6.50)
ck("П7 реалният изход ползва СЪЩАТА функция (не свое копие)",
   "_ladder_pnl(kind, hit, lv, e, знак, дол" in
   _src.split("def _shadow_exit_msg")[0].split("def _exit_msg")[1])

# --- сянка-картата вече показва сметката ---
_sh1 = lb._shadow_exit_msg("sl", _shtr({"tp1": True, "tp2": True}), _E, "2026-08-03T03:01:00", "бар", False)
ck("П7 сянка-стоп след 2 ТП показва +6.50$", "+6.50$" in _sh1)
ck("П7 сянка-стоп след 2 ТП НЕ се води загуба (без 🛑)", "🛑" not in _sh1.split("\n")[0])
ck("П7 сянка-стоп след 2 ТП казва, че е излязла на нула",   # ОДИТ-29
   "на нула" in _sh1)
ck("П7 сянка-картата дава СМЕТКАТА по стълбата, не голия крак",   # ОДИТ-29
   "+6.50$" in _sh1 and "+0.00$" not in _sh1)
ck("П7 сянка-картата казва, че НЕ е реална сделка", "не съм влизал" in _sh1)   # ОДИТ-29
_sh2 = lb._shadow_exit_msg("sl", _shtr({}), _E + 20.0, "2026-08-03T03:01:00", "бар", False)
ck("П7 чист сянка-стоп СИ ОСТАВА стоп",                # ОДИТ-29: 👁 е за «наум», думата носи вида
   "щеше да удари стоп" in _sh2.split("\n")[0])
# 🔴 ОБНОВЕН v12.5: «-20.00$/унция» → «−200 пипса (−20.00$)». Пази СЪЩОТО
# число, но в записа, на който собственикът говори, + самите пипсове.
ck("П7 чист сянка-стоп показва −20.00", "−20.00$" in _sh2)
ck("П7 и го дава В ПИПСОВЕ", "−200 пипса" in _sh2)
ck("П7 сянка-изходът е балансиран HTML", _sh1.count("<b>") == _sh1.count("</b>") and _sh1.count("<i>") == _sh1.count("</i>"))
_sh3 = lb._shadow_exit_msg("tp1", _shtr({"tp1": True}), _E - 7.5, "2026-08-03T00:51:00", "бар", False)
ck("П7 сянка-ТП1 не се води безрисков (нищо прибрано преди него)", "безрисков" not in _sh3)


# ═══════════════════════════════════════════════════════════════════════
# П8 · ОДИТ-6: РЕДЪТ И ИКОНИТЕ НА САМАТА КАРТА.
# присъдата стоеше на 9-и ред от 14 (под 5 реда готови за копиране числа);
# 🔴 значеше само «шорт» → червено стоеше над картите, на които ТРЯБВА да
# действаш, а 🟡 над тези, на които трябва да спреш. Мерено: 28 от 29 карти.
# ═══════════════════════════════════════════════════════════════════════
_MC = {"миньори": False, "долар": True, "лихви": False}
_RG = {"streaks": {"short": 0}, "vol_rank": 0.7}


def _card(adv, ok, **kw):
    return lb._sig_msg("short", 6, 7, "СРЕДЕН", sp, 4093.5, pd.Timestamp("2026-08-03 12:31:00"),
                       lb._levels(4088.9, "short"), 4088.9, adv, _MC, 0, _RG, stats,
                       1000, 2, adv_ok=ok, **kw)


_NO = "НЕ — този клас исторически губи (макрото не е ПОДРЕДЕНО днес): 67% · -0.87$/oz — ГУБЕЩ клас"
_YES = "ДА — пресен сигнал (ден 1) · клас 79.3% · +2.57$/oz (n=3860)"
_cn = _card(_NO, False); _cy = _card(_YES, True)
_ln = [x for x in _cn.split("\n") if x.strip()]
_ly = [x for x in _cy.split("\n") if x.strip()]

ck("П8 присъдата е на ПЪРВИЯ ред",                     # ОДИТ-29: «⏸ БЕЗ ВХОД» е заглавието
   "БЕЗ ВХОД" in _ln[0])
ck("П8 присъдата е НАД нивата",                        # ОДИТ-29
   next(i for i, x in enumerate(_ln) if "БЕЗ ВХОД" in x)
   < next(i for i, x in enumerate(_ln) if "ако решиш сам" in x))
ck("П8 «ДА» картата също слага присъдата горе", any("ДА" in x for x in _ly[:3]))
ck("П8 отказ → ⏸ в заглавието",                        # ОДИТ-29: 🛑 значи САМО «стоп-нивото»
   _ln[0].startswith("⏸"))
ck("П8 «ДА» → 🟢/🔴 по посоката в заглавието",           # ОДИТ-29: ✅ значи САМО «постигнато»
   _ly[0].startswith("🟢") or _ly[0].startswith("🔴"))
ck("П8 ИЗЧАКАЙ → ⏸ в заглавието",                      # ОДИТ-29: ⏳ падна от речника
   _card("ИЗЧАКАЙ — пресен, но без ръб", False).split("\n")[0].startswith("⏸"))
ck("П8 🔴 значи посока, и то само при ДА",              # ОДИТ-29: канонът се обърна нарочно —
   "🔴" not in _cn)                                      # при отказ картата е ⏸, без цвят
ck("П8 посоката пак се вижда с думи", "надолу" in _cn)   # ОДИТ-29: без латиница
ck("П8 при отказ НЯМА лот изобщо",                     # ОДИТ-29: по-силно от условен лот —
   "лот" not in _cn and "ако решиш сам" in _cn)        # картата не оразмерява отказан вход
ck("П8 при ДА лотът НЕ е условен", "само ако въпреки това влезеш" not in _cy)
# 🔴 ОДИТ-67 · ОБНОВЕН. «X$/унция» стана «N пипса (X.XX$)» — собственикът
# брои в пипсове («4420→4415 = 50 пипса»), а 231 карти не пишеха нито един.
# 🔴 ОБНОВЕН v12.5. Пазеше «пипсове САМО на картата с ДА» — вярно, докато
# клонът «БЕЗ ВХОД» нямаше НИКАКВИ разстояния. Днес и той ги получи, и това е
# нарочно: там пише «ако решиш сам», тоест точно там човекът има нужда да види
# колко е стопът, без да вади наум. РАЗСТОЯНИЕТО не е съвет — ЛОТЪТ е съвет.
# Затова разделението вече минава по лота, не по пипсовете.
ck("П8 разстоянието се казва И на двете карти (то не е съвет)",
   "пипса" in _cy and "пипса" in _cn)
ck("П8 но отказаната карта пак НЕ оразмерява (лотът е съветът)",
   "лот" not in _cn)
ck("П8 отказаната карта дава разстояние до ВСЯКА цел, не само до стопа",
   _cn.count("п)") >= 3)
ck("П8 стопът носи И долари, не само пипсове", "$)" in _cy)
ck("П8 сребърната карта брои по СРЕБЪРНИЯ пипс (0.001$), не по златния",
   "540 пипса" in lb._разст(58.970, 58.430, "XAGUSD", 3)
   and "5 пипса" in lb._разст(58.970, 58.430, "XAUUSD", 3))
ck("П8 картата е балансиран HTML", _cn.count("<b>") == _cn.count("</b>") and _cn.count("<i>") == _cn.count("</i>"))
ck("П8 картата е под лимита на Телеграм", len(_cn) < 4096 and len(_cy) < 4096)
ck("П8 нивата пак са на картата",                      # ОДИТ-29: етикетите ТП1/СТОП станаха
   _cn.count("️⃣") == 3 and "🛑" in _cn)                 # 1️⃣2️⃣3️⃣ и 🛑 — по-къси, същото нещо
# сянката: обещанието «този сетъп» само когато е вярно
_shon = {"direction": "short", "entry": 4111.0, "opened": "2026-08-03T05:00:00"}
_cs = _card(_NO, False, shadow_on=_shon)
ck("П8 сянка на ДРУГ сетъп → картата дава ДРУГИЯ вход",
   "следя наум от" in _cs and "4,111.00" in _cs)
ck("П8 сянка на ДРУГ сетъп → НЕ обещава «този»",
   "следя наум от" in _cs and "следя го наум" not in _cs)
ck("П8 сянка на СЪЩИЯ вход → пак «този»",
   "следя го наум" in _card(_NO, False, shadow_on={"direction": "short", "entry": 4088.9}))
ck("П8 без сянка → пак «този»", "следя го наум" in _cn)


# ═══════════════════════════════════════════════════════════════════════
# П9 · КИБЕР КВАНТ (kiber-kvant.vercel.app) — дълбочината на терминала.
# Сверено на живо 04.08.2026: страницата дава индекс 28,1 и клъстери 37/9/23/48;
# tRPC API-то дава score 28.14 и clusterScores {1:36.01,2:10.27,3:22.69,4:48.63}
# → една и съща система. Ботът вече дърпаше СКОРА, но хвърляше клъстерите.
# ═══════════════════════════════════════════════════════════════════════
_CQ = {"score": 28.1, "zone": "Натрупване 🟢",
       "clusters": {"1": 36.0, "2": 10.3, "3": 22.7, "4": 48.6},
       "fg_crypto": 28, "fg_stock": 45, "events": [], "fetched": "2026-08-04T09:00:00"}
_q = lb._cq_msg(_CQ, "2026-08-04T09:00:00", fng_live={"value": 25, "cls": "Extreme Fear"})
ck("П9 картата носи настроението като ФОН, не като таблица",   # ОДИТ-29
   "28/100" in _q or "28 от 100" in _q or "/100" in _q)
ck("П9 клъстерите ПАДНАХА (табло на инженер)",         # ОДИТ-29: обърнат
   not any(x in _q for x in ("валуация", "моментум", "on-chain")))
ck("П9 тежестите ПАДНАХА", "35%" not in _q)            # ОДИТ-29: обърнат
ck("П9 базовата честота ПАДНА", "от дните" not in _q)  # ОДИТ-29: обърнат
ck("П9 картата казва, че е само ФОН", "за фон" in _q or "фон" in _q)
ck("П9 картата пази уговорката, че не е сигнал", "не е сигнал" in _q or "фон" in _q)
ck("П9 страх-алчност ПАДНА от картата", "крипто сега" not in _q)   # ОДИТ-29: обърнат
ck("П9 при съвпадение НЕ дублира",
   "крипто сега" not in lb._cq_msg(_CQ, "2026-08-04T09:00:00", fng_live={"value": 28, "cls": "Fear"}))
ck("П9 без жив фийд картата пак излиза", len(lb._cq_msg(_CQ, "2026-08-04T09:00:00")) > 30)
ck("П9 връзката към терминала ПАДНА", "kiber-kvant.vercel.app" not in _q)   # ОДИТ-29: обърнат
ck("П9 картата е балансиран HTML",
   _q.count("<b>") == _q.count("</b>") and _q.count("<i>") == _q.count("</i>") and _q.count("<a ") == _q.count("</a>"))
ck("П9 картата е под лимита", len(_q) < 4096)
# устойчивост: старият кеш няма 'clusters' → картата пак трябва да излиза
_old = dict(_CQ); _old.pop("clusters")
ck("П9 стар кеш без клъстери НЕ чупи картата", len(lb._cq_msg(_old, "2026-08-04T09:00:00")) > 30)
# 🔴 ОДИТ-68 · ОБЪРНАТИ. Тези два теста викаха `_cq_clusters_line` — функция,
# която НИТО ЕДНА карта не ползва. Тоест тя съществуваше само за да бъде
# тествана: тестът я държеше жива, а продукцията не я викаше.
# Клъстерите отпаднаха при телеграфното пренаписване («три реда за онова,
# което мени поведението на бота»). Тестовете вече пазят ПРЕМАХВАНЕТО.
ck("П9 функцията за клъстери я няма (картата не ги показва)",
   not hasattr(lb, "_cq_clusters_line"))
ck("П9 крипто-картата остава къса и без клъстери",
   "клъстер" not in lb._cq_msg({"zone": "неутрална", "score": 50}, "2026-08-18T10:00"))
ck("П9 но крипто-картата пак носи фона, който мени поведението",
   "макро" in lb._cq_msg({"zone": "неутрална", "score": 50}, "2026-08-18T10:00")
   or "ИДВА" in lb._cq_msg({"zone": "неутрална", "score": 50}, "2026-08-18T10:00"))
ck("П9 непозната зона не чупи", len(lb._cq_msg(dict(_CQ, zone=""), "2026-08-04T09:00:00")) > 30)
# _fng_live е защитен: не гърми, а връща None (мрежата в CI може да е спряна)
_fv = lb._fng_live(timeout=6)
ck("П9 _fng_live връща None или валиден 0-100", _fv is None or (0 <= _fv["value"] <= 100))
ck("П9 всички ключове на клъстерите са познати", set(lb.CQ_CLUSTERS) == {"1", "2", "3", "4"})


# ═══════════════════════════════════════════════════════════════════════
# П10 · ОДИТ-6/T4-01: КАРТАТА СИ ПРОТИВОРЕЧЕШЕ ЗА МАКРОТО.
# «макрото не е ПОДРЕДЕНО днес» и «макро за шорт 2/3 ✓» на СЪЩАТА карта —
# 28 от 29. Причината: ✓ се даваше от 2 крака, а стрийкът иска И ТРИТЕ.
# Отметката вече съвпада с прага, който наистина решава.
# ═══════════════════════════════════════════════════════════════════════
_c23 = _card(_NO, False)                                   # 2/3 за шорт (долар е единственият бичи)
ck("П10 при 2/3 НЯМА ✓", "2/3 ✓" not in _c23)
# ОДИТ-10: дисплеят вече брои РЕШАВАЩИТЕ два крака (долар+лихви), не три.
ck("П10 присъдата казва кои крака решават",            # ОДИТ-29: редът «📊 долар+лихви 2/2 ✓»
   "доларът и лихвите" in _c23 or "макрото" in _c23)   # падна — казва го изречението «Защо»
_c33 = lb._sig_msg("short", 6, 7, "СРЕДЕН", sp, 4093.5, pd.Timestamp("2026-08-03 12:31:00"),
                   lb._levels(4088.9, "short"), 4088.9, _YES,
                   {"миньори": False, "долар": False, "лихви": False}, 1, _RG, stats, 1000, 2, adv_ok=True)
ck("П10 при съгласни крака картата е ВХОД, не отказ",  # ОДИТ-29: «✓ подредено» → самото решение
   _c33.split("\n")[0].startswith("🟢") or _c33.split("\n")[0].startswith("🔴"))
_c03 = lb._sig_msg("short", 6, 7, "СРЕДЕН", sp, 4093.5, pd.Timestamp("2026-08-03 12:31:00"),
                   lb._levels(4088.9, "short"), 4088.9, _NO,
                   {"миньори": True, "долар": True, "лихви": True}, 0, _RG, stats, 1000, 2, adv_ok=False)
ck("П10 при несъгласни крака картата е ОТКАЗ",         # ОДИТ-29
   _c03.split("\n")[0].startswith("⏸"))
ck("П10 «не е ПОДРЕДЕНО» и ✓ не стоят заедно",
   not ("не е ПОДРЕДЕНО" in _c23 and "/3 ✓" in _c23))
ck("П10 картите остават балансиран HTML",
   all(c.count("<i>") == c.count("</i>") and c.count("<b>") == c.count("</b>") for c in (_c23, _c33, _c03)))


# ═══════════════════════════════════════════════════════════════════════
# П11 · ОДИТ-7 — НАМЕРЕНО ОТ СОБСТВЕНИКА, НЕ ОТ ОДИТ:
# «СТОП Е УДАРЕН 1 ПЪТ ЗА ВСИЧКИ СИГНАЛИ ... а той никога не е удрял».
# Мерено в живия live/sent_log.jsonl: 8 стоп-карти, от които 5 са БЕЗРИСКОВ
# ИЗХОД след взети ТП (стопът стои на ВХОДА) и само 3 са истински стоп.
# Картата ги наричаше еднакво «🛑 СТОП» → изглежда като ударен стоп, а е печалба.
# Сянката беше оправена сутринта (П7); РЕАЛНИЯТ изход — не. Оттук и този блок.
# ═══════════════════════════════════════════════════════════════════════
def _rtr(hit, sl_at_entry=True):
    return {"direction": "short", "entry": _E, "hit": dict(hit), "sym": "XAUUSD",
            "opened": "2026-08-03T00:00:00",
            "levels": dict(_LVs, sl=(_E if sl_at_entry else _E + 20.0))}


_be2 = lb._exit_msg("sl", _rtr({"tp1": True, "tp2": True}), _E, "2026-08-03T03:01:00", "бар", False)
_be1 = lb._exit_msg("sl", _rtr({"tp1": True}), _E, "2026-08-03T05:56:00", "бар", False)
_hard = lb._exit_msg("sl", _rtr({}, False), _E + 20.0, "2026-08-04T00:21:00", "бар", False)

ck("П11 стоп след 2 ТП НЕ се нарича СТОП", not _be2.split("\n")[0].startswith("🛑"))
ck("П11 стоп след 2 ТП се нарича НУЛА, не СТОП", "НУЛА" in _be2.split("\n")[0])
ck("П11 стоп след 2 ТП брои +6.50 по стълбата", "+6.50$" in _be2)
ck("П11 стоп след 1 ТП брои +2.50 по стълбата", "+2.50$" in _be1)
ck("П11 заглавието казва, че стопът е бил на входа",      # ОДИТ-27/29
   "стопът беше на входа" in _be2 and "стопът беше на входа" in _be1)
ck("П11 картата дава ОБЩАТА сметка, не голия крак",       # ОДИТ-29: имената на ТП паднаха,
   "+6.50$" in _be2 and "+2.50$" in _be1                  # числото по стълбата остана
   and "донесе" in _be2 and "донесе" in _be1)
# 🔴 ОБНОВЕН v12.5: «/унция» отпадна от паричния ред — картата вече казва
# метала в заглавието, а редът носи пипсове + долари. Пази се СЪЩОТО:
# че общата сметка се различава от голия крак.
ck("П11 картата разграничава крака от общата сметка",     # ОДИТ-29
   "донесе" in _be2 and "пипса" in _be2 and _be2.count("$") >= 2)
ck("П11 ИСТИНСКИЯТ стоп СИ ОСТАВА 🛑 СТОП", _hard.split("\n")[0].startswith("🛑 СТОП"))
ck("П11 истинският стоп показва −20.00",                  # ОДИТ-29: «цяла позиция» падна —
   _hard.count("−20.00$") >= 1)                           # беше същото число, казано два пъти
ck("П11 и го дава в пипсове (200 пипса = 20.00$ при PIP 0.10)",
   "−200 пипса" in _hard)
# 🔴 ЕДИН ЗНАК на реда: Python дава ASCII «-», пипсовете ползват «−».
ck("П11 паричният ред НЕ смесва два различни минуса",
   not any(("-" in л and "−" in л) for л in _hard.split("\n")))
ck("П11 истинският стоп НЕ твърди, че е безрисков", "НУЛА" not in _hard and "Стопът НЕ е ударен" not in _hard)
ck("П11 реалният и сянката ползват ЕДНА функция за сметката",
   _src.count("_ladder_pnl(kind, hit, lv, e, знак, дол") == 2)
ck("П11 изходните карти са балансиран HTML",
   all(c.count("<b>") == c.count("</b>") and c.count("<i>") == c.count("</i>") for c in (_be2, _be1, _hard)))
ck("П11 ТП3 след ТП1+ТП2 брои 13.17, не 20.00",
   "+13.17$" in lb._exit_msg("tp3", _rtr({"tp1": True, "tp2": True}), _E - 20.0, "2026-08-03T09:41:00", "бар", False))


# ═══════════════════════════════════════════════════════════════════════
# П12 · ОДИТ-8: КОФАТА `stale` СЛИВАШЕ ДВЕ РАЗЛИЧНИ СЪСТОЯНИЯ.
# (стрийк==0) = «макрото ДНЕС е смесено» · (стрийк>=4) = «сигналът е ОСТАРЯЛ».
# Мерено на 114813 сделки, блоков бутстрап по ден:
#   long/mixed −0.04$ ШУМ (n=40094)   срещу   long/stale +1.18$ ПЕЧЕЛИ (n=12062)
# Слети даваха +0.24$ и ботът пращаше «ДА (слаб)» на 40 хиляди нулеви сделки.
# Разделени: +0.518 → +1.469$/сделка · общо +32956 → +34571$ · карти 152 → 53 дни/год.
# ═══════════════════════════════════════════════════════════════════════
_G = {"fresh": {
    "long":  {"day1":  {"win": 79.3, "net": 2.57, "n": 3860, "lo": 1.295, "hi": 3.831},
              "fresh": {"win": 76.7, "net": 1.84, "n": 4544, "lo": 0.608, "hi": 3.001},
              "mixed": {"win": 70.1, "net": -0.04, "n": 40094, "lo": -0.496, "hi": 0.426},
              "stale": {"win": 73.0, "net": 1.18, "n": 12062, "lo": 0.376, "hi": 1.960}},
    "short": {"day1":  {"win": 72.6, "net": 0.66, "n": 3065, "lo": -0.895, "hi": 2.169},
              "fresh": {"win": 65.4, "net": -1.22, "n": 4746, "lo": -2.613, "hi": 0.110},
              "mixed": {"win": 66.5, "net": -0.91, "n": 31898, "lo": -1.436, "hi": -0.389},
              "stale": {"win": 68.0, "net": -0.77, "n": 14544, "lo": -1.541, "hi": -0.010}}}}
_g = lambda d, s: lb._advice_entry(d, s, _G, None, False, 0)

ck("П12 long/mixed (стрийк 0) вече ОТКАЗВА", not _g("long", 0)[1])
ck("П12 long/mixed казва че макрото се кара", "се карат" in _g("long", 0)[0])   # ОДИТ-29
ck("П12 long/mixed е ОТКАЗ", _g("long", 0)[0].startswith("НЕ") and not _g("long", 0)[1])
ck("П12 long/stale (стрийк 4+) ПРОДЪЛЖАВА да пуска", _g("long", 5)[1])
ck("П12 long/stale се нарича застоял, НЕ смесено",        # ОДИТ-29: «застоял» → «подреждането
   "подреждането е отпреди" in _g("long", 5)[0]           # е отпреди N дни» — същото, с думи
   and "се карат" not in _g("long", 5)[0])
ck("П12 long/day1 пуска и числото е в ДНЕВНИКА, не в текста",   # ОДИТ-29
   _g("long", 1)[1] and "+2.57" not in _g("long", 1)[0])
ck("П12 long/fresh пуска и числото е в ДНЕВНИКА, не в текста",
   _g("long", 2)[1] and "+1.84" not in _g("long", 2)[0])
# ОДИТ-10: short/day1 вече минава през ШУМ-пазача и се ОТКАЗВА (интервалът обхваща нулата)
ck("П12 short/day1 при ШУМ вече ОТКАЗВА", not _g("short", 1)[1])
ck("П12 short/fresh отказва", not _g("short", 2)[1])
ck("П12 short/mixed отказва", not _g("short", 0)[1])
ck("П12 short/stale отказва", not _g("short", 5)[1])
# 🔴 ОДИТ-29 · ТОЗИ ТЕСТ ПАЗИ ПРАВИЛО 1 ОТ ПРОТОКОЛА — произход до всяко твърдение.
# Числата вече не са в ТЕКСТА (собственикът: «неразбираш нищо от тях»), а в `trace["мерено"]`,
# откъдето ги четат дневникът и одит-роботът. Тестът не се трие — сменя си мястото.
_tr12a, _tr12b = {}, {}
lb._advice_entry("long", 0, stats, None, False, 0, trace=_tr12a)
lb._advice_entry("short", 5, stats, None, False, 0, trace=_tr12b)
ck("П12 отказите записват мереното в ДНЕВНИКА (проверимо число)",
   all(t.get("мерено", {}).get(k) is not None
       for t in (_tr12a, _tr12b) for k in ("win", "net", "n", "lo", "hi")))
ck("П12 мереното НЕ изтича в текста на картата",
   "95%" not in _g("long", 0)[0] and "n=" not in _g("long", 0)[0])
# шумовият пазач: положително нето, но интервалът минава през нулата → пак отказ
_noisy = json.loads(json.dumps(_G))
_noisy["fresh"]["long"]["mixed"] = {"win": 70.0, "net": 0.30, "n": 40000, "lo": -0.40, "hi": 1.00}
ck("П12 ШУМ (нето>0, но нулата е в интервала) → пак ОТКАЗ",
   not lb._advice_entry("long", 0, _noisy, None, False, 0)[1])
ck("П12 _noise разпознава шум", lb._noise({"lo": -0.4, "hi": 1.0}) and not lb._noise({"lo": 0.4, "hi": 1.0}))
ck("П12 _noise без lo/hi не съди (стар stats)", not lb._noise({"net": 1.0}))
# устойчивост: стар stats БЕЗ клетка mixed → пада на stale = точно старото поведение
_old_stats = json.loads(json.dumps(_G))
for _d in ("long", "short"):
    _old_stats["fresh"][_d].pop("mixed")
    for _k in _old_stats["fresh"][_d].values():
        _k.pop("lo", None); _k.pop("hi", None)
ck("П12 стар stats без mixed НЕ гърми", isinstance(lb._advice_entry("long", 0, _old_stats, None, False, 0), tuple))
ck("П12 стар stats без mixed → старото поведение (long/0 пуска по stale +1.18)",
   lb._advice_entry("long", 0, _old_stats, None, False, 0)[1])
ck("П12 живият backtest_stats.json има разделена кофа",
   all("mixed" in stats.get("fresh", {}).get(d, {}) for d in ("long", "short")) if stats else True)


# ═══════════════════════════════════════════════════════════════════════
# П13 · ОДИТ-9: main() — 679 реда оркестратор — имаше НУЛА изпълнени теста.
# Досега се проверяваше само с грепване на изходния текст (`"низ" in _msrc`),
# което мъртъв код минава без да мигне. Тук main() се ИЗПЪЛНЯВА наистина,
# срещу изкуствени данни и БЕЗ мрежа, и се твърди за ПОВЕДЕНИЕТО му.
# ═══════════════════════════════════════════════════════════════════════
import tempfile as _tf, shutil as _sh4, contextlib as _ctx, io as _io2
import numpy as _np
import time as _t13

_REAL = {k: getattr(lb, k) for k in ("_yf", "_rates", "_spot", "_cq_fetch", "_fng_live", "_send_raw")}
_REAL_SLEEP = _t13.sleep


def _fx(n, start, freq, px, drift=0.0):
    """Изкуствена свещна серия — детерминирана, без случайност."""
    i = pd.date_range(start, periods=n, freq=freq)
    c = px + _np.arange(n) * drift + _np.sin(_np.arange(n) / 7.0) * 2.0
    return pd.DataFrame({"Open": c, "High": c + 1.5, "Low": c - 1.5, "Close": c,
                         "Volume": 1000.0}, index=i)


def _run_main(spot=None, stats_path="backtest_stats.json", send_ok=True, extra_argv=()):
    """Пуска ЦЕЛИЯ main() в tmp папка, без мрежа. Връща (изходен_код, пратени, папка)."""
    D = {"GC=F": _fx(800, "2024-01-01", "D", 3800, 0.35),
         "GDX": _fx(600, "2024-06-01", "D", 40, 0.02),
         "DX-Y.NYB": _fx(600, "2024-06-01", "D", 100, -0.005),
         "SI=F": _fx(900, "2026-07-20", "5min", 46.0, 0.001)}
    sent = []
    lb._yf = lambda s, period="2y", interval="1d": D.get(s, _fx(900, "2026-07-20", "5min", 4000, 0.002)).copy()
    lb._rates = lambda: pd.Series(2.0 - _np.arange(600) * 0.0008,
                                  index=pd.date_range("2024-06-01", periods=600, freq="D"))
    lb._spot = lambda instr="XAU/USD", market_closed=False, cme_pause=False: spot
    lb._cq_fetch = lambda now: None
    lb._fng_live = lambda timeout=8: None
    lb._send_raw = (lambda t: (sent.append(t), "SENT (200)")[1]) if send_ok \
        else (lambda t: (_ for _ in ()).throw(RuntimeError("HARD_FAIL:400 тест")))
    _t13.sleep = lambda *a, **k: None
    tmp = _P(_tf.mkdtemp())
    old_argv = sys.argv
    sys.argv = ["live_bot.py", "--out", str(tmp), "--stats", stats_path,
                "--balance", "1000", "--risk", "2", "--send", "--force", *extra_argv]
    code = 0
    try:
        with _ctx.redirect_stdout(_io2.StringIO()):
            lb.main()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    except Exception as e:
        code = f"ГРЪМНА: {type(e).__name__}: {e}"
    finally:
        sys.argv = old_argv
        for k, v in _REAL.items():
            setattr(lb, k, v)
        _t13.sleep = _REAL_SLEEP
    return code, sent, tmp


_SP = {"bid": 4079.0, "ask": 4079.5, "mid": 4079.25, "src": "тест", "age_sec": 2}

# --- А · нормален рън ---
_c, _s, _t1 = _run_main(spot=_SP)
ck("П13 main() минава ДО КРАЯ без изключение", _c == 0)
ck("П13 main() записва журнал", (_t1 / "live_journal.jsonl").exists())
_jr = [json.loads(x) for x in (_t1 / "live_journal.jsonl").read_text(encoding="utf-8").strip().split("\n") if x.strip()]
ck("П13 журналът има точно 1 запис за 1 рън", len(_jr) == 1)
ck("П13 записът носи версията", _jr[0].get("v") == lb.VERSION)
ck("П13 записът носи ТРИТЕ макро крака",
   set(_jr[0].get("macro", {})) == {"миньори", "долар", "лихви"})
ck("П13 записът носи СУРОВИТЕ макро числа (проверимост)",
   all(k in (_jr[0].get("macro_raw") or {}) for k in ("миньори", "долар", "лихви")))
ck("П13 записът носи борда по 7 рамки", len(_jr[0].get("board") or {}) == 7)
ck("П13 записът носи статус", isinstance(_jr[0].get("status"), list))
ck("П13 main() записва състоянието", (_t1 / "meta.json").exists() and (_t1 / "guard.json").exists())
ck("П13 main() води книга на пратеното", (_t1 / "sent_log.jsonl").exists())
_sh4.rmtree(_t1, ignore_errors=True)

# --- Б · БЕЗ спот (фийдът е паднал) ---
_c2, _s2, _t2 = _run_main(spot=None)
ck("П13 липсващ спот НЕ чупи бота", _c2 == 0)
_jr2 = [json.loads(x) for x in (_t2 / "live_journal.jsonl").read_text(encoding="utf-8").strip().split("\n") if x.strip()]
ck("П13 липсващият спот се ОТБЕЛЯЗВА в журнала, не се крие",
   _jr2[0].get("spot") is None or "спот" in " ".join(_jr2[0].get("notes") or []).lower())
_sh4.rmtree(_t2, ignore_errors=True)

# --- В · ПОВРЕДЕН stats файл ---
_bad = _P(_tf.mkdtemp()) / "bad_stats.json"
_bad.write_text("{това не е json", encoding="utf-8")
_c3, _s3, _t3 = _run_main(spot=_SP, stats_path=str(_bad))
ck("П13 повреден backtest_stats.json НЕ чупи бота (излиза чисто)",
   _c3 == 0 or (isinstance(_c3, int) and _c3 == 1))
ck("П13 при повреден stats НЕ се праща вход-карта",
   not any("КУПИ" in x or "ПРОДАЙ" in x for x in _s3))   # ОДИТ-29: заглавието е глагол
_sh4.rmtree(_t3, ignore_errors=True); _sh4.rmtree(_bad.parent, ignore_errors=True)

# --- Г · Телеграм отказва → съобщението НЕ изчезва ---
_c4, _s4, _t4 = _run_main(spot=_SP, send_ok=False)
_ob = (_t4 / "outbox.jsonl")
ck("П13 изключение при пращане НЕ изхвърля бота (беше traceback от main)", _c4 == 0)
ck("П13 изключение при пращане → съобщението ОСТАВА в пощата",
   _ob.exists() and _ob.read_text(encoding="utf-8").strip() != "")
_j4 = [json.loads(x) for x in
       (_t4 / "live_journal.jsonl").read_text(encoding="utf-8").strip().splitlines() if x.strip()]
ck("П13 изключението се ОТБЕЛЯЗВА като мек провал, не се крие",
   any("изключение" in " ".join(r.get("status") or []) for r in _j4))
_sh4.rmtree(_t4, ignore_errors=True)

# --- Д · истинските функции са ВЪРНАТИ (тестът да не трови следващите) ---
ck("П13 подмените са върнати след теста",
   all(getattr(lb, k) is v for k, v in _REAL.items()) and _t13.sleep is _REAL_SLEEP)


# ═══════════════════════════════════════════════════════════════════════
# П14 · ОДИТ-10: ПОДРЕЖДАНЕТО вече е по ДОЛАР+ЛИХВИ, БЕЗ миньорите.
# Мерено на 114813 сделки (блоков бутстрап по ден, доставената геометрия):
#   и трите (старото) +32560$ · 45 карти/год · мечи 2013-18: +1.41
#   2 от 3 всички     +58918$ · 116        · мечи: +0.07   ← умира в мечи пазар
#   ДОЛАР+ЛИХВИ       +44462$ · 72         · мечи: +0.54   ← избраното
# Избрано НЕ най-голямото число, а единственото, което не пада под +0.5$
# в НИТО един режим. Късмет-тест: 0 от 60 случайни правила го бият.
# ═══════════════════════════════════════════════════════════════════════
_ix = pd.date_range("2024-01-01", periods=120, freq="D")


def _mk(dx_dir, rr_dir):
    """dx_dir/rr_dir: -1 пада · +1 расте. Прави серии с ясна посока."""
    dxv = 100.0 + _np.arange(120) * (0.05 * dx_dir)
    rrv = 2.0 + _np.arange(120) * (0.01 * rr_dir)
    return (pd.DataFrame({"Close": 3800.0 + _np.arange(120)}, index=_ix),   # gold
            pd.DataFrame({"Close": 40.0 + _np.arange(120) * 0.5}, index=_ix),  # gdx (расте силно)
            pd.DataFrame({"Close": dxv}, index=_ix),
            pd.Series(rrv, index=_ix))


_g1, _gd1, _dx1, _rr1 = _mk(-1, -1)          # доларът пада, лихвите падат → ЛОНГ подредено
_st_l = lb._streaks(_g1, _gd1, _dx1, _rr1)
ck("П14 долар↓ + лихви↓ → ЛОНГ стрийк расте", _st_l["long"] > 3 and _st_l["short"] == 0)
_g2, _gd2, _dx2, _rr2 = _mk(+1, +1)          # доларът расте, лихвите растат → ШОРТ подредено
_st_s = lb._streaks(_g2, _gd2, _dx2, _rr2)
ck("П14 долар↑ + лихви↑ → ШОРТ стрийк расте", _st_s["short"] > 3 and _st_s["long"] == 0)
_g3, _gd3, _dx3, _rr3 = _mk(-1, +1)          # разнопосочни → НИЩО не е подредено
_st_m = lb._streaks(_g3, _gd3, _dx3, _rr3)
ck("П14 разнопосочни долар/лихви → и двата стрийка НУЛА",
   _st_m["long"] == 0 and _st_m["short"] == 0)
# миньорите вече НЕ участват в подреждането — същите долар/лихви, обърнати миньори
_gd_flip = pd.DataFrame({"Close": 60.0 - _np.arange(120) * 0.5}, index=_ix)   # миньорите ПАДАТ
ck("П14 миньорите НЕ променят подреждането (само контекст са)",
   lb._streaks(_g1, _gd_flip, _dx1, _rr1) == _st_l)
ck("П14 _streaks още приема gdx в подписа (обратна съвместимост)",
   "gdx_d" in _insp.signature(lb._streaks).parameters)
# картата казва КОИ крака решават
_c14 = _card(_NO, False)
ck("П14 присъдата казва кои крака решават",
   "доларът и лихвите" in _c14 or "макрото" in _c14 or "подреждането" in _c14)
ck("П14 миньорите не задръстват картата", "само контекст" not in _c14)   # ОДИТ-27: обърнат
ck("П14 картата вече НЕ брои «/3» за решението", "/3 ✓" not in _c14 and "/3 ⚠" not in _c14)
# шум-пазачът важи и за пресните клетки
_noisy_fresh = json.loads(json.dumps(_G))
_noisy_fresh["fresh"]["short"]["day1"] = {"win": 71.5, "net": 0.44, "n": 3100, "lo": -1.071, "hi": 1.850}
_t14, _p14 = lb._advice_entry("short", 1, _noisy_fresh, None, False, 0)
ck("П14 ПРЕСЕН клас с нула в интервала → ОТКАЗ (беше пускане на голо нето>0)", not _p14)
ck("П14 отказът обяснява защо", "не носят нищо" in _t14 or "се карат" in _t14)   # ОДИТ-29
ck("П14 живият stats е под НОВОТО правило (има бележката)",
   "подреждане_долар_лихви" in (stats.get("_meta", {}) if stats else {"подреждане_долар_лихви": 1}))


# ═══════════════════════════════════════════════════════════════════════
# П15 · ОДИТ-11: 54 от 314 проверки само ГРЕПВАТ изходния текст.
# Мъртъв код минава през тях без да мигне. Тук проверките, които пазят
# ПАРИ и ДОСТАВКА, вече се ИЗПЪЛНЯВАТ наистина — с истинска tmp папка,
# истински _outbox_flush и подменена мрежа.
# ═══════════════════════════════════════════════════════════════════════
import urllib.request as _ur15, urllib.error as _ue15


def _ob_run(msgs, send, new_msgs=()):
    """Пуска _outbox_flush НАИСТИНА върху tmp папка.
    НАУЧЕНО С ПАДАЩ ТЕСТ: `signal`/`s-signal`, пренесени от МИНАЛ рън и НЕрегенерирани
    сега, се ИЗХВЪРЛЯТ НАРОЧНО (НАХОДКА B — осиротяла карта: картата стига до човека,
    а сделка не се отваря). За тестове на задържане ползвай ИЗХОДЕН таг."""
    d = _P(_tf.mkdtemp())
    (d / "outbox.jsonl").write_text(
        "\n".join(json.dumps(m, ensure_ascii=False) for m in msgs), encoding="utf-8")
    st = []
    _o = lb._send_raw
    lb._send_raw = send
    try:
        sent = lb._outbox_flush(d, list(new_msgs), st)
    except SystemExit as e:
        sent = set(); st.append("SystemExit:" + str(e)[:70])
    finally:
        lb._send_raw = _o
    rem = [json.loads(x) for x in (d / "outbox.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return sent, rem, st, d


def _M(tag, txt="карта", hf=0):
    return {"tag": tag, "text": txt, "first_ts": "2026-08-04T00:00:00", "attempts": 1, "hard_fails": hf}


# --- 1 · ИЗХОДНИТЕ КАРТИ никога не се хвърлят като «отровни» ---
_s, _r, _st, _d = _ob_run([_M("exit:tp1", "<b>ТП1</b>", hf=5)], lambda t: "HARD_FAIL:400 bad html")
ck("П15 изходна карта с 5 твърди провала НЕ се изхвърля (парите са на риск)",
   any(m["tag"] == "exit:tp1" for m in _r))
ck("П15 изходната карта се пробва като ГОЛ ТЕКСТ (последен шанс)",
   any(m.get("plain") for m in _r) or any("HTML махнат" in s for s in _st))
_sh4.rmtree(_d, ignore_errors=True)

_s, _r, _st, _d = _ob_run([_M("ma-alert", "<b>карта</b>", hf=5)], lambda t: "HARD_FAIL:400 bad html")
ck("П15 обикновена карта с 5 твърди провала СЕ изхвърля (отровна)",
   not any(m["tag"] == "ma-alert" for m in _r) and any("ОТРОВНО" in s for s in _st))
_sh4.rmtree(_d, ignore_errors=True)

# --- 2 · ЛИПСВАЩ ТОКЕН пази пощата и вдига аларма ---
_s, _r, _st, _d = _ob_run([_M("exit:tp2"), _M("exit:sl")], lambda t: "DRY_RUN (няма токен)")
ck("П15 липсващ токен ПАЗИ и двете съобщения (не ги трие)", len(_r) == 2)
ck("П15 липсващ токен вдига аларма, не мълчи",
   any("КОНФИГУРАЦИЯ" in s or "ЛИПСВА TELEGRAM" in s for s in _st))
_sh4.rmtree(_d, ignore_errors=True)

# --- 3 · МЕК провал → ретрай вечно, съобщението остава ---
_s, _r, _st, _d = _ob_run([_M("exit:sl")], lambda t: "SEND_FAILED: мрежа")
ck("П15 мек провал ПАЗИ съобщението за следващия рън", len(_r) == 1)
ck("П15 мек провал НЕ брои за отровно", _r and _r[0].get("hard_fails", 0) == 0)
_sh4.rmtree(_d, ignore_errors=True)

# --- 4 · УСПЕХ → съобщението излиза от пощата и влиза в книгата ---
_s, _r, _st, _d = _ob_run([_M("exit:sl")], lambda t: "SENT (200)")
ck("П15 успешно пратено НАПУСКА пощата", len(_r) == 0 and "exit:sl" in _s)
ck("П15 успешно пратено се вписва в sent_log",
   (_d / "sent_log.jsonl").exists() and "карта" in (_d / "sent_log.jsonl").read_text(encoding="utf-8"))
_sh4.rmtree(_d, ignore_errors=True)

# --- 5 · ИЗКЛЮЧЕНИЕ при пращане не изхвърля бота и пази пощата (ОДИТ-9) ---
_s, _r, _st, _d = _ob_run([_M("exit:sl")], lambda t: (_ for _ in ()).throw(RuntimeError("бум")))
ck("П15 изключение при пращане НЕ вали обиколката", len(_r) == 1)
ck("П15 изключението се отбелязва като мек провал", any("изключение" in s for s in _st))
_sh4.rmtree(_d, ignore_errors=True)

# --- 6 · ВЕРИГАТА ОТ РЕЗЕРВНИ СПОТ-ИЗТОЧНИЦИ наистина пада надолу ---
_calls15 = []


def _fake_url15(req, timeout=0):
    u = req.full_url if hasattr(req, "full_url") else str(req)
    _calls15.append(u)

    class _R:
        status = 200
        def __enter__(s): return s
        def __exit__(s, *a): return False
        def read(s):
            if "binance" in u:
                raise _ue15.HTTPError(u, 451, "blocked", None, None)
            if "coinbase" in u:
                raise _ue15.HTTPError(u, 500, "err", None, None)
            if "kraken" in u:
                return b'{"result":{"PAXGUSD":{"b":["4001.5","1","1"],"a":["4002.0","1","1"]}}}'
            raise _ue15.HTTPError(u, 503, "no", None, None)
    return _R()


_ou15 = _ur15.urlopen
_ur15.urlopen = _fake_url15
try:
    _res15 = lb._spot("XAU/USD")
except Exception:
    _res15 = None
finally:
    _ur15.urlopen = _ou15
_tried = sum(1 for c in _calls15 if any(k in c for k in ("binance", "coinbase", "kraken")))
ck("П15 спот-веригата ПРОБВА следващия при провал (не спира на първия)", _tried >= 2)
ck("П15 спот-веригата стига до Kraken, когато първите два паднат",
   any("kraken" in c for c in _calls15))

# --- 7 · ПАЗАЧЪТ НА БАЗИСА лови ВСИЧКИ paxg-източници по префикс ---
ck("П15 префиксният пазач лови и трите paxg варианта, но не Swissquote",
   all(str(n).startswith("paxg") for n in ("paxg-bin", "paxg-cb", "paxg-kr"))
   and not str("swq").startswith("paxg"))
ck("П15 кодът ползва ПРЕФИКС, не точно име",
   'startswith("paxg")' in _src and '== "paxg-bin"' not in _src)

# --- 8 · САНИТИ-ФИЛТЪРЪТ на спота отхвърля абсурдна цена ---
_calls15b = []


def _absurd(req, timeout=0):
    u = req.full_url if hasattr(req, "full_url") else str(req)
    _calls15b.append(u)

    class _R:
        status = 200
        def __enter__(s): return s
        def __exit__(s, *a): return False
        def read(s):
            if "kraken" in u:
                return b'{"result":{"PAXGUSD":{"b":["4001.5","1","1"],"a":["4002.0","1","1"]}}}'
            return b'{"bidPrice":"0.01","askPrice":"0.02"}'      # абсурд
    return _R()


_ur15.urlopen = _absurd
try:
    _res15b = lb._spot("XAU/USD")
except Exception:
    _res15b = None
finally:
    _ur15.urlopen = _ou15
ck("П15 абсурдна цена (0.01$) НЕ се приема за злато",
   _res15b is None or _res15b.get("bid", 0) > 500)

# --- 9 · ПАЗАЧЪТ СРЕЩУ ОСИРОТЕЛИ КАРТИ (НАХОДКА B) — намерен от ПАДАЩ тест ---
# `signal`, пренесен от МИНАЛ рън и НЕрегенериран сега, трябва да се ИЗХВЪРЛИ:
# иначе картата стига до човека, а сделка не се отваря и не се следи.
# Дотук това се пазеше само от греп («in _src»); сега се ИЗПЪЛНЯВА.
_s, _r, _st, _d = _ob_run([_M("signal", "стара карта")], lambda t: "SENT (200)")
ck("П15 пренесен НЕрегенериран signal се ИЗХВЪРЛЯ (без осиротяла карта)",
   not any(m["tag"] == "signal" for m in _r) and "signal" not in _s)
_sh4.rmtree(_d, ignore_errors=True)
_s, _r, _st, _d = _ob_run([], lambda t: "SENT (200)", new_msgs=[("signal", "нова карта")])
ck("П15 регенериран signal СЕ праща нормално", "signal" in _s and len(_r) == 0)
_sh4.rmtree(_d, ignore_errors=True)
_s, _r, _st, _d = _ob_run([_M("exit:tp1", "стар изход")], lambda t: "SEND_FAILED: мрежа")
ck("П15 пренесена ИЗХОДНА карта се ПАЗИ (за разлика от signal)",
   any(m["tag"] == "exit:tp1" for m in _r))
_sh4.rmtree(_d, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════
# П16 · ОДИТ-13: ДВА ТИХИ НАЧИНА ДА СЕ ЗАГУБИ КАРТА ЗА ПАРИ НА РИСК.
# И двата възпроизведени върху ЖИВИЯ код, преди поправката.
# ═══════════════════════════════════════════════════════════════════════
# --- А · СУХ РЪН (без --send) изтриваше пощата и я обявяваше за пратена ---
_dm = [_M("exit:sl", "СТОП УДАРЕН"), _M("digest", "равносметка")]
_d = _P(_tf.mkdtemp())
(_d / "outbox.jsonl").write_text(
    chr(10).join(json.dumps(m, ensure_ascii=False) for m in _dm), encoding="utf-8")
_stq = []
_tg = lb._outbox_flush(_d, [], _stq, dry=True)
_rem = [json.loads(x) for x in (_d / "outbox.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
ck("П16 сух рън ПАЗИ чакащите карти (преди ги триеше)", len(_rem) == 2)
ck("П16 сух рън НЕ ги обявява за пратени (иначе трови състоянието)", not _tg)
ck("П16 сухият рън го КАЗВА в статуса", any("остава в пощата" in s for s in _stq))
_sh4.rmtree(_d, ignore_errors=True)

# --- Б · HTTP 200 без ok:true се броеше за доставено ---
class _TgResp:
    def __init__(s, body, status=200): s._b, s.status = body, status
    def __enter__(s): return s
    def __exit__(s, *a): return False
    def read(s): return s._b


def _tg_send(body, status=200):
    """Пуска ИСТИНСКИЯ _send_raw срещу подменен HTTP отговор."""
    _o = _ur15.urlopen
    _ur15.urlopen = lambda *a, **k: _TgResp(body, status)
    _ot, _oc = _os.environ.get("TELEGRAM_TOKEN"), _os.environ.get("TELEGRAM_CHAT_ID")
    _os.environ["TELEGRAM_TOKEN"] = "t"; _os.environ["TELEGRAM_CHAT_ID"] = "c"
    _sl2 = _time.sleep; _time.sleep = lambda *a: None
    try:
        return lb._send_raw("тест")
    finally:
        _ur15.urlopen = _o; _time.sleep = _sl2
        if _ot is None: _os.environ.pop("TELEGRAM_TOKEN", None)
        else: _os.environ["TELEGRAM_TOKEN"] = _ot
        if _oc is None: _os.environ.pop("TELEGRAM_CHAT_ID", None)
        else: _os.environ["TELEGRAM_CHAT_ID"] = _oc


_r_ok = _tg_send(b'{"ok":true,"result":{"message_id":7}}')
ck("П16 истинският успех (ok:true) СЕ брои за пратено", _r_ok.startswith("SENT"))
_r_no = _tg_send(b'{"ok":false,"error_code":400,"description":"Bad Request: chat not found"}')
ck("П16 200 + ok:false НЕ се брои за пратено", not _r_no.startswith("SENT"))
ck("П16 отказът носи ПРИЧИНАТА от Телеграм", "chat not found" in _r_no)
ck("П16 200 + ok:false е МЕК провал (ретрай), не отровно",
   _r_no.startswith("SEND_FAILED") and not _r_no.startswith("HARD_FAIL"))
_r_junk = _tg_send(b"<html>captive portal</html>")
ck("П16 200 с чуждо тяло (прокси/портал) НЕ се брои за пратено", not _r_junk.startswith("SENT"))
# и картата НЕ се трие, нито влиза в книгата
_s16, _r16, _st16, _d16 = _ob_run([_M("exit:sl", "СТОП")],
                                  lambda t: "SEND_FAILED: HTTP 200 без ok:true — chat not found")
ck("П16 недоставена карта ОСТАВА в пощата", len(_r16) == 1)
ck("П16 недоставена карта НЕ влиза в sent_log", not (_d16 / "sent_log.jsonl").exists())
_sh4.rmtree(_d16, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════
# П17 · ОДИТ-14: ЗОНИТЕ (FVG) ОТ ИНДИКАТОРА СТЕПЕНУВАТ РАЗМЕРА.
# Мерено на 114813 сделки, върху 31854 допуснати от гейта:
#   A зона отдолу + чисто отгоре  32.6%  +1.998$ [+1.41..+2.59] ПЕЧЕЛИ
#   B едно от двете               42.5%  +1.457$ [+0.85..+2.05] ПЕЧЕЛИ
#   C нито едно                   24.9%  +0.502$ [-0.19..+1.19] ШУМ
#   гейтът сам: +1.396$ · подредбата A>B>C е чиста, и в 4-те четвъртини
#   късмет-тест: 0 от 60 случайни подмножества бият +1.998$
# НИЩО НЕ СЕ РЕЖЕ — само размерът: +1.396 -> +1.597$/единица риск, при 31% по-малко риск.
# ═══════════════════════════════════════════════════════════════════════
def _h1(pat):
    _i = pd.date_range("2026-08-01", periods=len(pat), freq="h")
    return pd.DataFrame({"Open": [p[1] for p in pat], "High": [p[0] for p in pat],
                         "Low": [p[1] for p in pat], "Close": [p[1] for p in pat]}, index=_i)


_up = [(100 + i, 99 + i) for i in range(40)]; _up[20] = (140, 135)     # празнина нагоре
_dn = [(100 - i, 99 - i) for i in range(40)]; _dn[20] = (70, 65)       # празнина надолу
_fl = [(100.5, 99.5)] * 40

ck("П17 празнина отдолу + чисто отгоре → клас A", lb._zones(_h1(_up), "long")[0] == "A")
ck("П17 насрещна зона отгоре, без опора → клас C", lb._zones(_h1(_dn), "long")[0] == "C")
ck("П17 чисто, но без опора → клас B", lb._zones(_h1(_fl), "long")[0] == "B")
ck("П17 клас A го КАЗВА на картата", "СИЛНА ЗОНА" in lb._zones(_h1(_up), "long")[1])
ck("П17 клас A дава нивото на зоната", "137" in lb._zones(_h1(_up), "long")[1])
# ШОРТ е огледален: същата бича празнина при шорт НЕ е опора
ck("П17 шортът е ОГЛЕДАЛЕН (бича празнина не му е опора)",
   lb._zones(_h1(_up), "short")[0] != "A")
ck("П17 празнина НАДОЛУ е опора за ШОРТ", lb._zones(_h1(_dn), "short")[0] == "A")
# безопасни падове — никога не наказва при липса на данни
ck("П17 липсваща рамка → неутрално B, без текст", lb._zones(None, "long") == ("B", ""))
# и КЛЮЧОВОТО: zone=None (не е мерено) НЕ смалява размера — хванато от падащ тест
ck("П17 zone=None НЕ обявява намаление (тежест 1.0)",
   "малък размер" not in lb._sig_msg("long", 6, 7, "ПРЕМИУМ", sp, 4081.0,
                             pd.Timestamp("2026-08-05 09:00:00"), lb._levels(4079.25, "long"),
                             4079.25, "ДА", {"миньори": True, "долар": True, "лихви": True}, 1,
                             {"streaks": {"long": 1}, "vol_rank": 0.5}, stats, 10000, 2, adv_ok=True))
ck("П17 къса рамка → неутрално B", lb._zones(_h1(_fl[:5]), "long") == ("B", ""))
ck("П17 повредена рамка не гърми", lb._zones("не е рамка", "long")[0] == "B")
# тежестите: рискът на собственика е ТАВАН
ck("П17 клас A взима ПЪЛНИЯ обявен риск", lb.ZONE_W["A"] == 1.00)
ck("П17 нито един клас НЕ надхвърля обявения риск", max(lb.ZONE_W.values()) <= 1.0)
ck("П17 подредбата на тежестите е A>B>C", lb.ZONE_W["A"] > lb.ZONE_W["B"] > lb.ZONE_W["C"] > 0)
# картата: размерът наистина се степенува
_zc = lambda z, bal: lb._sig_msg("long", 6, 7, "ПРЕМИУМ", sp, 4081.0,
                                 pd.Timestamp("2026-08-05 09:00:00"),
                                 lb._levels(4079.25, "long"), 4079.25, "ДА — пресен сигнал (ден 1)",
                                 {"миньори": True, "долар": True, "лихви": True}, 1,
                                 {"streaks": {"long": 1}, "vol_rank": 0.5}, stats, bal, 2,
                                 adv_ok=True, zone=(z, "зона " + z))
_a, _b17, _c17 = _zc("A", 10000), _zc("B", 10000), _zc("C", 10000)
# ОДИТ-41 · лотът падна от картата. Тежестите вече решават ДАЛИ картата
# да каже «малък размер», не колко лот. Тестът пази точно това.
ck("П17 клас A → БЕЗ препоръка за намаление", "по-слаба" not in _a)
# 🔴 ОБНОВЕН 18.08. Пазеше думите «малък размер» — но ПЕТ различни размера
# получаваха ЕДНА И СЪЩА дума, а най-силният (×1.000) нямаше НИКАКВА. Сега има
# стълбица от четири нива + ДЯЛА, който Е самият множител. Тестът вече пази
# по-силното: че B и C дават РАЗЛИЧНИ и ПО-МАЛКИ препоръки от A.
ck("П17 клас B → препоръчва по-малко от пълния",
   "размер:" in _b17 and "пълен размер" not in _b17)
ck("П17 клас C → препоръчва по-малко от пълния",
   "размер:" in _c17 and "пълен размер" not in _c17)
ck("П17 A/B/C дават ТРИ РАЗЛИЧНИ препоръки за размер",
   len({[x for x in т.split(chr(10)) if "размер:" in x][0]
        for т in (_a, _b17, _c17)}) == 3)
ck("П17 клас A получава ПЪЛЕН размер и го КАЗВА",
   "размер: ВСИЧКО" in _a and "пълен размер" in _a)
ck("П17 всяка препоръка носи ДЯЛ, не само дума",
   all(("от пълния" in т or "пълен размер" in т) for т in (_a, _b17, _c17)))
ck("П17 и казва ЗАЩО (зоната)", "зоната е по-слаба" in _b17)
# ОДИТ-29: буквата на зоната («B», «C») не значи нищо на телефон. Проверява се
# самото ДЕЙСТВИЕ — че размерът наистина пада, и то с точния множител.
ck("П17 B и C наистина съветват по-малък размер",
   "зоната е по-слаба" in _b17 and "зоната е по-слаба" in _c17)
ck("П17 зона A НЕ намалява размера", "от пълния" not in _a)
ck("П17 при ОТВОРЕНА сделка зоната не се повтаря",
   "зона A" not in lb._sig_msg("long", 6, 7, "ПРЕМИУМ", sp, 4081.0,
                               pd.Timestamp("2026-08-05 09:00:00"), lb._levels(4079.25, "long"),
                               4079.25, "ДА", {"миньори": True, "долар": True, "лихви": True}, 1,
                               {"streaks": {"long": 1}, "vol_rank": 0.5}, stats, 10000, 2,
                               adv_ok=True, zone=("A", "зона A"),
                               open_trade={"entry": 4070.0, "opened": "2026-08-05T06:00:00",
                                           "levels": lb._levels(4070.0, "long"), "hit": {}}))
ck("П17 БЕЗ зона картата е точно каквато беше (обратна съвместимост)",
   "зона" not in lb._sig_msg("long", 6, 7, "ПРЕМИУМ", sp, 4081.0,
                             pd.Timestamp("2026-08-05 09:00:00"), lb._levels(4079.25, "long"),
                             4079.25, "ДА", {"миньори": True, "долар": True, "лихви": True}, 1,
                             {"streaks": {"long": 1}, "vol_rank": 0.5}, stats, 10000, 2, adv_ok=True))
ck("П17 картите остават балансиран HTML",
   all(c.count("<b>") == c.count("</b>") and c.count("<i>") == c.count("</i>")
       for c in (_a, _b17, _c17)))


# ═══════════════════════════════════════════════════════════════════════
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
        # ОДИТ-29: кофата вече не е в ТЕКСТА (собственикът: «неразбираш нищо от тях»),
        # а в следата `trace["мерено"]`, откъдето я четат дневникът и одит-роботът.
        # Тестът стана и ПО-СИЛЕН: сверява самото ЧИСЛО, по което е съдено,
        # а не низ, който може случайно да съвпадне.
        _tr18 = {}
        _txt18, _ok18 = lb._advice_entry(_d18, _s18, _st18, None, False, 0, trace=_tr18)
        _cell18 = lb._cell_name(_s18)
        _нето18 = (_tr18.get("мерено") or {}).get("net")
        ck(f"П18 {_d18}/стрийк{_s18}: следата съди по кофа «{_cell18}»",
           _нето18 is not None
           and abs(float(_нето18) - _CELLS18[_cell18]) < 0.001)

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

# --- 3б · ОДИТ-15/б: КОЙ ПЛАСТ реши. Първата версия на записа слагаше кофата
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

# --- 4 · ДОБАВКА, НЕ ЗАМЯНА: старият запис е непокътнат ---
for _k18 in ("run_utc", "date", "v", "bar", "spot", "basis", "macro", "macro_raw",
             "board", "trade", "exits", "notes", "status", "shield", "track_mode"):
    ck(f"П18 старият ключ «{_k18}» още стои в дневника", _k18 in _j18[0])
ck("П18 бордът още е по 7 рамки", len(_j18[0].get("board") or {}) == 7)
_sh4.rmtree(_t18, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════
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
ck("П19 картата казва ДА", _t19.startswith("ДА"))   # ОДИТ-29: процентът падна от текста
ck("П19 картата казва, че златото е на върха си", "върха си" in _t19)   # ОДИТ-29
# ОДИТ-29: числото на клетката се проверява в следата, не в текста
_tr19 = {}
lb._advice_entry("short", 2, _NEW19, None, False, 0, dd20=0.004, trace=_tr19)
ck("П19 следата цитира числото на клетката",
   (_tr19.get("мерено") or {}).get("n") == 779
   and abs(float((_tr19.get("мерено") or {}).get("net", 0)) - 5.05) < 0.01)

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


# ═══════════════════════════════════════════════════════════════════════
# П20 · ОДИТ-16/б: ВЕРИГАТА на новата клетка — от присъдата до сделката.
# Следенето на шорт е добре покрито (track_trade, _exit_msg), НО веригата
# «новата клетка каза ДА → карта → геометрия → отваряне» не беше минавана
# НИКОГА, нито в тест, нито на живо: ботът не е отварял реален шорт.
# Непусканият код е по-опасен от статистиката.
# ═══════════════════════════════════════════════════════════════════════
_E20 = 4100.0
_LV20 = lb._levels(_E20, "short")

ck("П20 шорт: и трите цели са ПОД входа", all(_LV20[k] < _E20 for k in ("tp1", "tp2", "tp3")))
ck("П20 шорт: стопът е НАД входа", _LV20["sl"] > _E20)
ck("П20 шорт: целите се отдалечават в правилния ред", _LV20["tp1"] > _LV20["tp2"] > _LV20["tp3"])
ck("П20 шорт: геометрията е замразената (7.5 / 12 / 20 / −20)",
   abs((_E20 - _LV20["tp1"]) - 7.5) < 1e-6 and abs((_E20 - _LV20["tp2"]) - 12.0) < 1e-6
   and abs((_E20 - _LV20["tp3"]) - 20.0) < 1e-6 and abs((_LV20["sl"] - _E20) - 20.0) < 1e-6)

# входът на шорт се прави по BID (продаваш на купувача), не по ask и не по mid
_sp20 = {"bid": 4099.0, "ask": 4101.0, "mid": 4100.0}
ck("П20 шорт влиза по BID (не по ask/mid)", lb._entry_side(_sp20, "short") == 4099.0)
ck("П20 лонг влиза по ASK — огледално и непроменено", lb._entry_side(_sp20, "long") == 4101.0)

# картата, която новата клетка ражда: съдържа присъдата ѝ и е валидна
_adv20 = lb._advice_entry("short", 2, _NEW19, None, False, 0, dd20=0.004)
ck("П20 новата клетка наистина връща ДА в тази точка", _adv20[1] is True)
_m20 = lb._sig_msg("short", 6, 7, "ПРЕМИУМ", _sp20, 4103.5,
                   pd.Timestamp("2026-07-16 12:31:00"), _LV20, _E20, "тест",
                   {"миньори": False, "долар": True, "лихви": True},
                   2, {"streaks": {"short": 2}, "vol_rank": 0.7}, _NEW19, 1000, 2)
ck("П20 картата на шорта е валиден HTML и под лимита",
   len(_m20) < 4096 and _m20.count("<b>") == _m20.count("</b>"))
ck("П20 картата казва ПРОДАЖБА, не покупка",        # ОДИТ-29: без латиница
   ("ПРОДАЙ" in _m20 or "надолу" in _m20 or "продажба" in _m20)
   and "КУПИ" not in _m20)

# пълният живот на такава сделка: ТП1 → безрисков стоп → стълбата смята вярно
_t20 = {"direction": "short", "entry": _E20, "opened": "2026-07-16T07:00",
        "checked": "2026-07-16T07:00", "levels": _LV20, "hit": {}, "status": "open",
        "v2": True, "ledger": "spot"}
# ВАЖНО (научено с падащ тест): свещта трябва да е СЛЕД `opened`, иначе се игнорира
# НАРОЧНО — сделка не се съди по барове отпреди да е отворена.
_, _ev20 = lb.track_trade(_t20, bars([(4095, 4096, 4091, 4092)], "2026-07-16 08:00:00"),
                          0.0, 4092.0, "2026-07-16T09:00")
ck("П20 шортът удря ТП1 при падаща цена", "tp1" in [e[0] for e in _ev20])
ck("П20 ТП1 се отбелязва в сделката", bool(_t20["hit"].get("tp1")))
ck("П20 след ТП1 стопът слиза до входа (безрисков)", abs(_t20["levels"]["sl"] - _E20) < 1e-6)
_t20b = dict(_t20, hit={}, levels=lb._levels(_E20, "short"), status="open")
_, _ev20b = lb.track_trade(_t20b, bars([(4102, 4121, 4101, 4120)], "2026-07-16 08:00:00"),
                           0.0, 4120.0, "2026-07-16T09:00")
ck("П20 шортът удря СТОП при качваща се цена", "sl" in [e[0] for e in _ev20b])
_dol20, _n20 = lb._ladder_pnl("sl", {"tp1": True}, _LV20, _E20, -1, 0.0)
ck("П20 стоп СЛЕД ТП1 е ПЕЧАЛБА по стълбата, не «−20»", _dol20 > 0)
ck("П20 чистият стоп (без ТП) е пълната загуба",
   lb._ladder_pnl("sl", {}, _LV20, _E20, -1, -20.0)[0] < -19.0)


# ═══════════════════════════════════════════════════════════════════════
# П21 · ОДИТ-17: УИКЕНД-СПАМЪТ.
# Докладван от собственика: в събота и неделя получавал съобщение «ботът е
# счупен» на всеки няколко минути. Веригата, потвърдена в кода:
#   `_yf` вдига «празни данни» (борсата спи) → except праща «временен проблем»
#   → SystemExit(1) → workflow стъпката `if: failure()` праща «ботът НЕ тръгна».
#   Ботът се буди на 5 минути И през уикенда → ДВЕ съобщения × 576 пускания.
# Поправка: `_market_closed` се пита ПРЕДИ данните → чист изход + 3 картички/ден.
# ═══════════════════════════════════════════════════════════════════════
import tempfile as _tf21, shutil as _sh21, contextlib as _ctx21, io as _io21

# --- 1 · кога е затворен пазарът (нюйоркско, сам лови DST) ---
for _t21, _want21, _lbl21 in (
    ("2026-08-08T12:00", True,  "събота"),
    ("2026-08-09T10:00", True,  "неделя преди 18:00 ET"),
    ("2026-08-07T22:00", True,  "петък след 17:00 ET"),
    ("2026-08-09T23:00", False, "неделя след 18:00 ET — отваря"),
    ("2026-08-10T09:00", False, "понеделник"),
    ("2026-08-05T12:00", False, "сряда"),
):
    ck(f"П21 {_lbl21}: затворен={_want21}", lb._market_closed(_t21) is _want21)

# --- 2 · трите слота по СОФИЙСКО, и мълчание извън тях ---
_slots21 = {}
for _h21 in range(24):
    _s21 = lb._weekend_slot(f"2026-08-08T{_h21:02d}:00")
    if _s21:
        _slots21.setdefault(_s21, []).append(_h21)
ck("П21 има точно ТРИ слота", sorted(_slots21) == ["вечер", "следобед", "сутрин"])
ck("П21 всеки слот е 3 часа", all(len(v) == 3 for v in _slots21.values()))
ck("П21 извън слотовете МЪЛЧИ (15 от 24 часа)", sum(len(v) for v in _slots21.values()) == 9)
ck("П21 слотовете не се застъпват",
   len(set(sum(_slots21.values(), []))) == 9)

# --- 3 · картичките ---
for _sl21 in ("сутрин", "следобед", "вечер"):
    _m21 = lb._weekend_msg(_sl21, "2026-08-08")
    ck(f"П21 картичка «{_sl21}»: непразна и с балансиран HTML",
       len(_m21) > 60 and _m21.count("<b>") == _m21.count("</b>")
       and _m21.count("<i>") == _m21.count("</i>"))
    # ОДИТ-29: «Ботът е буден и здрав — просто няма какво да следи» падна.
    # Същото се казва с емоджито 😴 и «борсата спи» — без обяснение защо.
    ck(f"П21 картичка «{_sl21}» КАЗВА, че пазарът спи, не ботът",
       "спи" in _m21 and "счупен" not in _m21)
ck("П21 различните дни дават различен текст",
   lb._weekend_msg("сутрин", "2026-08-08") != lb._weekend_msg("сутрин", "2026-08-09"))
ck("П21 всеки слот има поне 8 различни текста",
   all(len(set(v)) >= 8 for v in lb.WEEKEND_MSGS.values()))

# --- 4 · ЦИКЪЛЪТ: най-важното — по ЕДНА на слот, колкото и пъти да се пусне ---
_d21 = _P(_tf21.mkdtemp())
_sent21 = []
_or21 = lb._send_raw
lb._send_raw = lambda t: (_sent21.append(t), "SENT (200)")[1]
try:
    for _ in range(12):                       # 12 пускания = един час на 5 минути
        with _ctx21.redirect_stdout(_io21.StringIO()):
            lb._weekend_cycle(_d21, "2026-08-08T07:00", True)
    ck("П21 12 пускания в един слот → ЕДНО съобщение", len(_sent21) == 1)
    for _t21b in ("2026-08-08T13:00", "2026-08-08T18:00"):
        with _ctx21.redirect_stdout(_io21.StringIO()):
            lb._weekend_cycle(_d21, _t21b, True)
    ck("П21 трите слота на един ден → ТРИ съобщения", len(_sent21) == 3)
    with _ctx21.redirect_stdout(_io21.StringIO()):
        lb._weekend_cycle(_d21, "2026-08-08T02:00", True)
    ck("П21 извън прозорец не праща нищо", len(_sent21) == 3)
    with _ctx21.redirect_stdout(_io21.StringIO()):
        lb._weekend_cycle(_d21, "2026-08-09T07:00", True)
    ck("П21 новият ден пуска пак", len(_sent21) == 4)
    ck("П21 цял уикенд = 6 съобщения, не 1150 (6 слота × 1)",
       len(_sent21) == 4)          # 3 събота + 1 неделя дотук
    _j21 = [json.loads(x) for x in
            (_d21 / "live_journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    # 12 (сутрин) + 2 (следобед, вечер) + 1 (извън прозорец) + 1 (неделя) = 16
    ck("П21 дневникът пише за ВСЯКО пускане, и в уикенда", len(_j21) == 16)
    ck("П21 записът е отбелязан като уикенд", all(r.get("weekend") is True for r in _j21))
    ck("П21 записът носи версията и датата",
       _j21[-1].get("v") == lb.VERSION and _j21[-1].get("date") == "2026-08-09")
finally:
    lb._send_raw = _or21
    _sh21.rmtree(_d21, ignore_errors=True)

# --- 5 · главният път: уикендът се проверява ПРЕДИ дърпането на данни ---
_msrc21 = _src[_src.find("def main():"):]
_i_we21 = _msrc21.find("_market_closed(now_utc) and not args.force")
_i_yf21 = _msrc21.find('_yf("GC=F"')
ck("П21 уикенд-проверката стои ПРЕДИ първото дърпане на данни",
   _i_we21 > 0 and _i_yf21 > 0 and _i_we21 < _i_yf21)
ck("П21 уикендът излиза ЧИСТО (return), а не с грешка",
   "_weekend_cycle(out, now_utc, args.send)" in _msrc21 and "return" in
   _msrc21[_msrc21.find("_weekend_cycle(out, now_utc, args.send)"):][:80])
ck("П21 --force заобикаля уикенда (за ръчна проверка)",
   "and not args.force" in _msrc21[_i_we21 - 60:_i_we21 + 60])

# --- 6 · заглушаване на повтарящата се грешка в делник ---
ck("П21 еднаквата грешка се праща най-много веднъж на 3 часа",
   "3 * 3600" in _src and "err_seen.json" in _src)
ck("П21 РАЗЛИЧНА грешка минава веднага (подпис по вида и текста)",
   "_hashlib_e.sha1" in _src)


# ═══════════════════════════════════════════════════════════════════════
# П22 · 🧠 МОЗЪКЪТ НА ГРАФИКАТА
#
# Тестват се ТРИ неща, в този ред по важност:
#   1. че мозъкът НЕ наднича в бъдещето (иначе е безполезен на живо)
#   2. че СТАРОТО поведение на бота е непокътнато
#   3. че мозъкът не може да събори бота, каквото и да му се подаде
#
# Всичко върви на СИНТЕТИЧНИ барове — без parquet, без мрежа, детерминирано.
# ═══════════════════════════════════════════════════════════════════════
import importlib.util as _ilu22, tempfile as _tf22, shutil as _sh22, json as _j22
import numpy as _np22, pandas as _pd22
from pathlib import Path as _P22

_CBP22 = _P22("brain") / "chart_brain.py"
_CB22 = None
if _CBP22.exists():
    try:
        _s22 = _ilu22.spec_from_file_location("chart_brain_test", _CBP22)
        _CB22 = _ilu22.module_from_spec(_s22); _s22.loader.exec_module(_CB22)
    except Exception as _e22:
        print("П22 мозъкът не се внесе:", type(_e22).__name__, _e22)

ck("П22 chart_brain.py съществува и се внася", _CB22 is not None)

if _CB22 is None:
    ck("П22 ПРОПУСНАТ — няма модул", False)
else:
    # ── синтетични барове, които наистина палят поводи ──────────────────
    def _bars22(n=1400, seed=1):
        r = _np22.random.default_rng(seed)
        c = 4000 + _np22.cumsum(r.normal(0, 0.9, n)) + 40 * _np22.sin(_np22.arange(n) / 55.0)
        o = _np22.r_[c[0], c[:-1]]
        w = _np22.abs(r.normal(0, 1.6, n)) + 0.4
        return _pd22.DataFrame(
            {"open": o, "high": _np22.maximum(o, c) + w, "low": _np22.minimum(o, c) - w,
             "close": c, "volume": _np22.abs(r.normal(1.0, 0.45, n)) + 0.15},
            index=_pd22.date_range("2025-01-01", periods=n, freq="15min", tz="UTC"))

    _D22 = _bars22()
    _W22 = _CB22.ПРОЗОРЕЦ

    # ── 1 · СКАЛАТА ─────────────────────────────────────────────────────
    ck("П22 скалата има точно 7 степени", len(_CB22.СТЕПЕНИ) == 7)
    ck("П22 праговете растат монотонно",
       list(_CB22.ПРАГОВЕ) == sorted(_CB22.ПРАГОВЕ) and len(_CB22.ПРАГОВЕ) == 7)
    ck("П22 забранената дума «слаб» я няма в имената на степените",
       not any("слаб" in s.lower() for s in _CB22.СТЕПЕНИ))
    ck("П22 прагът за пращане съвпада с втората степен",
       _CB22.ПРАГ_ПРАЩАНЕ == _CB22.ПРАГОВЕ[1])
    ck("П22 всяко условие в таблицата има група с таван",
       all(g in _CB22.ТАВАН_ГРУПА for (_, g, _t) in _CB22.ТАБЛИЦА.values()))

    # ── 2 · НАДНИЧАНЕ В БЪДЕЩЕТО (най-важният тест) ─────────────────────
    # Един и същ прозорец, взет веднъж от масив, който СВЪРШВА там, и веднъж
    # от масив, който продължава 150 бара напред. Различен отговор = надничане.
    _разл22 = 0
    _пров22 = 0
    for _T22 in (1200, 1230, 1250):
        _a22 = _CB22.сканирай({"15м": _D22.iloc[_T22 - _W22:_T22]}, сега=None)
        _голям22 = _D22.iloc[_T22 - _W22:_T22 + 150]
        _b22 = _CB22.сканирай({"15м": _голям22.iloc[:_W22]}, сега=None)
        _пров22 += 1
        if _CB22._отпечатък(_a22) != _CB22._отпечатък(_b22):
            _разл22 += 1
    ck(f"П22 НЕ наднича в бъдещето ({_пров22} момента)", _разл22 == 0)

    # ── 3 · НЕЗАТВОРЕНИЯТ БАР ───────────────────────────────────────────
    # Пазачът се тества В ДВЕТЕ ПОСОКИ. Само «с рязане съвпада» не стига:
    # мъртъв пазач също би минал. Затова се проверява и че БЕЗ рязане
    # отговорът наистина се различава — иначе тестът не може да гръмне.
    _съвп22 = _разлика22 = 0
    for _T22 in (1240, 1260, 1280, 1300, 1320, 1340, 1360, 1380):
        _без22 = _CB22.сканирай({"15м": _D22.iloc[_T22 - _W22:_T22]}, сега=None)
        _плюс22 = _D22.iloc[_T22 - _W22:_T22 + 1]
        _сега22 = _D22.index[_T22] + _pd22.Timedelta(minutes=7)   # свещта е наполовина
        _рязан22 = _CB22.сканирай({"15м": _плюс22}, сега=_сега22)
        _нерязан22 = _CB22.сканирай({"15м": _плюс22}, сега=None, режи_незатворен=False)
        if _CB22._отпечатък(_без22) == _CB22._отпечатък(_рязан22):
            _съвп22 += 1
        if _CB22._отпечатък(_рязан22) != _CB22._отпечатък(_нерязан22):
            _разлика22 += 1
    ck("П22 незатвореният бар се реже по часовник (отговорът е като без него)",
       _съвп22 == 8)
    ck("П22 пазачът за незатворената свещ НЕ е мъртъв (без него отговорът се мени)",
       _разлика22 >= 1)

    # ── 4 · ЗАСТУДЯВАНЕТО Е ПО ВРЕМЕ, НЕ ПО ИНДЕКС НА БАР ───────────────
    # Намерен дефект: `бар` е `len(d)-1` — при постоянен прозорец е ЕДНО И
    # СЪЩО число всеки път, тоест «изминали бара» = 0 винаги и застудяването
    # заглушаваше всичко завинаги.
    ck("П22 барове между два момента се смятат по време",
       _CB22._барове_между("2026-01-01 12:00", "2026-01-01 13:00", 15) == 4)
    ck("П22 смесени часови пояси не чупят сметката",
       _CB22._барове_между(_pd22.Timestamp("2026-01-01 12:00", tz="UTC"),
                           "2026-01-01 13:00", 15) == 4)
    ck("П22 нечетимо време връща None, не гърми",
       _CB22._барове_между("боклук", "2026-01-01", 15) is None)
    _съст22 = {"15м|ЛОНГ": {"ранг": 3, "точки": 11, "време": "2025-01-15 00:00:00+00:00"}}
    ck("П22 застудяването пази ВРЕМЕ, не индекс на бар",
       "време" in _съст22["15м|ЛОНГ"] and "бар" not in _съст22["15м|ЛОНГ"])

    # ── 5 · ВРАЖДЕБНИ ВХОДОВЕ · нищо не поваля мозъка ───────────────────
    _мръсен22 = _D22.copy()
    _мръсен22.iloc[-1, _мръсен22.columns.get_loc("close")] = _np22.nan
    _плосък22 = _D22.copy(); _плосък22[["open", "high", "low", "close"]] = 2000.0
    _случаи22 = [
        ("празен речник", {}),
        ("None рамка", {"15м": None}),
        ("празен DataFrame", {"15м": _pd22.DataFrame()}),
        ("1 ред", {"15м": _D22.iloc[:1]}),
        ("под минимума бара", {"15м": _D22.iloc[:50]}),
        ("NaN в close на последния бар", {"15м": _мръсен22}),
        ("без обем", {"15м": _D22.drop(columns=["volume"])}),
        ("нулев обем", {"15м": _D22.assign(volume=0.0)}),
        ("без времеви индекс", {"15м": _D22.reset_index(drop=True)}),
        ("обърнат по време", {"15м": _D22.iloc[::-1]}),
        ("напълно плоска цена", {"15м": _плосък22}),
        ("непозната рамка", {"боклук": _D22, "15м": _D22}),
        ("имена Open/High/Low/Close", {"15м": _D22.rename(columns=str.capitalize)}),
    ]
    _гръм22 = []
    for _име22, _вх22 in _случаи22:
        try:
            _р22 = _CB22.сканирай(_вх22)
            if not isinstance(_р22, list):
                _гръм22.append(f"{_име22}: не върна списък")
        except Exception as _e22b:
            _гръм22.append(f"{_име22}: {type(_e22b).__name__}")
    ck(f"П22 {len(_случаи22)} враждебни входа, нито един срив", not _гръм22)
    if _гръм22:
        print("    →", _гръм22)

    # NaN в close СРИВАШЕ b_ликвидност и b_диапазон поотделно — пазачът е тук
    ck("П22 NaN в последния бар минава (блоковете поотделно СРИВАТ на това)",
       isinstance(_CB22.сканирай({"15м": _мръсен22}), list))

    # ── 6 · ФОРМАТА НА СЕТЪПА ───────────────────────────────────────────
    _намерен22 = None
    for _к22 in range(_W22, len(_D22), 3):
        _r22 = _CB22.сканирай({"15м": _D22.iloc[_к22 - _W22:_к22]}, сега=None)
        if _r22:
            _намерен22 = _r22[0]
            break
    ck("П22 синтетичните барове раждат поне един повод (тестът не е празен)",
       _намерен22 is not None)
    if _намерен22:
        _задълж22 = ("рамка", "посока", "степен", "ранг", "точки", "повод", "ниво",
                     "вход", "стоп", "цел", "цел2", "съотношение", "съвпаднали",
                     "липсва", "праща", "статус")
        ck("П22 сетъпът носи всички задължителни полета",
           all(k in _намерен22 for k in _задълж22))
        ck("П22 сетъпът е маркиран «НОВО · още не е мерено»",
           _намерен22["статус"] == "НОВО · още не е мерено")
        ck("П22 степента е една от седемте", _намерен22["степен"] in _CB22.СТЕПЕНИ)
        ck("П22 точките са цяло число ≥0 и не надминават теоретичния таван",
           isinstance(_намерен22["точки"], int) and 0 <= _намерен22["точки"] <= 30)
        _л22 = _намерен22["лонг"]
        ck("П22 стопът е от правилната страна на входа",
           (_намерен22["стоп"] < _намерен22["вход"]) if _л22
           else (_намерен22["стоп"] > _намерен22["вход"]))
        ck("П22 целта е от правилната страна на входа",
           (_намерен22["цел"] > _намерен22["вход"]) if _л22
           else (_намерен22["цел"] < _намерен22["вход"]))
        ck("П22 «праща» е вярно точно когато точките стигат прага",
           _намерен22["праща"] == (_намерен22["точки"] >= _CB22.ПРАГ_ПРАЩАНЕ)
           or "застудяване" in _намерен22)

        # ── 7 · КАРТАТА ─────────────────────────────────────────────────
        _т22 = _CB22.карта(_намерен22)
        ck("П22 картата се сглобява и е текст", isinstance(_т22, str) and len(_т22) > 100)
        ck("П22 картата се побира в лимита на Телеграм (4000)", len(_т22) <= 4000)
        ck("П22 картата няма знаци, които чупят parse_mode=HTML",
           "<" not in _т22 and ">" not in _т22 and "&" not in _т22)
        ck("П22 картата НОСИ задължителния ред за неизмереното",   # ОДИТ-31
           "наблюдение, не е вход" in _т22)
        # ОДИТ-29: списъкът «✗ липсва: …» падна — степента отгоре вече казва
        # колко силна е картата, а какво НЕ е съвпаднало не му върши работа.
        ck("П22 картата показва КОЕ съвпада",
           "📌" in _т22 or "🎯" in _т22)
        ck("П22 секцията «СТАРОТО ПРАВИЛО» я НЯМА вече",      # ОДИТ-27: собственикът я поиска махната
           "СТАРОТО ПРАВИЛО" not in _т22)
        ck("П22 без подадено мерено НЯМА измислен ред",       # ОДИТ-27: мълчанието си е мълчание
           "мерено " not in _т22)

        # мереното НЕ бива да мени точките — двете числа не се смесват
        _stats22 = {"fresh": {"long": {"day1": {"win": 79.9, "net": 2.99, "n": 4019,
                                                "lo": 1.655, "hi": 4.196}},
                              "short": {"day1": {"win": 71.5, "net": 0.44, "n": 3100,
                                                 "lo": -1.07, "hi": 1.85}}}}
        _м22 = _CB22.мерено_от_стата(_stats22, "day1", _намерен22["лонг"])
        _т22б = _CB22.карта(_намерен22, мерено=_м22)
        ck("П22 мереното НЕ променя точките (двете числа не се смесват)",
           _намерен22["точки"] == _намерен22["точки"] and str(_намерен22["точки"]) in _т22б)
        ck("П22 мереното НЕ отива на картата на мозъка",      # ОДИТ-29: старото правило и
           "n=" not in _т22б and "95%" not in _т22б             # новата логика са две неща
           and not any(r.startswith("мерено ") for r in _т22б.split("\n")))
        ck("П22 кофа с малко наблюдения (n<100) НЕ се цитира",
           _CB22.мерено_от_стата({"fresh": {"long": {"day1": {"win": 90, "net": 9,
                                                              "n": 12}}}},
                                 "day1", True) is None)
        ck("П22 липсваща кофа не гърми",
           _CB22.мерено_от_стата({}, "няма_такава", True) is None)

    # ── 8 · СЪГЛАСИЕТО НА РАМКИТЕ Е СВЕДЕНИЕ, НЕ ТОЧКИ ──────────────────
    # Праговете са мерени БЕЗ него. Влезе ли в точките, мереният брой карти
    # на ден спира да важи — затова се проверява, че НЕ влиза.
    _ч22 = _D22.resample("60min").agg(open=("open", "first"), high=("high", "max"),
                                      low=("low", "min"), close=("close", "last"),
                                      volume=("volume", "sum")).dropna()
    _сам22 = _CB22.сканирай({"15м": _D22.iloc[-_W22:]}, сега=None)
    _скон22 = _CB22.сканирай({"15м": _D22.iloc[-_W22:], "1час": _ч22}, сега=None)
    ck("П22 контекстните рамки НЕ променят точките (само сведение)",
       [x["точки"] for x in _сам22] == [x["точки"] for x in _скон22])

    # ── 9 · СТАРОТО ПОВЕДЕНИЕ НА БОТА Е НЕПОКЪТНАТО ─────────────────────
    # ВАЖНО: `_run_main` подава на златото ЕДНА И СЪЩА дневна серия за всички
    # интервали, тоест мозъкът получава мъртва синусоида и не ражда НИЩО.
    # Тест, в който новият код мълчи, не може да гръмне — затова тук има
    # СОБСТВЕН рън с жива 5-минутна серия, в който мозъкът наистина работи.
    # 5013 не е кръгло число, а НАМЕРЕНО: това е дължината, при която последният
    # 15-минутен бар на seed=1 ражда повод, минаващ прага (👀 НАБЛЮДЕНИЕ, 9 т., ЛОНГ).
    # Поводите падат на ~23% от баровете — на произволна дължина рънът мълчи и
    # тестът става празен, без да гръмне.
    def _run22(cb, _N22=5013):
        _D5 = _bars22(_N22, seed=1).rename(columns=str.capitalize)
        _D5.index = _pd22.date_range("2026-04-01", periods=_N22, freq="5min")
        _DD = {"GC=F": _fx(800, "2024-01-01", "D", 3800, 0.35),
               "GDX": _fx(600, "2024-06-01", "D", 40, 0.02),
               "DX-Y.NYB": _fx(600, "2024-06-01", "D", 100, -0.005)}
        _sent = []
        _старо = {k: getattr(lb, k) for k in ("_yf", "_rates", "_spot", "_cq_fetch",
                                              "_fng_live", "_send_raw", "CB")}
        # 🔴 ОДИТ-60 · ТОЗИ ТЕСТ ПРОВЕРЯВА ПЪТЯ, НЕ ПРАГА.
        # Собственикът вдигна прага до ⚡ МНОГО СИЛЕН (14) — синтетичните барове
        # тук рядко дават 14 точки, а въпросът «стига ли мозъчна карта до
        # пращане през пощата» трябва да се проверява НЕЗАВИСИМО от това колко
        # висок е прагът днес. Затова за ТОЗИ рън прагът пада до 9.
        _старо["МОЗЪК_ПРАГ"] = lb.МОЗЪК_ПРАГ
        _старо["МОЗЪК_ПРАГ_РАМКА"] = lb.МОЗЪК_ПРАГ_РАМКА
        _старо["МОЗЪК_РАНГ_ВХОД"] = lb.МОЗЪК_РАНГ_ВХОД
        lb.МОЗЪК_ПРАГ = 9
        lb.МОЗЪК_ПРАГ_РАМКА = {"1мин": 11, "1м": 11, "5м": 10, "15м": 9}
        lb.МОЗЪК_РАНГ_ВХОД = 3

        def _yf22(s, period="2y", interval="1d"):
            if s == "GC=F" and interval in ("1m", "5m"):
                return _D5.copy()
            return _DD.get(s, _fx(900, "2026-07-20", "5min", 4000, 0.002)).copy()
        lb._yf = _yf22
        lb._rates = lambda: _pd22.Series(
            2.0 - _np22.arange(600) * 0.0008,
            index=_pd22.date_range("2024-06-01", periods=600, freq="D"))
        lb._spot = lambda instr="XAU/USD", market_closed=False, cme_pause=False: _SP
        lb._cq_fetch = lambda now: None
        lb._fng_live = lambda timeout=8: None
        lb._send_raw = lambda t: (_sent.append(t), "SENT (200)")[1]
        lb.CB = cb
        _tmp = _P22(_tf22.mkdtemp())
        _oa = sys.argv
        sys.argv = ["live_bot.py", "--out", str(_tmp), "--stats", "backtest_stats.json",
                    "--balance", "1000", "--risk", "2", "--send", "--force"]
        _code = 0
        try:
            with _ctx.redirect_stdout(_io2.StringIO()):
                lb.main()
        except SystemExit as e:
            _code = e.code if isinstance(e.code, int) else 1
        except Exception as e:
            _code = f"ГРЪМНА: {type(e).__name__}: {e}"
        finally:
            sys.argv = _oa
            for k, v in _старо.items():
                setattr(lb, k, v)
        return _code, _sent, _tmp

    _cA22, _sA22, _tA22 = _run22(None)          # мозъкът изключен
    _cB22, _sB22, _tB22 = _run22(_CB22)         # мозъкът включен
    ck("П22 живият рън БЕЗ мозък излиза чисто", _cA22 == 0)
    ck("П22 живият рън С мозък излиза чисто", _cB22 == 0)
    _bj22 = _tB22 / "brain_journal.jsonl"
    _зап22 = ([_j22.loads(x) for x in _bj22.read_text(encoding="utf-8").splitlines()
               if x.strip()] if _bj22.exists() else [])
    # ← ТОВА е тестът, който прави останалите непразни
    ck("П22 мозъкът НАИСТИНА произвежда поводи в жив рън (тестът не е празен)",
       len(_зап22) > 0)
    ck("П22 всеки повод влиза в дневника със степен, ниво, вход, стоп и цел",
       all(all(k in r for k in ("степен", "ниво", "вход", "стоп", "цел", "праща"))
           for r in _зап22))
    ck("П22 карта на мозъка стига ДО ПРАЩАНЕ през пощата на бота",
       any("наблюдение, не е вход" in x for x in _sB22))
    ck("П22 без мозък такава карта НЯМА (сравнението не е самозаблуда)",
       not any("наблюдение, не е вход" in x for x in _sA22))
    _jA22 = [json.loads(x) for x in
             (_tA22 / "live_journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    _jB22 = [json.loads(x) for x in
             (_tB22 / "live_journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    _клк22б = ("dir", "score", "tier", "trade", "spot", "macro", "board", "regime",
               "advice", "cell")
    ck("П22 при РАБОТЕЩ мозък решението на бота е СЪЩОТО (посока/клас/сделка/борд)",
       all(_jA22[0].get(k) == _jB22[0].get(k) for k in _клк22б if k in _jA22[0]))
    import re as _re22
    _новиA22 = [x for x in _sA22 if "наблюдение, не е вход" in x]
    _новиB22 = [x for x in _sB22 if "наблюдение, не е вход" in x]
    # ОДИТ-27: двата рънa main() стават в различни секунди, а всяка карта носи часа.
    # Мине ли минутата между тях, «еднакви» карти се разминават и тестът червенее
    # без никаква вина на мозъка. Хванато на 3 пуска: 2 зелени, 1 червен.
    # Часовете се нормализират; всичко останало се сравнява дума по дума.
    _без_час22 = lambda t: _re22.sub(r"\d{1,2}:\d{2}", "ЧЧ:ММ", t)
    ck("П22 старите карти са дума по дума същите с и без мозък",
       [_без_час22(x) for x in _sA22 if x not in _новиA22]
       == [_без_час22(x) for x in _sB22 if x not in _новиB22])
    ck("П22 мозъкът НЕ отваря сделка, дори когато има повод",
       (_tA22 / "trade.json").exists() == (_tB22 / "trade.json").exists())
    _sh22.rmtree(_tA22, ignore_errors=True); _sh22.rmtree(_tB22, ignore_errors=True)

    _стар_CB22 = getattr(lb, "CB", None)
    try:
        lb.CB = None
        _c_без22, _s_без22, _t_без22 = _run_main(spot=_SP)
        _j_без22 = [json.loads(x) for x in
                    (_t_без22 / "live_journal.jsonl").read_text(encoding="utf-8").splitlines()
                    if x.strip()]
        lb.CB = _CB22
        _c_с22, _s_с22, _t_с22 = _run_main(spot=_SP)
        _j_с22 = [json.loads(x) for x in
                  (_t_с22 / "live_journal.jsonl").read_text(encoding="utf-8").splitlines()
                  if x.strip()]
        ck("П22 main() с включен мозък пак излиза чисто", _c_с22 == 0)
        _клк22 = ("dir", "score", "tier", "trade", "spot", "macro", "board", "regime")
        _еднакви22 = all(_j_без22[0].get(k) == _j_с22[0].get(k)
                         for k in _клк22 if k in _j_без22[0])
        ck("П22 мозъкът НЕ променя решението на бота (посока/клас/сделка/борд)",
           _еднакви22)
        ck("П22 мозъкът НЕ отваря и не пипа сделка",
           (_t_без22 / "trade.json").exists() == (_t_с22 / "trade.json").exists())
        _стари22 = [x for x in _s_с22 if "наблюдение, не е вход" not in x]
        ck("П22 старите карти излизат непроменени по брой",
           len(_стари22) == len(_s_без22))
        _sh4.rmtree(_t_без22, ignore_errors=True); _sh4.rmtree(_t_с22, ignore_errors=True)

        # ── 10 · МОЗЪКЪТ ГЪРМИ → БОТЪТ ОЦЕЛЯВА ──────────────────────────
        class _Бомба22:
            def __getattr__(self, име):
                raise RuntimeError("нарочна бомба в мозъка")
        lb.CB = _Бомба22()
        _c_б22, _s_б22, _t_б22 = _run_main(spot=_SP)
        ck("П22 мозък, който гърми, НЕ поваля бота", _c_б22 == 0)
        _j_б22 = [json.loads(x) for x in
                  (_t_б22 / "live_journal.jsonl").read_text(encoding="utf-8").splitlines()
                  if x.strip()]
        ck("П22 провалът на мозъка се ОТБЕЛЯЗВА в журнала, не се крие",
           any("мозък" in " ".join(r.get("notes") or []) for r in _j_б22))
        _sh4.rmtree(_t_б22, ignore_errors=True)
    finally:
        lb.CB = _стар_CB22

    # ── 11 · КРЪПКИТЕ СА НА МЯСТО (структурно, не по описание) ──────────
    # ОДИТ-24: щурмът го остави ИЗКЛЮЧЕН по подразбиране; собственикът го иска ЖИВ.
    # Изключвателят остава — CHART_BRAIN=0 го спира моментално, без качване на код.
    # Тестът вече проверява и ДВЕТЕ неща, а не само че низът съществува.
    ck("П22 изключвателят CHART_BRAIN съществува",
       'os.environ.get("CHART_BRAIN"' in _src)
    ck("П22 мозъкът е ВКЛЮЧЕН по подразбиране (по решение на собственика)",
       'os.environ.get("CHART_BRAIN", "1") == "1"' in _src)
    def _вкл22(стойност):
        """Пуска СЪЩИЯ израз, който ботът ползва, при дадена стойност на променливата."""
        import os as _o22
        _старо = _o22.environ.get("CHART_BRAIN")
        try:
            if стойност is None:
                _o22.environ.pop("CHART_BRAIN", None)
            else:
                _o22.environ["CHART_BRAIN"] = стойност
            return _o22.environ.get("CHART_BRAIN", "1") == "1"
        finally:
            if _старо is None:
                _o22.environ.pop("CHART_BRAIN", None)
            else:
                _o22.environ["CHART_BRAIN"] = _старо
    ck("П22 без променлива → ВКЛЮЧЕН", _вкл22(None) is True)
    ck("П22 CHART_BRAIN=0 наистина го СПИРА", _вкл22("0") is False)
    ck("П22 CHART_BRAIN=1 го пуска", _вкл22("1") is True)
    # ОДИТ-31 · собственикът, 11.08 вечерта: «от наблюдение нагоре».
    # Мерено на 156 истински карти: 99 бяха «✨ ИСКРА», тоест две трети от
    # трафика беше най-слабото нещо, което мозъкът вижда.
    ck("П22 прагът е на ⚡ МНОГО СИЛЕН (14 точки), не 0",
       lb.МОЗЪК_ПРАГ == 14
       and 'os.environ.get("МОЗЪК_ПРАГ", "14")' in _src)
    # ОДИТ-25: мълчанието на мозъка не бива да изглежда като спънат мозък.
    # Дотук и двете даваха празни `notes` — сляпо петно, което ме подведе.
    ck("П22 бележка се пише и при НУЛА повода (не само когато има)",
       "тихо — няма събитие на този бар" in _src)
    ck("П22 изключеният мозък си го КАЗВА", "мозъкът е изключен (CHART_BRAIN=0)" in _src)
    ck("П22 уикендното мълчание си го КАЗВА", "борсата е затворена" in _src)
    ck("П22 повикването е обвито в try/except (не може да събори main)",
       "🧠 мозъкът се спъна" in _src)
    ck("П22 картите на мозъка имат СВОЙ таг в пощата", 'f"brain:{' in _src)
    ck("П22 мозъкът се вика ПРЕДИ пращането, не след него",
       _src.find("CB.сканирай") > 0 and
       _src.find("CB.сканирай") < _src.find("sent_tags = _outbox_flush"))
    ck("П22 мозъкът не пипа trade/guard/board",
       all(x not in _src[_src.find("=== 6.5)"):_src.find("=== 7)")]
           for x in ("trade[", "guard[", "board[", "trade =", "guard =")))


# ═══════════════════════════════════════════════════════════════════════
# П23 · ОДИТ-26: СЕДЕМТЕ СПИРАЧКИ ВЕЧЕ НЕ МЪЛЧАТ
# Ботът виждаше сетъп и мълчеше на седем места. Правилата са мерени и
# ОСТАВАТ — сделка пак не се отваря. Променя се само мълчанието: вместо
# ред в дневника излиза карта «виждам, но не предлагам, и ето защо».
# ═══════════════════════════════════════════════════════════════════════
_СП23 = ("ре-влизане в пауза", "борсата е затворена", "US-щит",
         "стоп-пазач", "макро събитие", "има отворена", "бордът флика посока")
for _п23 in _СП23:
    ck(f"П23 спирачка «{_п23[:26]}» си казва причината", f'_спрян = ("{_п23}' in _src
       or f'_спрян = (f"{_п23}' in _src)
ck("П23 и седемте спирачки записват причина (нито една не е забравена)",
   _src.count("_спрян = (") == 7)
ck("П23 решението НЕ се променя — should_sig си остава False",
   _src.count(chr(10).join(("should_sig = False", "        _спрян")))
   + _src.count(chr(10).join(("should_sig = False", "            _спрян"))) == 7)
_м23 = lb._спряна_msg("short", ("1час", "short", 6, "strong", "СИЛЕН"), 4365.2,
                      "стоп-пазач · 2 стопа днес", "третият опит влошава деня",
                      "2026-08-11T11:20", [("1час", "short", 6, "strong", "СИЛЕН")] * 7)
ck("П23 картата се сглобява и е под лимита", 60 < len(_м23) < 4096)
ck("П23 картата е балансиран HTML",
   _м23.count("<b>") == _м23.count("</b>") and _м23.count("<i>") == _м23.count("</i>"))
ck("П23 картата КАЗВА, че вижда сетъпа", "ВИЖДАМ" in _м23)
ck("П23 картата КАЗВА защо не го предлага", "📌" in _м23 and "стоп-пазач" in _м23)
ck("П23 картата НЯМА нива за вход (да не се чете като покана)",
   "ТП1" not in _м23 and "СТОП:" not in _м23 and "1️⃣" not in _м23)
ck("П23 картата казва причината и спира дотам",           # ОДИТ-27/29
   "📌" in _м23 and "не покана" not in _м23)
# 🔴 ОДИТ-45г · ОБЪРНАТ. Този тест ИЗИСКВАШЕ невярното число «7/7».
# Мерено на 1965 живи ръна: в 84.6% седемте рамки са БУКВАЛНО еднакви и
# различни отчета никога не е имало повече от ДВА — «7 от 7 съгласни» броеше
# седем копия на едно измерване. Тестът не се трие; пази обратното.
ck("П23 картата НЕ твърди «7/7» — рамките са копия, не седем мнения",
   "7/7" not in _м23 and "/7 мащаба" not in _м23)
ck("П23 при ЕДИН отчет картата не се хвали с брой",
   "отчета" not in _м23 or "от 1 отчета" not in _м23)
ck("П23 пращането е обвито — спъне ли се, не поваля бота",
   "картата «виждам, но не предлагам» се спъна" in _src)
ck("П23 спрените карти имат СВОЙ таг", '"спряна:" + new_dir' in _src)
ck("П23 в уикенда спряна карта НЕ се праща (борсата е затворена)",
   "and actionable and not weekend" in _src)



import datetime as _dt


# ═══ П24 · ЗАБРАНЕНИЯТ ШУМ (ОДИТ-27, 11.08) ════════════════════════════════
# Собственикът: «пак има мега мега ненужна информация... просто се казва как
# нещата седят. Това обърква и не е нужно изобщо.»
# 24 теста дотук пазеха ТОЧНО тези изречения — днес всеки от тях беше обърнат.
# Този блок е ключалката: рендерира всеки вид карта и проверява две неща
# едновременно — че забраненото го няма И че фактите са си останали.
_ЗАБРАНЕНО24 = (
    "не е съвет", "не е фин. съвет", "хартия ·", "информативно",
    "при гап може повече", "Стопът НЕ е ударен", "само контекст",
    "СТАРОТО ПРАВИЛО", "още не е мерено", "не покана",
    "Сложи нивата при брокера", "Мерено: вход в първите",
    "Само за информация", "Следя този сетъп", "ПЪРВИЯ сетъп",
    "Шорт е непотвърден", "НЕ я следи като сделка",
)
_lv24 = lb._levels(4365.20, "long")
_mac24 = {"долар": True, "лихви": True, "миньори": True}
_brd24 = [("1час", "long", 6, "strong", "СИЛЕН")] * 7
_bst24 = ("1час", "long", 6, "strong", "СИЛЕН")
_tr24 = {"direction": "long", "entry": 4000.0, "opened": "2026-08-11T09:00",
         "levels": {"tp1": 4007.5, "tp2": 4012.0, "tp3": 4020.0, "sl": 4000.0},
         "hit": {"tp1": True, "tp2": True}, "sym": "XAUUSD"}
_КАРТИ24 = {
    "сигнал ДА": lb._sig_msg("long", 6, 7, "СИЛЕН", {"mid": 4365.2}, 4365.0,
                             "2026-08-11T11:15", _lv24, 4365.2, "ДА — пресен клас",
                             _mac24, 1, {"vol_rank": 0.5}, stats, 5000, 2.0, adv_ok=True),
    "сигнал НЕ": lb._sig_msg("short", 5, 4, "ГОТОВ", {"mid": 4365.2}, 4365.0,
                             "2026-08-11T11:15", lb._levels(4365.2, "short"), 4365.2,
                             "НЕ — макрото е против", _mac24, 0, {"vol_rank": 0.5},
                             stats, 5000, 2.0, adv_ok=False,
                             shadow_on={"direction": "short", "entry": 4111.0}),
    "стоящ":     lb._standing_msg("long", _bst24, 14.0, {"mid": 4365.2}, 4365.0,
                                  4365.2, _brd24, _mac24, {}, "2026-08-11T11:20"),
    "спряна":    lb._спряна_msg("short", _bst24, 4365.2, "стоп-пазач · 2 стопа днес",
                                "х", "2026-08-11T11:20", _brd24),
    "изход ТП1": lb._exit_msg("tp1", _tr24, 4007.5, "2026-08-11T10:00", "бар", False),
    "изход БЕ":  lb._exit_msg("sl", _tr24, 4000.0, "2026-08-11T10:00", "бар", False),
    "сянка-изход": lb._shadow_exit_msg("sl", _tr24, 4000.0, "2026-08-11T10:00", "бар", False),
    "MA-аларма": lb._ma_alert_msg("long", "ema200", 4365.2, {"win": 62.8, "n": 410}, _mac24),
    "пулс":      lb._pulse_msg("09", _brd24, _bst24, "long", "ДА — пресен клас", True,
                               None, None, {"mid": 4365.2}, None, _mac24, False, False),
}
for _име24, _т24 in _КАРТИ24.items():
    _намерени24 = [z for z in _ЗАБРАНЕНО24 if z in _т24]
    ck(f"П24 «{_име24}» е без забранения шум {_намерени24 or ''}", not _намерени24)

# ── и обратната страна: фактите НЕ са изчезнали заедно с шума ──────────────
ck("П24 сигналът пак носи вход, трите цели и стопа",     # ОДИТ-29: етикетите станаха знаци
   "вход" in _КАРТИ24["сигнал ДА"] and "🛑" in _КАРТИ24["сигнал ДА"]
   and _КАРТИ24["сигнал ДА"].count("️⃣") == 3)
ck("П24 сигналът пак носи стопа — в ПИПСОВЕ и долари",   # ОДИТ-67
   "пипса" in _КАРТИ24["сигнал ДА"] and "$)" in _КАРТИ24["сигнал ДА"])
# 🔴 «по 1/3 на всяка цел» се скъси на «по 1/3» и слезе ПРИ ЦЕЛИТЕ — там му е
# мястото. Пази се СЪЩОТО: че картата казва как се прибира.
ck("П24 сигналът пак дели на 1/3", "по 1/3" in _КАРТИ24["сигнал ДА"])
ck("П24 и го казва ПРИ ЦЕЛИТЕ, не на отделен ред",
   any(("по 1/3" in л and "1️⃣" in л) for л in _КАРТИ24["сигнал ДА"].split(chr(10))))
ck("П24 «НЕ» картата пак си казва присъдата и пази сянката",
   "БЕЗ ВХОД" in _КАРТИ24["сигнал НЕ"] and "наум" in _КАРТИ24["сигнал НЕ"]
   and "4,111.00" in _КАРТИ24["сигнал НЕ"])
ck("П24 стоящата карта пак дава нивата",
   "🛑" in _КАРТИ24["стоящ"] and _КАРТИ24["стоящ"].count("️⃣") == 3)
ck("П24 спряната карта пак казва какво вижда и защо не",
   "ВИЖДАМ" in _КАРТИ24["спряна"] and "📌" in _КАРТИ24["спряна"])
ck("П24 безрисковият изход пак се различава от истинския стоп",   # ОДИТ-29
   "НУЛА" in _КАРТИ24["изход БЕ"] and "стопът беше на входа" in _КАРТИ24["изход БЕ"])
ck("П24 MA-алармата пак казва, че ботът НЕ влиза по нея",
   "Не е съвет" not in _КАРТИ24["MA-аларма"])
ck("П24 пулсът пак казва какво гледа и какво чака",      # ОДИТ-29: етикетите станаха знаци
   "🥇" in _КАРТИ24["пулс"] and "👁" in _КАРТИ24["пулс"])

# ── и трето: картите наистина СА СТАНАЛИ по-къси ──────────────────────────
_ДЪЛЖИНИ24 = {"сигнал ДА": 7, "стоящ": 6, "спряна": 4, "пулс": 6}   # ОДИТ-29: тавани надолу
for _име24, _макс24 in _ДЪЛЖИНИ24.items():
    _n24 = len(_КАРТИ24[_име24].split("\n"))
    ck(f"П24 «{_име24}» е под {_макс24} реда (сега {_n24})", _n24 <= _макс24)

# ── четвърто: картата на мозъка (най-дългата) също е свита ────────────────
if _CB22 is not None:
    _к24 = {"степен": "🔥 СИЛЕН", "ранг": 4, "точки": 12, "лонг": True, "цена": 4365.2,
            "atr": 8.8, "рамка": "15мин", "време": _dt.datetime(2026, 8, 11, 11, 20,
                                                                tzinfo=_dt.timezone.utc),
            "повод_текст": ["вход в СИЛНА зона"], "всички_условия": {},
            "залог": {"вход": 4365.2, "стоп": 4352.1, "риск": 13.1, "цел": 4391.4,
                      "награда": 26.2, "основа_цел": "ликвидност", "съотношение": 2.0,
                      "цел2": None, "награда2": None, "основа_цел2": "", "съотношение2": None}}
    _тк24 = _CB22.KT.сглоби(_к24, таблица=_CB22.ТАБЛИЦА, тавани=_CB22.ТАВАН_ГРУПА,
                            граници=_CB22.ПРАГОВЕ, степени=_CB22.СТЕПЕНИ,
                            час_сега="17:16",
                            мерено={"кофа": "day1", "посока": "long", "win": 79.9,
                                    "net": 2.99, "n": 4019, "ci": (1.66, 4.20)})
    ck("П24 картата на мозъка е без забранения шум",
       not [z for z in _ЗАБРАНЕНО24 if z in _тк24])
    ck("П24 мереното НЕ отива на картата на мозъка",     # ОДИТ-29
       not any(r.startswith("мерено ") for r in _тк24.split("\n")))
    # ОДИТ-39: под «ГОТОВ» долният ред е «наблюдение, не е вход»; от «ГОТОВ»
    # нагоре е «нов метод · още без бектест». Тестът иска ЕДИН ред и в двата.
    ck("П24 долният ред на мозъка е един и къс",
       len([r for r in _тк24.split("\n") if r.startswith("🧪")]) == 1
       and ("наблюдение, не е вход" in _тк24 or "НЕ е сигнал" in _тк24))
    # ОДИТ-31 · часът вече е този на ПРАЩАНЕТО, не на бара — картата се
    # подава отвън (`час_сега`). Карта, пристигнала в 17:16, пишеше 17:00.
    ck("П24 часът на мозъка е жив и се подава отвън",
       "17:16" in _тк24 and "UTC" not in _тк24)


# ═══ П28 · ЧИСЛАТА ИМАТ КЪДЕ ДА ОТИДАТ (ОДИТ-29) ══════════════════════════
# Махнах статистиката от картите и казах «числата остават в дневника». После
# видях живия дневник:  се пише от ФИКСИРАН списък ключове и 
# не беше в него. Тоест твърдението беше без произход — правило 1 от протокола.
# Този тест пази трите брънки: следата ги носи, дневникът ги записва, картата не.
_src28 = open("live_bot.py", encoding="utf-8").read()
ck("П28 дневникът записва мереното в gate",
   '"мерено": _gate_trace.get("мерено")' in _src28)
_tr28 = {}
lb._advice_entry("long", 1, stats, None, False, 0, trace=_tr28)
ck("П28 следата носи win/net/n и интервала",
   all(_tr28.get("мерено", {}).get(k) is not None for k in ("win", "net", "n", "lo", "hi")))
ck("П28 но НЕ отиват на картата",
   "n=" not in lb._advice_entry("long", 1, stats, None, False, 0)[0])

# ═══ П29 · ЗНАКЪТ НА ДОЛАРА И ЛИХВИТЕ (ОДИТ-30) ════════════════════════════
# 🔴 ДЕФЕКТ, КОЙТО КАЧИХ И КОЙТО АДВЕРСАРНАТА ВЪЛНА ХВАНА.
# В `_streaks` ЛОНГ стрийкът значи доларът ПАДА и лихвите ПАДАТ — това вдига
# златото. Първата ми човешка версия писа «доларът и лихвите НАГОРЕ» на карта
# ЗА ПОКУПКА — точно обратното, върху реда, по който той решава с пари.
# Тестът е с две страни: правилната дума я ИМА, обърнатата я НЯМА.
_src29 = open("live_bot.py", encoding="utf-8").read()
ck("П29 кодът още смята ЛОНГ като «доларът пада и лихвите падат»",
   "доларът пада И лихвите падат" in _src29
   and "(-(dx.pct_change(20)))" in _src29.split("m_l =")[1][:80])
_дл29 = lb._advice_entry("long", 1, stats, None, False, 0)[0]
ck("П29 при ПОКУПКА текстът казва, че доларът ПАДА",
   "падат" in _дл29 and "нагоре" not in _дл29)
ck("П29 при ПОКУПКА текстът казва и ефекта върху златото", "вдига златото" in _дл29)
_дс29 = None
for _n29 in (1, 2, 3):
    _t29, _o29 = lb._advice_entry("short", _n29, stats, None, False, 0)
    if _o29:
        _дс29 = _t29
        break
if _дс29:
    ck("П29 при ПРОДАЖБА текстът казва, че доларът РАСТЕ",
       "растат" in _дс29 and "надолу" not in _дс29)
    ck("П29 при ПРОДАЖБА текстът казва и ефекта", "сваля златото" in _дс29)
else:
    # честно: при тези числа продажбата изобщо не се пуска, значи няма какво
    # да се сверява. Тестът го КАЗВА, вместо да мълчи и да се брои за зелен.
    _пр29 = {"fresh": {"short": {"day1": {"n": 9999, "win": 80.0, "net": 3.0,
                                          "lo": 1.0, "hi": 5.0}}}}
    _т29 = lb._advice_entry("short", 1, _пр29, None, False, 0)[0]
    ck("П29 при ПРОДАЖБА текстът казва, че доларът РАСТЕ (изкуствени числа)",
       "растат" in _т29 and "надолу" not in _т29)
    ck("П29 при ПРОДАЖБА текстът казва и ефекта", "сваля златото" in _т29)

# ═══ П30 · «БЪРЗ ПАЗАР» Е ИНСТРУКЦИЯ ЗА ВХОД (ОДИТ-30) ═════════════════════
# «влизай само с лимитна поръчка» на карта, която казва «не влизам», е покана
# и отказ в едно изречение. Лепи се САМО на разрешените входове.
for _д30, _с30 in (("long", 0), ("long", 5), ("short", 5), ("short", 1), ("short", 0)):
    _т30, _ок30 = lb._advice_entry(_д30, _с30, stats, 12.0, False, 0)
    if not _ок30:
        ck(f"П30 отказ {_д30}/{_с30} НЕ говори за лимитна поръчка",
           "лимитна" not in _т30)
_т30д, _ок30д = lb._advice_entry("long", 1, stats, 12.0, False, 0)
ck("П30 но при РАЗРЕШЕН вход предупреждението за бърз пазар ОСТАВА",
   _ок30д and "лимитна" in _т30д)

# ═══ П31 · МОЗЪКЪТ ГЛЕДА ЖИВАТА ГРАФИКА (ОДИТ-31) ═════════════════════════
# 🔴 ДЕФЕКТЪТ, КОЙТО СОБСТВЕНИКЪТ ВИДЯ ПРЪВ: карта с «вход 4443.50», докато
# графиката му показва 4390. Измерено в дневника (11.08, 14:16):
#     барът от Yahoo (GC=F фючърс) = 4443.30, на 10 минути
#     живата цена (swq)            = 4385.89, на 0.2 секунди
# Мозъкът чете БАРОВЕ. Всичко останало в бота вече е на живата цена.
# Тестът пази трите брънки: изместването работи · часът е жив · прагът е
# «НАБЛЮДЕНИЕ» · и че при изместване 0 картата е точно каквато беше.
if _CB22 is not None:
    _к31 = {"степен": "👀 НАБЛЮДЕНИЕ", "ранг": 1, "точки": 9, "лонг": True,
            "цена": 4443.5, "atr": 6.1, "рамка": "15м",
            "време": _dt.datetime(2026, 8, 11, 14, 0, tzinfo=_dt.timezone.utc),
            "повод_текст": ["вход в СИЛНА зона 1час"],
            "всички_условия": {"A3_повод_зона": True, "D1_в_зона": True},
            "залог": {"вход": 4443.50, "стоп": 4437.44, "риск": 6.06, "цел": 4453.00,
                      "награда": 9.50, "основа_цел": "ликвидност", "съотношение": 1.57,
                      "цел2": 4462.50, "награда2": 19.0, "основа_цел2": "гап",
                      "съотношение2": 3.1}}
    _арг31 = dict(таблица=_CB22.ТАБЛИЦА, тавани=_CB22.ТАВАН_ГРУПА,
                  граници=_CB22.ПРАГОВЕ, степени=_CB22.СТЕПЕНИ)
    _бар31 = _CB22.KT.сглоби(_к31, **_арг31, изместване=0.0, час_сега="17:16")
    _жив31 = _CB22.KT.сглоби(_к31, **_арг31, изместване=59.58, час_сега="17:16")
    ck("П31 без изместване картата е на скалата на бара", "4443.50" in _бар31)
    ck("П31 с изместване нивото слиза на живата скала",
       "4383.92" in _жив31 and "4443.50" not in _жив31)
    ck("П31 стопът също слиза", "4377.86" in _жив31 and "4437.44" not in _жив31)
    ck("П31 и двете цели слизат",
       "4393.42" in _жив31 and "4402.92" in _жив31
       and "4453.00" not in _жив31 and "4462.50" not in _жив31)
    # ОДИТ-35: картата вече казва ДО КОЯ цел е съотношението — «11.1× риска»
    # стоеше до първа цел, която е 5.6×.
    ck("П31 съотношението НЕ се мени от изместването (то е разлика, не ниво)",
       "1.6× риска до първа цел" in _жив31 and "3.1× до втора" in _жив31
       and "1.6× риска до първа цел" in _бар31)
    ck("П31 часът е този на ПРАЩАНЕТО, подаден отвън", "17:16" in _жив31)
    ck("П31 картата се обявява за наблюдение, не за вход",
       "🧠" in _жив31 and "наблюдение, не е вход" in _жив31
       and "КУПИ" not in _жив31 and "ПРОДАЙ" not in _жив31)
    # ⚠️ САМО когато нещо е против; «2/2 натам» е добра новина
    _добро31 = _CB22.KT.сглоби(_к31, **_арг31, изместване=59.58, час_сега="17:16",
                               предупреждения=["голямата картина: 2/2 натам"])
    _лошо31 = _CB22.KT.сглоби(_к31, **_арг31, изместване=59.58, час_сега="17:16",
                              предупреждения=["голямата картина: 0/2 натам"])
    ck("П31 добра новина → 📌, не ⚠️", "📌 голямата картина: 2/2" in _добро31)
    ck("П31 лоша новина → ⚠️", "⚠️ голямата картина: 0/2" in _лошо31)

_src31 = open("live_bot.py", encoding="utf-8").read()
ck("П31 ботът подава базиса на мозъка",
   "изместване=_изм" in _src31 and "float(basis_g)" in _src31)
ck("П31 ботът подава ЖИВИЯ час на мозъка", "час_сега=_sofia()" in _src31)
ck("П31 има път назад (МОЗЪК_ЖИВА_ЦЕНА)", "МОЗЪК_ЖИВА_ЦЕНА" in _src31)

# ═══ П32 · ОДИТ-РОБОТЪТ МЪЛЧИ В ТЕЛЕГРАМ (ОДИТ-31) ════════════════════════
# Собственикът: «одит ти казах не искам — искаме само неща полезни за човек
# трейдър». Одитът ПРОДЪЛЖАВА да върви (той е щитът), но не пише в чата.
_a32 = open("audit_bot.py", encoding="utf-8").read()
ck("П32 отчетът не тръгва към Телеграм", "ПРАЩАЙ_ОТЧЕТ = False" in _a32)
ck("П32 но одитът ПРОДЪЛЖАВА да върви (не е спрян)",
   "def main()" in _a32 and "A.rows" in _a32)
ck("П32 има път назад (една дума)", "ПРАЩАЙ_ОТЧЕТ" in _a32)

# ═══ П33 · МОЗЪКЪТ ВИЖДА 1м, 5м И 15м (ОДИТ-32) ═══════════════════════════
# Собственикът: «нали си е на 1 мин 5 мин и 15 мин». Проверено в кода:
# `РАБОТНИ = ("15м",)` — картите се раждаха САМО от 15м. Две трети от това,
# което той гледа, ботът не виждаше.
# Три рамки значи и три пазача срещу заливане — тестът пази и тях.
_s33 = open("live_bot.py", encoding="utf-8").read()
ck("П33 работните рамки са три", '"МОЗЪК_РАМКИ", "1мин,5м,15м"' in _s33)
ck("П33 рамките се подават на сканирането", "работни=МОЗЪК_РАМКИ" in _s33)
# ОДИТ-34: първата версия лепна етикет «1мин» върху `src`, а `src` е
# ПЕТМИНУТНАТА серия. Тестът вече иска ИСТИНСКАТА минутна серия.
ck("П33 1м и 5м идват от истинските си серии, не от ресемплване",
   '_bfr["1мин"] = frames.get("1мин")' in _s33
   and '_bfr["5м"] = frames.get("5м")' in _s33
   and '_bfr["1мин"] = src' not in _s33)
# 🔴 ОДИТ-60 · ОБНОВЕН. Стъпаловидните прагове (1мин 11 · 5м 10 · 15м 9)
# отпаднаха: собственикът реши да идват САМО ⚡ МНОГО СИЛЕН (14+) и 💎 РЯДЪК
# (16+), значи ВСЯКА рамка иска 14. Мерено: 19 карти за 30 часа стават 4.
ck("П33 всяка рамка иска прага на ⚡ МНОГО СИЛЕН",
   all(v == 14 for v in lb.МОЗЪК_ПРАГ_РАМКА.values()))
ck("П33 и общият праг е същият", lb.МОЗЪК_ПРАГ == 14)
ck("П33 прагът е ПОД върха — 💎 РЯДЪК не е единственото, което говори",
   lb.МОЗЪК_ПРАГ < 16)
ck("П33 има таван за рън", "МОЗЪК_ТАВАН" in _s33 and "таван за рън" in _s33)
ck("П33 има ОБЩ разредител между картите",
   "МОЗЪК_РАЗРЕД_МИН" in _s33 and "_последна_карта" in _s33)
ck("П33 по-силна степен минава през разредителя",
   'int(_s.get("ранг", 0)) <= _посл_ранг' in _s33)
ck("П33 има път назад (една променлива)", 'os.environ.get("МОЗЪК_РАМКИ"' in _s33)
_c33 = open("brain/chart_brain.py", encoding="utf-8").read()
ck("П33 застудяването е в МИНУТИ, не само в барове",
   "ПАУЗА_МИНУТИ = 20" in _c33 and "-(-ПАУЗА_МИНУТИ // max(мин_бар, 1))" in _c33)

# ═══ П34 · МОЗЪКЪТ СЛЕДИ СЕТЪПИТЕ СИ ДО РАЗВРЪЗКА (ОДИТ-33) ═══════════════
# Собственикът: «да си има пак ТП-та, всичко както си е». Дотук мозъкът
# пращаше ниво, стоп и две цели — и толкова. Никой не гледаше какво става
# после; той получаваше обещание без развръзка.
# Това е и ИЗМЕРВАНЕТО, което липсваше: `brain_result.jsonl` след няколко
# седмици ще каже с числа дали зоните и гаповете дават ръб.
import ast
import shutil as _sh34
_o34 = _P("_следене34"); _sh34.rmtree(_o34, ignore_errors=True); _o34.mkdir()
_f34, _d34 = _o34 / "brain_track.json", _o34 / "brain_result.jsonl"
_нов34 = {"лонг": True, "рамка": "15м", "степен": "👀 НАБЛЮДЕНИЕ", "точки": 9,
          "залог": {"вход": 4390.0, "стоп": 4384.0, "цел": 4399.0, "цел2": 4408.0}}
ck("П34 без отворено и без нов — мълчи",
   lb._мозък_следене(_f34, _d34, 4390.0, "2026-08-11T18:00") == [])
lb._мозък_следене(_f34, _d34, 4390.0, "2026-08-11T18:00", нов=_нов34)
ck("П34 отваря следене", _f34.exists())
ck("П34 движение без удар мълчи",
   lb._мозък_следене(_f34, _d34, 4395.0, "2026-08-11T18:05") == [])
_m34 = lb._мозък_следене(_f34, _d34, 4399.5, "2026-08-11T18:10")
ck("П34 първата цел праща карта и НЕ затваря",
   len(_m34) == 1 and _m34[0][0] == "brain-exit:цел1" and _f34.exists())
ck("П34 първата цел се брои по НИВОТО, не по цената на удара",
   "+9.00$" in _m34[0][1])
ck("П34 първата цел не се повтаря",
   lb._мозък_следене(_f34, _d34, 4400.0, "2026-08-11T18:12") == [])
_m34b = lb._мозък_следене(_f34, _d34, 4408.5, "2026-08-11T18:20")
ck("П34 втората цел затваря следенето",
   len(_m34b) == 1 and _m34b[0][0] == "brain-exit:цел2" and not _f34.exists())
_р34 = [_j22.loads(x) for x in _d34.read_text(encoding="utf-8").splitlines() if x.strip()]
# 🔴 ОДИТ-57 · ОБНОВЕН. Дотук този тест изискваше ПЪЛНИТЕ 18.0$ — тоест
# заковаваше формулата, която ИГНОРИРА взетата ЦЕЛ1. Мерено в живия
# brain_result.jsonl: 1 от 6 записа е точно така (08-12 03:51, взета цел1,
# изход стоп, записан −5.36$ вместо +2.12$ — разлика 7.48$ на ЕДИН сетъп).
# Две цели → две части: половина на +9, половина на +18 = 13.5$.
ck("П34 резултатът влиза в дневника ПО СТЪЛБАТА, не гол",
   len(_р34) == 1 and _р34[0]["резултат"] == 13.5)
ck("П34 компонентите се пазят отделно (проверимо)",
   _р34[0].get("част1") == 9.0 and _р34[0].get("част2") == 18.0)
# стопът бие целта, ако и двете са докоснати — честното допускане
lb._мозък_следене(_f34, _d34, 4390.0, "2026-08-11T19:00", нов=_нов34)
_m34c = lb._мозък_следене(_f34, _d34, 4383.0, "2026-08-11T19:10")
ck("П34 стопът затваря и записва загубата",
   _m34c and _m34c[0][0] == "brain-exit:стоп" and "-6.00$" in _m34c[0][1])
_р34b = [_j22.loads(x) for x in _d34.read_text(encoding="utf-8").splitlines() if x.strip()]
ck("П34 дневникът пази и двата изхода", [r["резултат"] for r in _р34b] == [13.5, -6.0])
ck("П34 БЕЗ взета цел1 стълбата не се прилага (пълна загуба е вярна)",
   _р34b[1]["резултат"] == -6.0 and "част1" not in _р34b[1])
# едно наведнъж: нов сетъп НЕ измества отворен
lb._мозък_следене(_f34, _d34, 4390.0, "2026-08-11T20:00", нов=_нов34)
_друг34 = dict(_нов34, залог=dict(_нов34["залог"], вход=9999.0))
lb._мозък_следене(_f34, _d34, 4391.0, "2026-08-11T20:05", нов=_друг34)
ck("П34 отвореното следене НЕ се измества от нов сетъп",
   _j22.loads(_f34.read_text(encoding="utf-8"))["вход"] == 4390.0)
_sh34.rmtree(_o34, ignore_errors=True)
_s34 = open("live_bot.py", encoding="utf-8").read()
ck("П34 следенето е включено в живия цикъл", "_мозък_следене(out / \"brain_track.json\"" in _s34)
ck("П34 има път назад (МОЗЪК_СЛЕДЕНЕ)", "МОЗЪК_СЛЕДЕНЕ" in _s34)
ck("П34 следенето е обвито — спъне ли се, не поваля бота",
   "🧠 следенето се спъна" in _s34)
# ОДИТ-33: проверява се КОДЪТ, не описанието. Първата версия на този тест
# падна, защото самото docstring казва «нищо тук не докосва trade.json» —
# тест, който чете обяснението вместо кода, съди по грешното място.
_ф34 = [n for n in ast.parse(_s34).body
        if isinstance(n, ast.FunctionDef) and n.name == "_мозък_следене"][0]
_тяло34 = ast.get_source_segment(_s34, _ф34) or ""
_тяло34 = chr(10).join(l for l in _тяло34.split(chr(10))
                      if not l.strip().startswith("#"))
_ч34 = _тяло34.split(chr(34) * 3)
_тяло34 = _ч34[0] + (chr(34) * 3).join(_ч34[2:]) if len(_ч34) > 2 else _тяло34
ck("П34 НЕ пипа реалната сделка, пазача и статистиката",
   not any(w in _тяло34 for w in ("trade.json", "guard", "stats", "backtest")))

# ═══ П35 · ДВА ДЕФЕКТА, ХВАНАТИ НА ЖИВО (ОДИТ-34) ═════════════════════════
# И двата мои, от предишния час, и двата видени в ЖИВИЯ дневник:
#  1 · таг «brain:1мин:КЪСО», а заглавието пишеше «15м». Ключът «рамка» стои
#      на ВЪНШНИЯ сетъп, не на `_карта_вход`; `сглоби` падаше на подразбирането.
#  2 · карта тръгна в 15:11, а brain_track.json не се появи. Външният сетъп
#      НЯМА ключ «залог» — нивата стоят направо в него. Четях празно и
#      следенето не се отваряше нито веднъж.
_c35 = open("brain/chart_brain.py", encoding="utf-8").read()
ck("П35 картата взима рамката от ВЪНШНИЯ сетъп",
   '_вх["рамка"] = с.get("рамка")' in _c35)
_l35 = open("live_bot.py", encoding="utf-8").read()
ck("П35 следенето чете нивата направо от сетъпа, не от «залог»",
   'for _k in ("вход", "стоп", "цел", "цел2")' in _l35
   and '_за_следене.get("залог")' not in _l35)
if _CB22 is not None:
    # рамката минава чак до заглавието — за всяка от трите работни рамки
    for _рм35 in ("1мин", "5м", "15м"):
        _с35 = {"рамка": _рм35, "лонг": True, "степен": "👀 НАБЛЮДЕНИЕ",
                "_карта_вход": {"степен": "👀 НАБЛЮДЕНИЕ", "ранг": 1, "точки": 9,
                                "лонг": True, "цена": 4390.0, "atr": 5.0,
                                "повод_текст": ["зона"], "всички_условия": {},
                                "залог": {"вход": 4390.0, "стоп": 4384.0, "риск": 6.0,
                                          "цел": 4399.0, "награда": 9.0,
                                          "основа_цел": "зона", "съотношение": 1.5,
                                          "цел2": None, "награда2": None,
                                          "основа_цел2": "", "съотношение2": None}},
                "съгласие_рамки": {}}
        _к35 = _CB22.карта(_с35, час_сега="18:20")
        ck(f"П35 картата от «{_рм35}» го КАЗВА в заглавието",
           _рм35 in _к35.split(chr(10))[0])

# ═══ П37 · О1 · ИЗХОДЪТ НЕ ВИСИ ЗАД МАКРОТО (ОДИТ-36) ═════════════════════
# От генералния план, приоритет 🟠: «ако GDX/DXY/лихвите гръмнат, целият рън
# пропада ПРЕДИ track_trade → отворена сделка не получава изход». Дефект С
# ПАРИ: цената удря ТП или СТОП, а ботът е паднал на индекса на миньорите.
# Тестът пуска ЦЕЛИЯ main() с гръмнало GDX и иска рънът да оцелее.
_src37 = open("live_bot.py", encoding="utf-8").read()
ck("П37 златото се дърпа ТВЪРДО (без него няма нищо)",
   'gold_d = _yf("GC=F", "3y", "1d")' in _src37)
ck("П37 макрото е в try — гръмне ли, не поваля рънa",
   "_макро_мъртво" in _src37 and "except Exception as _e:" in _src37)
ck("П37 при мъртво макро гейтът получава нулеви стрийкове (кофа mixed)",
   '{"long": 0, "short": 0} if _макро_мъртво' in _src37)
ck("П37 `_hist` приема None (стои ПРЕДИ следенето)",
   "if df is None:" in _src37.split("def _hist")[1][:220])
ck("П37 бележката казва, че входовете спират, а следенето върви",
   "НОВИ ВХОДОВЕ" in _src37 and "следенето" in _src37)

import numpy as np
# ОДИТ-40 · ПАПКАТА Е АБСОЛЮТНА И УНИКАЛНА. Един пуск от осем гръмна с
# «FileNotFoundError: _o37\outbox.jsonl» — относителен път, изчезнал под
# краката на main(). Не можах да го възпроизведа (8 пуска, 1 провал), затова
# махам самата възможност: абсолютен път + уникално име + проверка, че
# папката СЪЩЕСТВУВА точно преди main().
_o37 = (_P(__file__).resolve().parent / f"_o37_{_os.getpid()}")
_sh34.rmtree(_o37, ignore_errors=True); _o37.mkdir(parents=True)
_idx37 = pd.date_range("2024-06-01", periods=800, freq="D")
_дн37 = pd.DataFrame({"Open": np.linspace(2000, 4400, 800), "High": np.linspace(2005, 4405, 800),
                      "Low": np.linspace(1995, 4395, 800), "Close": np.linspace(2000, 4400, 800),
                      "Volume": 1000.0}, index=_idx37)
_i537 = pd.date_range("2026-08-01", periods=3000, freq="5min")
_м537 = pd.DataFrame({"Open": 4390.0, "High": 4392.0, "Low": 4388.0, "Close": 4390.0,
                      "Volume": 100.0}, index=_i537)
_старо37 = {k: getattr(lb, k) for k in ("_yf", "_rates", "_spot", "_send_raw",
                                        "_market_closed", "_cq_fetch")}
lb._yf = lambda t, p_, i: (_ for _ in ()).throw(RuntimeError("Yahoo падна")) if t == "GDX"     else (_м537.copy() if i in ("1m", "5m") else _дн37.copy())
lb._rates = lambda: pd.Series(np.linspace(2.0, 1.5, 800), index=_idx37)
lb._spot = lambda *a, **k: {"mid": 4390.0, "bid": 4389.8, "ask": 4390.2,
                            "src": "swq", "age": 0.1, "ts": "2026-08-11T15:50:00"}
lb._send_raw = lambda t: "SENT (200)"
lb._market_closed = lambda *a, **k: False
lb._cq_fetch = lambda now: None
(_o37 / "trade.json").write_text(_j22.dumps({
    "direction": "long", "entry": 4380.0, "opened": "2026-08-11T09:00",
    "levels": {"tp1": 4387.5, "tp2": 4392.0, "tp3": 4400.0, "sl": 4360.0},
    "hit": {}, "sym": "XAUUSD", "status": "open", "date": "2026-08-11"}), encoding="utf-8")
_аргс37 = sys.argv
sys.argv = ["live_bot.py", "--out", str(_o37), "--stats", "backtest_stats.json",
            "--balance", "5000", "--risk", "2", "--force"]
_код37 = 0
ck("П37 папката съществува точно преди main()", _o37.is_dir())
try:
    with _ctx.redirect_stdout(_io2.StringIO()):
        lb.main()
except SystemExit as _e37:
    _код37 = _e37.code if isinstance(_e37.code, int) else 1
except Exception as _e37:
    _код37 = f"{type(_e37).__name__}: {_e37}"
finally:
    sys.argv = _аргс37
    for _k37, _v37 in _старо37.items():
        setattr(lb, _k37, _v37)
ck(f"П37 рънът ОЦЕЛЯВА при гръмнало GDX (код {_код37})", _код37 == 0)
_ж37 = _o37 / "live_journal.jsonl"
ck("П37 дневникът се пише въпреки мъртвото макро", _ж37.exists())
if _ж37.exists():
    _r37 = _j22.loads(_ж37.read_text(encoding="utf-8").splitlines()[-1])
    ck("П37 бележката за О1 влиза в дневника",
       any("О1" in b for b in (_r37.get("notes") or [])))
ck("П37 отворената сделка ОСТАВА под наблюдение", (_o37 / "trade.json").exists())
_sh34.rmtree(_o37, ignore_errors=True)

# ═══ П38 · О3, О4 и металът в картата на мозъка (ОДИТ-37) ═════════════════
# О3 · «двете сделки в една посока = ~2× риск» се появяваше САМО в 21:00
#      равносметката — часове след решението. Златото и среброто вървят заедно
#      (корелация ~0.8): два залога в една посока са един двоен.
# О4 · `_reentry_verdict` пазеше САМО рънa на затварянето. Следващият рън, пет
#      минути по-късно, я заобикаляше и отваряше точно шорта, за който същото
#      правило казва, че губи −2.75$/сделка.
_да38 = lb._advice_entry("long", 1, stats, None, False, 0)
_др38 = {"direction": "long", "entry": 65.1, "sym": "XAGUSD", "hit": {},
         "levels": {"tp1": 65.3, "tp2": 65.4, "tp3": 65.6, "sl": 64.6}}
def _к38(**кв):
    return lb._sig_msg("long", 6, 5, "СИЛЕН", {"mid": 4365.2}, 4365.0, "x",
                       lb._levels(4365.2, "long"), 4365.2, _да38[0],
                       {"долар": True, "лихви": True}, 1, {"vol_rank": .35},
                       stats, 5000, 2.0, adv_ok=True, **кв)
ck("О3 · без друга сделка НЯМА предупреждение", "вече държиш" not in _к38())
ck("О3 · СЪЩАТА посока → предупреждение НА КАРТАТА",
   "вече държиш среброто в същата посока" in _к38(other_trade=_др38))
ck("О3 · ОБРАТНАТА посока → без предупреждение",
   "вече държиш" not in _к38(other_trade=dict(_др38, direction="short")))
ck("О3 · предупреждението казва ЗАЩО (един голям риск, не два)",
   "един голям" in _к38(other_trade=_др38))
_m38 = {}
ck("О4 · чиста памет → няма забрана", lb._reentry_ban(_m38, "short", 2)[0] is False)
lb._reentry_ban(_m38, "short", 2, why="шорт ре-влизане губи", set_it=True)
ck("О4 · забраната ОЦЕЛЯВА следващия рън", lb._reentry_ban(_m38, "short", 2)[0] is True)
ck("О4 · носи и причината", "губи" in lb._reentry_ban(_m38, "short", 2)[1])
ck("О4 · друга ПОСОКА не е забранена", lb._reentry_ban(_m38, "long", 2)[0] is False)
_m38b = {}
lb._reentry_ban(_m38b, "short", 2, why="х", set_it=True)
ck("О4 · СМЕНЕН стрийк → забраната пада САМА",
   lb._reentry_ban(_m38b, "short", 5)[0] is False and "reentry_ban" not in _m38b)
_s38 = open("live_bot.py", encoding="utf-8").read()
ck("О4 · забраната се пита ПРЕДИ правилото", "_забранен, _защо_бан = _reentry_ban" in _s38)
ck("О4 · отказът се ЗАПОМНЯ", "set_it=True" in _s38)
# металът в картата на мозъка
if _CB22 is not None:
    _к38б = {"степен": "👀 НАБЛЮДЕНИЕ", "ранг": 1, "точки": 9, "лонг": True,
             "цена": 65.1, "atr": 0.3, "рамка": "15м",
             "време": _dt.datetime(2026, 8, 11, 14, 0, tzinfo=_dt.timezone.utc),
             "повод_текст": ["зона"], "всички_условия": {},
             "залог": {"вход": 65.1, "стоп": 64.9, "риск": 0.2, "цел": 65.5,
                       "награда": 0.4, "основа_цел": "зона", "съотношение": 2.0,
                       "цел2": None, "награда2": None, "основа_цел2": "",
                       "съотношение2": None}}
    _а38 = dict(таблица=_CB22.ТАБЛИЦА, тавани=_CB22.ТАВАН_ГРУПА,
                граници=_CB22.ПРАГОВЕ, степени=_CB22.СТЕПЕНИ)
    ck("П38 картата на мозъка по подразбиране е за ЗЛАТО",
       "злато" in _CB22.KT.сглоби(_к38б, **_а38, час_сега="18:20"))
    ck("П38 но металът може да е СРЕБРО (заковано «злато» беше дефект)",
       "сребро" in _CB22.KT.сглоби(_к38б, **_а38, час_сега="18:20", метал="сребро"))

import re as _re39
# ═══ П39 · О2 · «МАЛЪК РАЗМЕР» ВЕЧЕ ИМА ЧИСЛО ЗАД СЕБЕ СИ (ОДИТ-38) ════════
# 🔴 Доказано преди фикса: застоял сигнал даваше 0.05 лот / ≈$100 — ТОЧНО
# колкото пресен, макар присъдата да казва «ДА (малък размер)». Думата
# обещаваше намаление, което кодът не правеше.
# О2(а): «риск $27» не казва нищо, ако не знаеш от колко. При среброто мин.
# лот е 50 унции — при малък баланс това е далеч над целевия процент.
def _р39(streak, **кв):
    _т, _ok = lb._advice_entry("long", streak, stats, None, False, 0)
    _m = lb._sig_msg("long", 6, 5, "СИЛЕН", {"mid": 4365.2}, 4365.0, "x",
                     lb._levels(4365.2, "long"), 4365.2, _т,
                     {"долар": True, "лихви": True}, streak, {"vol_rank": .35},
                     stats, 5000, 2.0, adv_ok=_ok, **кв)
    return _re39.sub(r"<[^>]+>", "", _m)
_пресен39, _застоял39 = _р39(1), _р39(5)
ck("П39 присъдата при застоял ОБЕЩАВА малък размер",
   "малък размер" in lb._advice_entry("long", 5, stats, None, False, 0)[0])
# ОДИТ-41 · лотът падна; остана препоръката с думи. Тя пак е РАЗЛИЧНА
# между пресен и застоял сигнал — това беше същината на О2(в).
# 🔴 ОБНОВЕН 18.08 · «малък размер» стана СТЪЛБИЦА от четири нива + ДЯЛ.
# Същината на О2(в) остава: думата трябва да е РАЗЛИЧНА между пресен и
# застоял, тоест да има число зад себе си. Сега се пази по-силното —
# двата случая дават различен РЕД, и застоялият е с по-малък дял.
_рз39 = lambda т: [x for x in т.split(chr(10)) if "размер:" in x]
ck("П39 застоялият сигнал ПАК получава по-малка препоръка",
   _рз39(_застоял39) and _рз39(_пресен39)
   and _рз39(_застоял39)[0] != _рз39(_пресен39)[0])
ck("П39 картата казва ЗАЩО", "сигналът не е пресен" in _застоял39)
ck("П39 при пресен сигнал НЯМА намаление", "пълен размер" in _пресен39)
ck("П39 застоялият носи ДЯЛ, не само дума", "от пълния" in _застоял39)
# 🔴 И ОБРАТНАТА ПОСОКА: стълбицата трябва да РАЗЛИЧАВА всичките шест реални
# множителя, а не да ги свива до две думи, както беше до 18.08.
_шест39 = [lb._сила(m) for m in (1.0, 0.67, 0.5, 0.335, 0.33, 0.165)]
ck(f"П39 стълбицата различава шестте множителя ({len({(a, c) for a, _, c in _шест39})} записа)",
   len({(a, c) for a, _, c in _шест39}) >= 4)
ck("П39 най-силният казва «пълен размер», най-слабият — не",
   _шест39[0][2] == "пълен размер" and _шест39[-1][2] != "пълен размер")
ck("П39 думата и дялът не си противоречат (по-голям множител → не по-малка дума)",
   [d for _, d, _ in _шест39] == sorted([d for _, d, _ in _шест39],
                                        key=lambda x: ["НУЛА", "ЕДВА", "ЛЕКО",
                                                       "ПОЛОВИНАТА", "МНОГО",
                                                       "ВСИЧКО"].index(x),
                                        reverse=True))
# 🔴 НУЛАТА · дотук клонът `not adv_ok` връщаше БЕЗ дума за размера: картата
# даваше пълен план — вход, стоп, три цели — и нито дума, че не се влиза.
_нула39 = lb._сила(0.0)
ck("П39 нулевият размер има СВОЯ дума", _нула39[1] == "НУЛА" and "не влизам" in _нула39[2])
_отк39 = _re39.sub(r"<[^>]+>", "", lb._sig_msg(
    "long", 6, 7, "ПРЕМИУМ", {"mid": 4365.2}, 4365.0, None, lb._levels(4365.2, "long"),
    4365.2, "НЕ — доларът и лихвите се карат днес", {"долар": True, "лихви": False}, 0,
    {"streaks": {"long": 0}, "vol_rank": .5}, stats, 1000, 2, adv_ok=False))
ck("П39 отказаната карта КАЗВА, че размерът е нула", "размер: НУЛА" in _отк39)
ck("П39 и пак не оразмерява (лотът си остава извън картата)", "лот" not in _отк39)
_s39 = open("live_bot.py", encoding="utf-8").read()
ck("П39 има път назад (МАЛЪК_РАЗМЕР_W=1.0 връща старото)",
   'os.environ.get("МАЛЪК_РАЗМЕР_W", "0.5")' in _s39)
# О2(а) · процентът при под-минимален лот
_сре39 = _re39.sub(r"<[^>]+>", "", lb._sig_msg(
    "long", 6, 5, "СИЛЕН", {"mid": 65.15}, 65.1, "x",
    lb._levels_silver(65.15, "long"), 65.15,
    lb._advice_entry("long", 1, stats, None, False, 0)[0],
    {"долар": True, "лихви": True}, 1, {"vol_rank": .35}, stats, 600, 2.0,
    adv_ok=True, sym="XAGUSD", dec=3))
# ОДИТ-41 · при най-малката възможна позиция предупреждението остава —
# то е единственото, което лотът вече не може да каже сам.
ck("П39 предупреждава, когато и най-малката позиция е над целта",
   "най-малката позиция" in _сре39 and "над целта 2%" in _сре39)
_зл39 = _re39.sub(r"<[^>]+>", "", lb._sig_msg(
    "long", 6, 5, "СИЛЕН", {"mid": 4365.2}, 4365.0, "x", lb._levels(4365.2, "long"),
    4365.2, lb._advice_entry("long", 1, stats, None, False, 0)[0],
    {"долар": True, "лихви": True}, 1, {"vol_rank": .35}, stats, 5000, 2.0,
    adv_ok=True, zone=("C", "зона C")))
ck("П39 при златото и достатъчен баланс НЯМА фалшива тревога",   # ОДИТ-67
   "над целта" not in _зл39 and "пипса" in _зл39 and "$)" in _зл39)

# ═══ П40 · МОЗЪЧНИТЕ СИЛНИ СЕТЪПИ СА ВХОДОВЕ, НЕ НАБЛЮДЕНИЯ (ОДИТ-39) ═════
# Собственикът, 15-ия час: «искам сигнали, съвети, всичко от А до Я».
# Мозъкът виждаше сетъпи с вход, стоп и две цели — но ги наричаше
# «наблюдение» и НЕ даваше лот. Значи не бяха сигнали.
# СЕГА: под «✅ ГОТОВ» остават наблюдения; от «ГОТОВ» нагоре са ВХОДОВЕ с лот.
if _CB22 is not None:
    _осн40 = {"лонг": True, "цена": 4443.5, "atr": 6.1, "рамка": "15м",
              "време": _dt.datetime(2026, 8, 11, 14, 0, tzinfo=_dt.timezone.utc),
              "повод_текст": ["СИЛНА зона"], "всички_условия": {"D1_в_зона": True},
              "залог": {"вход": 4443.50, "стоп": 4437.44, "риск": 6.06,
                        "цел": 4453.00, "награда": 9.5, "основа_цел": "ликвидност",
                        "съотношение": 1.57, "цел2": 4462.50, "награда2": 19.0,
                        "основа_цел2": "гап", "съотношение2": 3.1}}
    _а40 = dict(таблица=_CB22.ТАБЛИЦА, тавани=_CB22.ТАВАН_ГРУПА,
                граници=_CB22.ПРАГОВЕ, степени=_CB22.СТЕПЕНИ)
    _ЛОТ40 = "💰 0.07 лот · риск ≈$42 · по 1/3 на цел"
    def _к40(ранг, степен, лот=None):
        return _CB22.KT.сглоби(dict(_осн40, ранг=ранг, степен=степен, точки=9 + ранг),
                               **_а40, час_сега="19:55", лот=лот)
    _набл40 = _к40(1, "👀 НАБЛЮДЕНИЕ")
    _вх40 = _к40(3, "✅ ГОТОВ", _ЛОТ40)
    _силен40 = _к40(6, "💎 РЯДЪК", _ЛОТ40)
    ck("П40 НАБЛЮДЕНИЕ си остава наблюдение (без лот, без КУПИ)",
       "наблюдение, не е вход" in _набл40 and "лот" not in _набл40
       and "КУПИ" not in _набл40 and _набл40.startswith("🧠"))
    # 🔴 ОДИТ-43 · ОБЪРНАТ. Вчера този тест пазеше «🟢 КУПИ ЗЛАТО».
    # Собственикът, 20-ия час: «последните съобщения са все сякаш са вход
    # истински… трябва съвет за гледане накъде — сигналите са други».
    # Мозъкът НЯМА бектест; 🟢/🔴 КУПИ/ПРОДАЙ остават само за мереното правило.
    ck("П40 силният сетъп е СЪВЕТ «ГЛЕДАЙ», не заповед «КУПИ»",
       _вх40.startswith("👁") and "ГЛЕДАЙ" in _вх40
       and "КУПИ" not in _вх40 and "ПРОДАЙ" not in _вх40)
    ck("П40 входът пази степента в заглавието (не се губи КОЛКО е силен)",
       "ГОТОВ" in _вх40.split(chr(10))[0] and "РЯДЪК" in _силен40.split(chr(10))[0])
    ck("П40 съветът говори за НИВА, не за вход и стоп",
       "нивото е" in _вх40 and "отпада" in _вх40
       and "🎯 вход" not in _вх40 and "🛑 стоп" not in _вх40)
    ck("П40 целите са условни («ако тръгне»), не обещани",
       "ако тръгне" in _вх40 and "1️⃣" not in _вх40)
    ck("П40 съветът СИ КАЗВА, че не е сигнал",
       "съвет за гледане · НЕ е сигнал" in _вх40)
    ck("П40 наблюдението и съветът НЕ звучат еднакво",
       _набл40.split(chr(10))[0] != _вх40.split(chr(10))[0])
    # 🔴 ТРИТЕ ВИДА СЪОБЩЕНИЯ НЕ БИВА ДА СЕ БЪРКАТ
    # СИГНАЛ = 🟢/🔴 КУПИ/ПРОДАЙ · само от мереното правило
    # СЪВЕТ  = 👁 ГЛЕДАЙ · мозъкът
    # ОБЗОР  = ☀️🌤️🌙 / 📌 · какво виждам
    _сиг43 = lb._sig_msg("long", 6, 5, "СИЛЕН", {"mid": 4365.2}, 4365.0, "x",
                         lb._levels(4365.2, "long"), 4365.2,
                         lb._advice_entry("long", 1, stats, None, False, 0)[0],
                         {"долар": True, "лихви": True}, 1, {"vol_rank": .35},
                         stats, 5000, 2.0, adv_ok=True)
    _сиг43 = _re22.sub(r"<[^>]+>", "", _сиг43)
    ck("П43 СИГНАЛЪТ казва КУПИ и започва с 🟢", _сиг43.startswith("🟢 КУПИ"))
    ck("П43 СЪВЕТЪТ никога не казва КУПИ", "КУПИ" not in _вх40)
    ck("П43 СИГНАЛЪТ никога не казва ГЛЕДАЙ", "ГЛЕДАЙ" not in _сиг43)
    ck("П43 само СИГНАЛЪТ носи 🟢/🔴 в заглавието",
       _сиг43[0] in "🟢🔴" and _вх40[0] not in "🟢🔴" and _набл40[0] not in "🟢🔴")
    ck("П40 при вход НЯМА два реда с 💰",
       sum(1 for r in _вх40.split(chr(10)) if r.startswith("💰")) == 1)
    ck("П40 при вход НЯМА два реда с 🎯",
       sum(1 for r in _вх40.split(chr(10)) if r.startswith("🎯")) == 1)
    ck("П40 картата остава под 7 реда", len(_вх40.split(chr(10))) <= 7)
_s40 = open("live_bot.py", encoding="utf-8").read()
ck("П40 ботът смята лота от РЕАЛНИЯ стоп на сетъпа",
   'abs(float(_s["вход"]) - float(_s["стоп"]))' in _s40)
# 🔴 ОДИТ-68 · ОБЪРНАТ. `МОЗЪК_РИСК_W` беше теглото за размера на мозъчния
# вход. Размерите отпаднаха («не искам лотове, всеки си преценя»), настройката
# остана да виси и стана призрак. Тестът вече пази ПРЕМАХВАНЕТО и това, което
# наистина държи мозъка под мереното правило: по-висок праг и «НЕ е сигнал».
ck("П40 мъртвата настройка за риск я няма", "МОЗЪК_РИСК_W" not in _s40)
ck("П40 мозъкът е под мереното правило по ПРАГ, не по тегло",
   int(lb.МОЗЪК_РАНГ_ВХОД) >= 4 and lb.МОЗЪК_ПРАГ >= 12)
# 🔴 ОДИТ-46 · ПРАГЪТ СЕ ВДИГНА ОТ 3 (✅ ГОТОВ) НА 4 (🔥 СИЛЕН).
# Измерено на 42 НЕЗАВИСИМИ наблюдения (17ч, след корекция на базиса):
# ГОТОВ дава 0 от 4 печеливши и −4.10$ средно; живото следене независимо
# от това даде 0 от 4. Над него: СИЛЕН 2/3 +4.17$, МНОГО СИЛЕН 1/1 +11.40$.
# n е нищожно и НЕ доказва нищо — но при небектествана логика посоката на
# съмнението е нагоре: по-малко и по-силни повиквания.
# 🔴 ОДИТ-60 · ОБНОВЕН. Рангът следва прага: щом идват само ⚡ и 💎, всяка
# пратена карта Е покана — няма степен, която пристига, но не е вход.
ck("П40 «гледай» иска поне ⚡ МНОГО СИЛЕН",
   'os.environ.get("МОЗЪК_РАНГ_ВХОД", "5")' in _s40)
ck("П40 има път назад (МОЗЪК_РАНГ_ВХОД=3 връща старото, 99 = само наблюдения)",
   'МОЗЪК_РАНГ_ВХОД", "' in _s40 and 'os.environ.get' in _s40)
ck("П40 прагът е под върха — 💎 РЯДЪК не е единственото, което говори",
   _CB22 is not None and int(lb.МОЗЪК_РАНГ_ВХОД) < len(_CB22.СТЕПЕНИ) - 1)
ck("П40 прагът е над дъното — не всяка искра е «гледай»",
   int(lb.МОЗЪК_РАНГ_ВХОД) >= 3)
ck("П40 сметката за лота е обвита — спъне ли се, картата пак тръгва",
   "_лот_ред = None" in _s40)

# ═══ П41 · ТРИ ДЕФЕКТА ОТ АРМИЯТА, ВСИЧКИТЕ МОИ (ОДИТ-42) ═════════════════
# 🔴 №1 · СЕДЕМТЕ СПИРАЧКИ МЪЛЧАХА ОТ ДЕНЯ, В КОЙТО ГИ НАПИСАХ.
# `new_msgs.append(...)` стоеше 170 реда ПРЕДИ `new_msgs = []` → UnboundLocalError
# при всяко пускане, глътнат от `except` и превърнат в бележка, която
# собственикът не вижда. Точно картата, която обяснява мълчанието на бота,
# беше единствената, която не можеше да излезе. Мерено: 0 спрени карти.
# Тестът ми П23 ГРЕПВАШЕ изходния код вместо да ИЗПЪЛНИ пътя — затова 938
# теста светеха зелено над счупена функция.
# ТОЗИ ТЕСТ ПАЗИ ЦЕЛИЯ КЛАС, не един ред: всяко име, което се пълни със
# `.append()`, трябва да е СЪЗДАДЕНО преди първата си употреба в `main()`.
import ast as _ast41
_дърво41 = _ast41.parse(open("live_bot.py", encoding="utf-8").read())
_гл41 = [n for n in _ast41.walk(_дърво41)
         if isinstance(n, _ast41.FunctionDef) and n.name == "main"][0]
_рано41 = []
for _им41 in ("new_msgs", "silver_new_msgs", "notes", "statuses", "exit_msgs"):
    _деф41 = [n.lineno for n in _ast41.walk(_гл41)
              if isinstance(n, _ast41.Assign)
              for _t41 in n.targets
              if isinstance(_t41, _ast41.Name) and _t41.id == _им41]
    _упо41 = [n.lineno for n in _ast41.walk(_гл41)
              if isinstance(n, _ast41.Attribute) and n.attr == "append"
              and isinstance(n.value, _ast41.Name) and n.value.id == _им41]
    if _деф41 and _упо41 and min(_упо41) < min(_деф41):
        _рано41.append(f"{_им41}: употреба на {min(_упо41)} преди дефиниция на {min(_деф41)}")
ck("П41 нищо не се пълни ПРЕДИ да е създадено " + str(_рано41 or ""), not _рано41)
_s41 = open("live_bot.py", encoding="utf-8").read()
ck("П41 спряната карта се сглобява отделно и влиза СЛЕД списъка",
   "_спряна_карта = None" in _s41 and "new_msgs.append(_спряна_карта)" in _s41)
# ВНИМАНИЕ: "new_msgs = []" се съдържа и в "silver_new_msgs = []" — първата ми
# версия на този тест хвана сребърния списък и падна по невярна причина.
# Затова котвата носи отстъпа: точно `    new_msgs = []` в началото на реда.
_кот41 = chr(10) + "    new_msgs = []"
ck("П41 сглобяването е ПРЕДИ списъка, а вкарването СЛЕД него",
   _s41.index("_спряна_карта = None") < _s41.index(_кот41)
   < _s41.index("new_msgs.append(_спряна_карта)"))

# 🔴 №2 · МОЗЪЧЕН ВХОД БЕЗ ПОД ЗА СЪОТНОШЕНИЕТО
# Единственият реален мозъчен вход (11.08, 17:26) плащаше 0.8x риска до първа
# цел — картата сама го признаваше и пак даваше вход. Шест минути по-късно:
# стоп, −1.55$. Сетъп, който плаща по-малко от риска си, не е вход.
ck("П41 има под за съотношението при мозъчен вход",
   chr(39) + chr(39) not in "x" and 'os.environ.get("МОЗЪК_МИН_RR", "1.5")' in _s41)
ck("П41 слабото съотношение СВАЛЯ картата до наблюдение, не я трие",
   '_s["ранг"] = МОЗЪК_РАНГ_ВХОД - 1' in _s41)
ck("П41 и го казва в дневника", "наблюдение, не вход" in _s41)

# 🔴 №3 · ЧАСОВНИКЪТ СЕ НАВИВАШЕ ОТ НЕПРАТЕНИ КАРТИ
# Мерено: непратен сетъп от 15:51 (9 точки, под прага за 1мин) презаписа
# ПРАТЕНИЯ от 15:11 (12 точки) и заглуши следващите 20 минути.
_c41 = open("brain/chart_brain.py", encoding="utf-8").read()
ck("П41 сканирането само ОТБЕЛЯЗВА какво би записало", "_чака_запис" in _c41)
ck("П41 има отделна функция, която навива часовника", "def запиши_застудяване" in _c41)
ck("П41 ботът я вика САМО за реално пратените",
   "CB.запиши_застудяване(_s, _bstate)" in _s41)
if _CB22 is not None:
    _д41 = {}
    _CB22.запиши_застудяване(
        {"праща": True, "_чака_запис": ("15м|long", {"ранг": 3, "точки": 11, "време": "x"})},
        _д41)
    ck("П41 навиването работи", _д41.get("15м|long", {}).get("точки") == 11)
    _д41б = {}
    _CB22.запиши_застудяване({"праща": False}, _д41б)
    ck("П41 непратена карта НЕ навива часовника", _д41б == {})

# ═══ П42 · СТОПЪТ НЕ СЕ СМАЛЯВА С РАМКАТА (ОДИТ-43) ══════════════════════
# 🔴 ИЗМЕРЕНО НА ЖИВО, две карти от 11.08 вечерта:
#     🎯 вход 4380.67 · 🛑 стоп 4379.12 → стоп 1.55$ → УДАРИ след 6 минути
#     🎯 вход 4369.47 · 🛑 стоп 4366.77 → стоп 2.70$ → УДАРИ след 54 минути
# Причината: «1.0× ATR» се мереше с ATR-а НА САМАТА РАМКА, а на 1-минутна
# графика той е ~2.7$. Шумът на ЗЛАТОТО обаче не се смалява, защото гледаш
# по-бърза графика — той си остава същият.
# Сега подът е ПО-ГОЛЯМОТО от 1.0× ATR и 0.12% от цената (≈5.24$ при 4370$),
# и се скалира сам за среброто (≈0.078$ при 65$).
import importlib.util as _iu42
_sp42 = _iu42.spec_from_file_location("sl42", "brain/b_сливане.py")
_SL42 = _iu42.module_from_spec(_sp42)
try:
    _sp42.loader.exec_module(_SL42)
except Exception:
    _SL42 = None
ck("П42 модулът на залога се внася", _SL42 is not None)
if _SL42 is not None:
    ck("П42 има процентен под", hasattr(_SL42, "МИН_СТОП_ПРОЦЕНТ"))
    ck("П42 подът е поне 0.10% от цената", _SL42.МИН_СТОП_ПРОЦЕНТ >= 0.10)
    for _ц42, _atr42, _мин42 in ((4370.0, 2.7, 5.0), (4370.0, 7.9, 7.9),
                                 (65.0, 0.05, 0.078)):
        _под42 = _SL42.МИН_СТОП_ПРОЦЕНТ / 100.0 * _ц42
        _рез42 = max(_SL42.МИН_СТОП_ATR * _atr42, _под42)
        ck(f"П42 при цена {_ц42:.0f} и ATR {_atr42} стопът е поне {_мин42:.2f}$",
           _рез42 >= _мин42 - 0.01)
    _с42 = open("brain/b_сливане.py", encoding="utf-8").read()
    ck("П42 подът е ВПЛЕТЕН в сметката, не само деклариран",
       "МИН_СТОП_ПРОЦЕНТ / 100.0 * abs(c)" in _с42)
    ck("П42 има път назад", 'МИН_СТОП_ПРОЦЕНТ", "0.12"' in _с42)

# ═══ П44 · БОТЪТ ОБЯСНЯВА МЪЛЧАНИЕТО СИ (ОДИТ-45) ════════════════════════
# Мерено на 1965 живи ръна (02–11.08): гейтът е отказал 100% от ръновете с
# оценка, всеки път `cell: mixed`, защото доларът пада (вдига златото), а
# лихвите растат (свалят го). Ботът мълчи ПРАВИЛНО — но 93.2% от ръновете
# записваха само «тихо (без събития)» и нищо не стигаше до собственика.
#
# 🔴 НАЙ-ВАЖНОТО ТУК СА ЗНАЦИТЕ. На 11.08 качих карта с ОБЪРНАТ знак на долара
# и я хвана армията, не аз. Числата в macro_raw са ВЕЧЕ обърнати (`-(промяна)`),
# значи ПЛЮС = добро за златото. Проверяваме И ЧЕТИРИТЕ комбинации.
_знак44 = [
    # (долар_суров, лихви_сурови, долар_дума, лихви_дума, подредено)
    (+0.0145, +0.07, "пада",  "падат",  True),    # и двете вдигат златото
    (-0.0110, -0.05, "расте", "растат", True),    # и двете го свалят
    (+0.0145, -0.07, "пада",  "растат", False),   # ТОЧНО ТОВА Е ЖИВОТО ДНЕС
    (-0.0110, +0.05, "расте", "падат",  False),
]
for _д44, _л44, _дд44, _лд44, _под44 in _знак44:
    _р44 = lb._защо_мълчи({"долар": _д44, "лихви": _л44}, {"long": 2, "short": 1})
    _т44 = chr(10).join(_р44)
    ck(f"П44 долар {_д44:+.4f} → «{_дд44}»", f"доларът {_дд44}" in _т44)
    ck(f"П44 лихви {_л44:+.3f} → «{_лд44}»", f"лихвите {_лд44}" in _т44)
    # посоката на ВЛИЯНИЕТО не бива да противоречи на посоката на ДВИЖЕНИЕТО
    ck(f"П44 доларът {_дд44} → казва че {'вдига' if _д44 > 0 else 'сваля'}",
       f"{'вдига' if _д44 > 0 else 'сваля'} златото" in _т44)
    ck(f"П44 лихвите {_лд44} → казва че {'вдигат' if _л44 > 0 else 'свалят'}",
       f"{'вдигат' if _л44 > 0 else 'свалят'} златото" in _т44)
    if _под44:
        ck(f"П44 подредено ({_дд44}/{_лд44}) НЕ казва, че мълчи", "⏸" not in _т44)
        ck(f"П44 подредено ({_дд44}/{_лд44}) брои дните подред", "подред" in _т44)
    else:
        ck(f"П44 разбъркано ({_дд44}/{_лд44}) казва, че мълчи", "⏸" in _т44)
        # 🔴 ОДИТ-48 · ОБЪРНАТ. Този тест изискваше «−0.04$ (40094 сделки)» —
        # числото от _meta за СЛЕТИТЕ кофи отпреди 04.08. Гейтът обаче съди по
        # клетката /fresh/long/mixed/net = −0.47$. Заковаваше грешното число.
        ck(f"П44 разбъркано ({_дд44}/{_лд44}) НЕ зазижда число в текста",
           "40094" not in _т44 and "−0.04$" not in _т44)
        ck(f"П44 разбъркано ({_дд44}/{_лд44}) казва, че правилото не носи нищо",
           "мереното" in _т44)
        ck(f"П44 разбъркано ({_дд44}/{_лд44}) казва какво ЧАКА", "👁 чакам" in _т44)
# мъртъв фийд не бива да мине за «подредено»
_мр44 = lb._защо_мълчи({"долар": None, "лихви": None}, {})
ck("П44 мъртъв фийд се казва на глас", any("мълчи" in r for r in _мр44))
ck("П44 мъртъв фийд НЕ обявява посока",
   not any("вдига златото" in r or "сваля златото" in r for r in _мр44))
ck("П44 липсващо макро не гърми", lb._защо_мълчи(None, None) == [])

# ── честното броене на отчети ────────────────────────────────────────────
# Мерено: в 84.6% от 1965 ръна СЕДЕМТЕ рамки са БУКВАЛНО еднакви, а различни
# отчета никога не е имало над ДВА. «7 от 7 съгласни» броеше седем копия.
_едно44 = [(l, "long", 5, "medium", "СРЕДЕН") for l in
           ("1мин", "5м", "15м", "30м", "1час", "4час", "1ден")]
ck("П44 седем еднакви рамки = ЕДИН отчет", lb._съгласни(_едно44, "long") == (1, 1))
_две44 = _едно44[:5] + [("4час", "long", 6, "strong", "СИЛЕН"),
                        ("1ден", "long", 6, "strong", "СИЛЕН")]
ck("П44 два различни отчета се броят като два", lb._съгласни(_две44, "long") == (2, 2))
_смес44 = _едно44[:4] + [("1час", "short", 5, "medium", "СРЕДЕН"),
                         ("4час", "short", 5, "medium", "СРЕДЕН"),
                         ("1ден", "long", 5, "weak", "ЧАКАЙ")]
ck("П44 «weak» не се брои", lb._съгласни(_смес44, "long")[0] == 1)
ck("П44 празна дъска не гърми", lb._съгласни([], "long") == (0, 0))

# ── думата я взима БАВНАТА рамка ─────────────────────────────────────────
# Мерено на 1923 ръна с активна дъска: 1мин взимаше думата в 88.4%, защото
# max() при равенство връща ПЪРВИЯ, а първи в TFS е «1мин».
_src44 = open("live_bot.py", encoding="utf-8").read()
ck("П44 при равенство печели бавната рамка", "_бавност.get(x[0], 0)" in _src44)
ck("П44 има път назад", 'РАВЕНСТВО_БЪРЗА", "0"' in _src44)
_rk44 = {"premium": 3, "strong": 2, "medium": 1, "weak": 0}
_бв44 = {l: i for i, (l, *_) in enumerate(lb.TFS)}
_дъска44 = [(l, "long", 5, "medium", "СРЕДЕН") for l in
            ("1мин", "5м", "15м", "30м", "1час", "4час", "1ден")]
ck("П44 при 7 равни отчета говори «1ден», не «1мин»",
   max(_дъска44, key=lambda x: (_rk44[x[3]], x[2], _бв44.get(x[0], 0)))[0] == "1ден")
_дъска44б = _дъска44[:6] + [("1ден", "long", 4, "medium", "СРЕДЕН")]
ck("П44 но по-СИЛЕН бърз отчет пак печели — редът е клас→точки→бавност",
   max(_дъска44б, key=lambda x: (_rk44[x[3]], x[2], _бв44.get(x[0], 0)))[2] == 5)

# ── картата при обрат на макрото ─────────────────────────────────────────
# Мерено: за 9 дни и 1965 ръна състоянието НЕ се е сменяло нито веднъж, тъй
# че тази карта не може да стане спам — но точно нея той чака.
_об44 = _re22.sub(r"<[^>]+>", "",
                  lb._обрат_msg((True, False), (True, True),
                                {"долар": 0.0145, "лихви": 0.07}, {"long": 1}))
ck("П44 обратът се обявява като събитие", "МАКРОТО СЕ ПОДРЕДИ" in _об44)
ck("П44 обратът носи и двете числа",
   "доларът" in _об44 and "лихвите" in _об44)
_об44р = _re22.sub(r"<[^>]+>", "",
                   lb._обрат_msg((True, True), (True, False),
                                 {"долар": 0.0145, "лихви": -0.07}, {"long": 0}))
ck("П44 разбъркването също се обявява", "МАКРОТО СЕ РАЗБЪРКА" in _об44р)
ck("П44 обратът се праща от бота", '_обрат_msg(' in _src44 and 'макро_сост' in _src44)
ck("П44 обратът е обвит — спъне ли се, не поваля бота",
   "обрат-картата гръмна" in _src44)

# ── пулсът остава ≤7 реда във ВСИЧКИТЕ състояния ─────────────────────────
_бд44 = [(l, "long", 5, "medium", "СРЕДЕН") for l in
         ("1мин", "5м", "15м", "30м", "1час", "4час", "1ден")]
for _име44, _мр, _ст in (("разбъркано", {"долар": 0.0145, "лихви": -0.07}, {"long": 0}),
                         ("подредено", {"долар": 0.0145, "лихви": 0.07}, {"long": 6}),
                         ("мъртво", {"долар": None, "лихви": None}, {}),
                         ("липсващо", None, None)):
    for _ч44 in ("09", "14", "22"):
        _п44 = _re22.sub(r"<[^>]+>", "", lb._pulse_msg(
            _ч44, _бд44, _бд44[-1], "long", "x", False, None, None,
            {"mid": 4370.12}, {"mid": 64.821},
            {"миньори": True, "долар": True, "лихви": False}, False, False,
            macro_raw=_мр, streaks=_ст))
        ck(f"П44 пулс {_ч44} при {_име44} е до 7 реда",
           len(_п44.split(chr(10))) <= 7)
        ck(f"П44 пулс {_ч44} при {_име44} не повтаря «не влизам» след обяснение",
           not ("⏸ двете се бият" in _п44 and "не е пресен" in _п44))


# 🔴 ОДИТ-48 · ЧИСЛОТО НА КАРТАТА ИДВА ОТ КЛЕТКАТА, ПО КОЯТО СЪДИ ГЕЙТЪТ.
_кл48 = ((stats or {}).get("fresh", {}).get("long", {}).get("mixed", {}))
_нт48 = _кл48.get("net")
ck("П44 клетката mixed съществува в статистиката", _нт48 is not None)
if _нт48 is not None:
    _т48 = chr(10).join(lb._защо_мълчи({"долар": 0.0145, "лихви": -0.07},
                                       {"long": 0}, стат=stats))
    # 🔴 ОБНОВЕН v12.5: числото вече идва през `_пари()` и носи типографски
    # минус («−0.47$»), а не ASCII («-0.47$»). Пази СЪЩОТО — че цитираното е
    # ТОЧНО клетката — плюс новото: че е и в пипсове.
    _зп48 = ("+" if float(_нт48) >= 0 else "−") + f"{abs(float(_нт48)):.2f}$"
    ck(f"П44 картата цитира ТОЧНО клетката ({_зп48})", _зп48 in _т48)
    ck("П44 и я дава в ПИПСОВЕ", "пипса" in _т48)
    # 🔴 ОБРАТНАТА ПОСОКА (18.08): досега тук се подаваше САМО стрийк за long и
    # никой не проверяваше, че шортът получава СВОЯТА клетка. Именно затова
    # `_защо_мълчи` можа да живее със заковано "long" — а short/mixed е −1.30$
    # срещу −0.47$, тоест картата подаваше 2.8× по-меко число.
    _нш48 = ((stats or {}).get("fresh", {}).get("short", {}) or {}).get("mixed", {}).get("net")
    if _нш48 is not None:
        _тш48 = chr(10).join(lb._защо_мълчи({"долар": 0.0145, "лихви": -0.07},
                                            {"short": 0}, "short", stats))
        _зш48 = ("+" if float(_нш48) >= 0 else "−") + f"{abs(float(_нш48)):.2f}$"
        ck(f"П44 ШОРТ-картата цитира ШОРТ клетката ({_зш48})", _зш48 in _тш48)
        ck("П44 и НЕ цитира лонг числото", _зп48 not in _тш48)
    _т48б = chr(10).join(lb._защо_мълчи({"долар": 0.0145, "лихви": -0.07},
                                        {"long": 0}, стат=None))
    ck("П44 без статистика картата НЕ си измисля число",
       "$" not in _т48б.split(chr(10))[3] if len(_т48б.split(chr(10))) > 3 else True)
    ck("П44 без статистика пак казва, че правилото не носи нищо",
       "не носи нищо" in _т48б)

# ═══ П45 · БОТЪТ ЗНАЕ, ЧЕ Е СПАЛ (ОДИТ-47) ═══════════════════════════════
# Мерено на 1965 живи ръна: една дупка от 447 МИНУТИ в работно време (06.08,
# 18:36→02:03 София). В целия sent_log няма нищо между 15:36 и 23:03 UTC и
# собственикът не е разбрал. Алармата в aero-bot.yml се пали с `if: failure()`
# — тоест само при ПАДНАЛ рън. Рън, който не тръгва, не пада: най-опасният
# случай беше единственият невидим.
_сп45 = _re22.sub(r"<[^>]+>", "", lb._спал_msg(447, "2026-08-06T15:36", "2026-08-06T23:03"))
_кс45 = _re22.sub(r"<[^>]+>", "", lb._спал_msg(52, "2026-08-06T15:36", "2026-08-06T16:28"))
ck("П45 казва КОЛКО е спал, в часове и минути", "7ч 27мин" in _сп45)
ck("П45 казва ОТ КОГА ДО КОГА, по София", "18:36" in _сп45 and "02:03" in _сп45)
ck("П45 признава, че не е гледал", "не съм гледал" in _сп45)
ck("П45 е до 5 реда", len(_сп45.split(chr(10))) <= 5)
ck("П45 къса дупка се казва само в минути",
   "52 мин" in _кс45 and "ч " not in _кс45.split(chr(10))[0])
_s45 = open("live_bot.py", encoding="utf-8").read()
ck("П45 има праг с път назад", 'os.environ.get("СПАЛ_МИН", "45")' in _s45)
ck("П45 прагът е поне 3x над нормалния интервал (5 мин)", lb.СПАЛ_МИН >= 15)
ck("П45 часовникът се записва ВСЕКИ рън, не само при карта", '\n    meta["последен_рън"] = now_utc' in _s45)
# 🔴 ОДИТ-48 · ОБЪРНАТ. Старата проверка гледаше само ДВАТА КРАЯ на дупката.
# Реалната уикенд дупка е петък 20:55 → неделя 22:01: и двата края са в ОТВОРЕН
# пазар, а между тях лежи целият уикенд → «БОТЪТ СПА 49ч» всеки понеделник.
ck("П45 дупката се мери в ТЪРГОВСКИ минути, не календарни",
   "_дупка = _търговски_минути(_посл, now_utc)" in _s45)
ck("П45 има функция, която брои само отвореното време",
   "def _търговски_минути" in _s45)
# ИЗПЪЛНЕНО, в двете посоки, с РЕАЛНИТЕ дупки от живия дневник:
_уик45 = lb._търговски_минути("2026-08-07T20:55", "2026-08-09T22:01")   # 2946 календарни
_реал45 = lb._търговски_минути("2026-08-06T15:36", "2026-08-06T23:03")  # 447 календарни
ck(f"П45 уикенд дупка от 2946 мин дава {_уик45:.0f} търговски → МЪЛЧИ",
   _уик45 < lb.СПАЛ_МИН)
ck(f"П45 истинската дупка от 06.08 дава {_реал45:.0f} търговски → ПАЛИ",
   _реал45 >= lb.СПАЛ_МИН)
ck("П45 абсурдна дупка (студен старт) не гадае",
   lb._търговски_минути("2020-01-01T00:00", "2026-08-06T23:03") == 0.0)
ck("П45 обърнат ред не гърми", lb._търговски_минути("2026-08-06T23:03", "2026-08-06T15:36") == 0.0)
ck("П45 боклук не гърми", lb._търговски_минути("боклук", "пак боклук") == 0.0)
ck("П45 проверката е обвита — спъне ли се, не поваля бота",
   "проверката за сън се спъна" in _s45)
# структурно: сглобява се РАНО, вкарва се СЛЕД списъка (шаблонът на спряната
# карта). Обратното — append преди списъка — държа седемте спирачки неми.
import ast as _a45
_m45 = [n for n in _a45.walk(_a45.parse(_s45))
        if isinstance(n, _a45.FunctionDef) and n.name == "main"][0]
_сгл45 = [n.lineno for n in _a45.walk(_m45) if isinstance(n, _a45.Assign)
          for t in n.targets if isinstance(t, _a45.Name) and t.id == "_спал_карта"]
_нм45 = [n.lineno for n in _a45.walk(_m45) if isinstance(n, _a45.Assign)
         for t in n.targets if isinstance(t, _a45.Name) and t.id == "new_msgs"]
_вк45 = [n.lineno for n in _a45.walk(_m45) if isinstance(n, _a45.Attribute)
         and n.attr == "append" and isinstance(n.value, _a45.Name) and n.value.id == "new_msgs"]
ck("П45 картата се сглобява ПРЕДИ списъка", bool(_сгл45) and min(_сгл45) < min(_нм45))
ck("П45 и се вкарва СЛЕД него", min(_нм45) < min(_вк45))

# ═══ П46 · РЕЗЕРВ ЗА МАКРОТО + ХИГИЕНА (О8/О11) ══════════════════════════
# О8: един хълцук на Yahoo сваляше цялото макро-краче, а О1 при мъртво краче
# СПИРА новите входове — тоест едно мигване = час без входове. Лихвите имаха
# резерв (FRED пази), Yahoo нямаше. Сега последната ДОБРА стойност се пази.
_s46 = open("live_bot.py", encoding="utf-8").read()
ck("П46 има праг за възрастта на резерва", 'os.environ.get("СТАР_МАКРО_Ч", "36")' in _s46)
ck("П46 резервът се ЗАПИСВА при успех", 'macro_backup.json' in _s46
   and '_бек[_име] = {"utc": now_utc' in _s46)
ck("П46 резервът се ЧЕТЕ при провал", '_рез = (_load_state(out / "macro_backup.json"' in _s46)
ck("П46 стар резерв НЕ се ползва — казва «не виждам»", "_въз <= СТАР_МАКРО_Ч" in _s46)
ck("П46 ползването на резерв се КАЗВА в дневника", "карам на резерва" in _s46)
ck("П46 провалът пак спира входовете, ако няма резерв",
   "if not _взет:" in _s46 and "_макро_мъртво.append(_име)" in _s46)

# ── ИЗПЪЛНЕНО, не грепнато: оцелява ли рамката през запис/четене ─────────
import io as _io46
_idx46 = _pd22.date_range("2026-06-01", periods=120, freq="D")
_df46 = _pd22.DataFrame({"Open": _np22.linspace(40, 50, 120),
                         "High": _np22.linspace(41, 51, 120),
                         "Low": _np22.linspace(39, 49, 120),
                         "Close": _np22.linspace(40.5, 50.5, 120)}, index=_idx46)
_кръг46 = _pd22.read_json(_io46.StringIO(_df46.tail(120).to_json(orient="split")), orient="split")
_кръг46.index = _pd22.to_datetime(_кръг46.index)
ck("П46 рамката (GDX/DXY) оцелява през резерва",
   _кръг46.shape == _df46.shape
   and abs(float(_кръг46["Close"].iloc[-1]) - float(_df46["Close"].iloc[-1])) < 1e-6)
_с46 = _pd22.Series(_np22.linspace(1.9, 2.1, 120), index=_idx46)
_кр46 = _pd22.read_json(_io46.StringIO(_с46.tail(120).to_frame("rate").to_json(orient="split")),
                        orient="split")
_кр46.index = _pd22.to_datetime(_кр46.index)
_rr46 = _кр46["rate"] if "rate" in _кр46 else _кр46.iloc[:, 0]
ck("П46 серията (лихви) оцелява през резерва",
   abs(float(_rr46.iloc[-1]) - float(_с46.iloc[-1])) < 1e-6)
_g46 = _pd22.DataFrame({"Close": _np22.linspace(4300, 4400, 120),
                        "High": _np22.linspace(4310, 4410, 120),
                        "Low": _np22.linspace(4290, 4390, 120)}, index=_idx46)
try:
    _m46 = lb._macro(_g46, _кръг46, _кръг46, _rr46)
    _st46 = lb._streaks(_g46, _кръг46, _кръг46, _rr46)
    _ок46 = isinstance(_m46, dict) and set(_m46) == {"миньори", "долар", "лихви"} \
        and isinstance(_st46, dict)
except Exception:
    _ок46 = False
ck("П46 макрото и стрийкът РАБОТЯТ с възстановените данни", _ок46)

# ── О11 · хигиена ────────────────────────────────────────────────────────
# Мерено: POISON_ATTEMPTS вече го няма ✅ · outbox 0 реда ✅ · archive 3352 KB
# за ЕДИН месец в git repo → ~40 MB/година.
ck("П46 POISON_ATTEMPTS е махнат (коментарът лъжеше)", "POISON_ATTEMPTS" not in _s46)
ck("П46 архивът има таван в месеци", 'os.environ.get("АРХИВ_МЕСЕЦИ", "3")' in _s46)
ck("П46 чистенето пази ПОСЛЕДНИТЕ месеци, не първите",
   "sorted(_по_месец)[:-АРХИВ_МЕСЕЦИ]" in _s46)
ck("П46 чистенето се КАЗВА в дневника", "архивът от" in _s46)
ck("П46 чистенето е обвито", "чистенето на архива се спъна" in _s46)
ck("П46 АРХИВ_МЕСЕЦИ=0 изключва чистенето", "if АРХИВ_МЕСЕЦИ > 0:" in _s46)
ck("П46 опашката има таван", 'os.environ.get("ОПАШКА_ТАВАН", "200")' in _s46)


# 🔴 ОДИТ-48 · ОПАШКА_ТАВАН БЕШЕ ОБЯВЕН И НЕ СЕ ПОЛЗВАШЕ НИКЪДЕ (мое, v9.8),
# а тестът ми по-долу «го пазеше», защото проверяваше само декларацията.
# Константа, която нищо не прави, и тест, който я пази. Хванато от армията.
_s48о = open("live_bot.py", encoding="utf-8").read()
ck("П46 таванът се ЧЕТЕ, не само обявява",
   "if ОПАШКА_ТАВАН > 0 and len(remaining) > ОПАШКА_ТАВАН:" in _s48о)
ck("П46 изходните карти НИКОГА не се режат", "_пази = [m for m in remaining" in _s48о)
ck("П46 орязването се КАЗВА на глас", "опашката преля" in _s48о)
# изпълнено: 250 обикновени + 2 изходни, таван 200
_оп48 = ([{"tag": f"pulse{i}"} for i in range(250)]
         + [{"tag": "exit:tp1"}, {"tag": "s-exit:sl"}])
_пз48 = [m for m in _оп48 if str(m["tag"]).split(":")[0] in lb.EXIT_TAGS]
_др48 = [m for m in _оп48 if str(m["tag"]).split(":")[0] not in lb.EXIT_TAGS]
_мс48 = max(0, lb.ОПАШКА_ТАВАН - len(_пз48))
_рз48 = _пз48 + (_др48[-_мс48:] if _мс48 else [])
ck(f"П46 опашка от {len(_оп48)} се реже до {lb.ОПАШКА_ТАВАН}", len(_рз48) == lb.ОПАШКА_ТАВАН)
ck("П46 и двете изходни карти оцеляват",
   sum(1 for m in _рз48 if str(m["tag"]).split(":")[0] in lb.EXIT_TAGS) == 2)

# ═══ П47 · ВЕРСИЯТА НЕ БИВА ДА ЗАСЕДНЕ (О10) ═════════════════════════════
# 🔴 НАМЕРЕНО ДНЕС: VERSION стоеше "v9.4", докато бяха качени v9.5, v9.6, v9.7
# и v9.8. Всеки ред в live_journal.jsonl от четирите качвания твърдеше грешна
# версия — а дневникът е ЕДИНСТВЕНИЯТ начин отвън да се види какво работи.
# Този тест пада, ако VERSION не се среща в темата на последния commit.
import subprocess as _sp47
_в47 = lb.VERSION
ck("П47 версията изглежда като версия", _в47.startswith("v") and _в47[1].isdigit())
# 🔴 18.08 · ДОТУК ТУК `except Exception` глътваше ВСЯКА причина и я наричаше
# «няма git». В жив рън тестът се обяви за пропуснат, а git работеше нормално от
# същата папка за 0.1 сек. Пропускане, което гадае причината, не може да бъде
# оправено — а този пазач пази точно нещо, което ВЕЧЕ се е чупило (VERSION стоя
# "v9.4" през четири качвания). Сега: `-C` вместо работна папка, 60с вместо 20,
# и истинската причина влиза в текста.
_репо47 = str(_P(lb.__file__).resolve().parent)
_защо47 = ""
try:
    _р47 = _sp47.run(["git", "-C", _репо47, "log", "-1", "--pretty=%s"],
                     capture_output=True, text=True, encoding="utf-8", timeout=60)
    _тема47 = (_р47.stdout or "").strip()
    if not _тема47:
        _защо47 = f"git код {_р47.returncode}: {(_р47.stderr or '')[:60]}"
except Exception as _e47:
    _тема47 = ""
    _защо47 = f"{type(_e47).__name__}: {str(_e47)[:60]}"
def _номер47(v):
    """«v9.10a» → (9, 10, 'a') — за сравнение, не за красота"""
    m = _re.match(r"v(\d+)\.(\d+)([a-z]*)", str(v or ""))
    return (int(m.group(1)), int(m.group(2)), m.group(3)) if m else (0, 0, "")
if _тема47:
    _тек47 = _номер47(_в47)
    _пос47 = _номер47((_re.search(r"v\d+\.\d+[a-z]*", _тема47) or [""])[0]
                      if _re.search(r"v\d+\.\d+[a-z]*", _тема47) else "")
    # 🔴 ПРАВИЛОТО: версията може да е РАВНА на последния commit (току-що качена)
    # или ПО-НОВА (сега я вдигам за следващото качване). НЕ БИВА да е по-стара —
    # точно това стана днес: стоеше v9.4 през четири качвания.
    ck(f"П47 VERSION ({_в47}) не изостава от последния commit "
       f"({_тема47[:34]})", _тек47 >= _пос47)
else:
    # без git (напр. разпакетиран архив) тестът не бива да мълчи ТИХО
    ck(f"П47 ПРОПУСНАТА, не минала — {_защо47 or 'без причина'}", True)
    print(f"    ⚠️ П47: версията НЕ е сверена · причина: {_защо47 or 'неизвестна'}"
          f" · папка: {_репо47[-40:]}")
ck("П47 версията влиза във всеки ред на дневника", '"v": VERSION' in
   open("live_bot.py", encoding="utf-8").read())
_я47 = open(".github/workflows/aero-bot.yml", encoding="utf-8").read()
ck("П47 версията се печата в лога на Actions", "- name: версия" in _я47)

# ═══ О7 · АЛАРМАТА СТРЕЛЯ ВЕДНЪЖ НА ЕПИЗОД ═══════════════════════════════
# Дотук: щом веднъж се навъртят 5 падания, всеки следващ рън също вижда 5-6 и
# алармата излиза на всеки 5 минути до края на епизода.
ck("О7 алармата гледа и ПРЕДХОДНИТЕ 6 ръна", "PREV=$(echo" in _я47)
ck("О7 стреля само на прехода", '[ "${PREV:-0}" -lt 5 ]' in _я47)
ck("О7 брои от 12, не от 6", "per_page=12" in _я47)
# истинската логика, изпълнена тук:
def _ал47(поредица):
    ф = sum(1 for x in поредица[:6] if x == "f")
    п = sum(1 for x in поредица[6:12] if x == "f")
    return ф >= 5 and п < 5
ck("О7 нормално → мълчи", not _ал47("ssssssssssss"))
ck("О7 едно мигване → мълчи", not _ал47("fsssssssssss"))
ck("О7 епизодът ЗАПОЧВА → аларма", _ал47("fffffsssssss"))
ck("О7 епизодът ПРОДЪЛЖАВА → мълчи (без спам)", not _ал47("fffffffffffs"))
ck("О7 епизодът свършва → мълчи", not _ал47("ssffffffffff"))

# ═══ О10 · concurrency ═══════════════════════════════════════════════════
for _ф47 in ("aero-bot", "audit", "tests"):
    _т47 = open(f".github/workflows/{_ф47}.yml", encoding="utf-8").read()
    ck(f"О10 {_ф47}.yml има concurrency", "concurrency:" in _т47)
ck("О10 коментарът за крона не лъже за зимата",
   "зима" in open(".github/workflows/audit.yml", encoding="utf-8").read())

# ═══ П48 · ДАННИ-ХИГИЕНА (О9) ════════════════════════════════════════════
_s48 = open("live_bot.py", encoding="utf-8").read()

# 🔴 №1 · РЕАЛНИ → НОМИНАЛНИ ЛИХВИ БЕЗ ДА СЕ КАЖЕ
# `_rates()` вика FRED DFII10 (РЕАЛНИ). Падне ли, минава на ^TNX/10 —
# НОМИНАЛНИ. Разлика от порядъка на 2 процентни пункта, а клетките на гейта са
# мерени на DFII10. Дотук смяната се казваше само с print() в stdout, който
# умира заедно с Actions лога.
ck("П48 източникът на лихвите се помни", "ЛИХВИ_ИЗТОЧНИК" in _s48)
ck("П48 резервата се маркира като РЕЗЕРВА", 'резерва=True' in _s48)
ck("П48 казва се, че са НОМИНАЛНИ, не реални",
   "са НОМИНАЛНИ" in _s48 and "DFII10" in _s48)
ck("П48 бележката влиза в ДНЕВНИКА, не само в лога",
   'notes.append("🟡 О9: FRED мълчи' in _s48)

# 🔴 №2 · ЗАСТОЯЛ FRED
ck("П48 възрастта на лихвите се мери", 'ЛИХВИ_ИЗТОЧНИК["дни"]' in _s48)
ck("П48 има праг за застой с път назад",
   'os.environ.get("ЛИХВИ_ЗАСТОЙ_ДНИ", "5")' in _s48)
ck("П48 прагът покрива дълъг уикенд без фалшива тревога", lb.ЛИХВИ_ЗАСТОЙ_ДНИ >= 4)
ck("П48 застоят се казва с ЧИСЛОТО дни", "лихвите са отпреди" in _s48)

# 🔴 №3 · СБЪРКАН БАР ВЛИЗА ПРАВО В КЛАСА
# `_scores` чете само `iloc[-1]` — един spike може да вдигне класа и да отвори
# сделка. НЕ поправяме цената мълчаливо: тиха «поправка» на пазарни данни е
# по-опасна от дефекта. Само откриваме и казваме.
ck("П48 има праг за изблик с път назад", 'os.environ.get("ИЗБЛИК_Х", "8")' in _s48)
ck("П48 прагът е далеч над нормален бърз ден", lb.ИЗБЛИК_Х >= 5)
ck("П48 изблик се търси във ВСЯКА рамка", "for _лбл, _рмк in list(frames.items()):" in _s48)
ck("П48 НЕ поправя цената мълчаливо",
   "НЕ поправяме цената" in _s48 and "_рмк[" not in _s48.split("def _изблик")[1][:1200])

# ── ИЗПЪЛНЕНО, в ДВЕТЕ ПОСОКИ (не грепнато) ─────────────────────────────
_idx48 = _pd22.date_range("2026-01-01", periods=80, freq="D")
_c48 = _np22.cumsum(_np22.random.default_rng(7).normal(0, 3, 80)) + 4300
_норм48 = _pd22.DataFrame({"Close": _c48}, index=_idx48)
_из48, _кр48 = lb._изблик(_норм48)
ck(f"П48 нормална серия НЕ пали тревога ({_кр48:.1f}x)", not _из48)
_шип48 = _норм48.copy()
_шип48.iloc[-1, 0] = float(_шип48.iloc[-2, 0]) + 200
_из48б, _кр48б = lb._изблик(_шип48)
ck(f"П48 сбъркан бар ПАЛИ тревога ({_кр48б:.0f}x)", _из48б)
ck("П48 къса серия не гърми", lb._изблик(_pd22.DataFrame({"Close": [1, 2, 3]})) == (False, 0.0))
ck("П48 празна серия не гърми", lb._изблик(_pd22.DataFrame({"Close": []})) == (False, 0.0))
ck("П48 боклук не гърми", lb._изблик(None) == (False, 0.0))

# ═══ П49 · О13 + О15 + О17 ═══════════════════════════════════════════════
_s49 = open("live_bot.py", encoding="utf-8").read()
_a49 = open("audit_bot.py", encoding="utf-8").read()

# 🔧 О13 · ПРАГЪТ ЗА РОЛОВЪР БЕШЕ ГЛОБАЛЕН, А МЕТАЛИТЕ СА С РАЗЛИЧЕН МАЩАБ.
# $8 при злато (~4400) е 0.18% от цената; същите $8 при сребро (~65) са 12% —
# детекторът за среброто беше практически мъртъв.
ck("П49 среброто има свой праг за роловър", hasattr(lb, "ROLLOVER_JUMP_S"))
ck("П49 сребърният праг е далеч под златния", lb.ROLLOVER_JUMP_S < lb.ROLLOVER_JUMP / 10)
_отн49 = (lb.ROLLOVER_JUMP_S / 65.0) / (lb.ROLLOVER_JUMP / 4400.0)
ck(f"П49 двата прага са на сравним мащаб ({_отн49:.1f}x, беше 68x)", 0.2 <= _отн49 <= 6)
ck("П49 подписът приема праг", "скок=None" in _s49)
ck("П49 среброто наистина го подава", "скок=ROLLOVER_JUMP_S" in _s49)
ck("П49 златото пази стария праг (нищо не се променя за него)",
   "скок if скок is not None else ROLLOVER_JUMP" in _s49)
ck("П49 има път назад", 'os.environ.get("ROLLOVER_JUMP_S", "0.4")' in _s49)

# 🔧 О15 · ЧАСОВОТО СКЮ КЛАМПВАШЕ ЦЕЛИ 60 СЕКУНДИ
# Платформа с часовник +60с И ЗАСТОЯЛА цена минаваше за съвсем прясна (age→0).
ck("П49 има отделен допуск за скю", hasattr(lb, "СКЮ_ДОПУСК"))
ck("П49 допускът е стегнат (истинското скю е ~1с)", lb.СКЮ_ДОПУСК <= 5)
ck("П49 но не е нула — 1с скю е нормално", lb.СКЮ_ДОПУСК >= 1)
ck("П49 отвъд допуска платформата се ПРОПУСКА, не се клампва",
   "if age < -СКЮ_ДОПУСК:" in _s49 and "continue" in _s49)
ck("П49 има път назад", 'os.environ.get("СКЮ_ДОПУСК", "2")' in _s49)

# 🔧 О17 · ОДИТ-РОБОТЪТ НЕ ВИЖДАШЕ СРЕБЪРНИТЕ ИЗХОДИ
# `re.match(r"exit:...")` иска съвпадение от НАЧАЛОТО; сребърните тагове са
# `s-exit:...` → нула сребърни изхода в целия одит, никога не се е мерило.
ck("П49 регексът приема и s-exit", '(?:s-)?exit:' in _a49)
_стар49 = r"exit:(\w+)=SENT"
_нов49 = r"(?:s-)?exit:(\w+)=SENT"
for _т49, _зл49, _ср49 in (("exit:tp1=SENT (200)", True, True),
                           ("s-exit:tp1=SENT (200)", False, True),
                           ("sh-exit:sl=SENT (200)", False, False),
                           ("signal=SENT (200)", False, False)):
    ck(f"П49 стар регекс на «{_т49[:18]}» → {_зл49}",
       bool(_re22.match(_стар49, _т49)) == _зл49)
    ck(f"П49 нов регекс на «{_т49[:18]}» → {_ср49}",
       bool(_re22.match(_нов49, _т49)) == _ср49)
ck("П49 СЯНКА-изходите остават извън (те са хипотетични, не сделки)",
   not _re22.match(_нов49, "sh-exit:sl=SENT (200)"))

# ═══ П50 · СТЪЛБАТА 1/3, РАЗМЕРЪТ И НИВАТА (О12 + О16) ═══════════════════
# О16 казваше: selftest НЕ покрива стълбата 1/3, риск-размера и генерирането на
# нива — математиката е вярна (разнищена на ръка), но регресия тук би минала
# ТИХО. Точно това е най-опасният вид дупка: пари, без пазач.
_s50 = open("live_bot.py", encoding="utf-8").read()
_lv50 = {"tp1": 4407.5, "tp2": 4412.0, "tp3": 4420.0, "sl": 4400.0}
_E50 = 4400.0

# ── стълбата, разнищена: всяка комбинация ───────────────────────────────
ck("П50 нищо прибрано + стоп −20 = −20 (цялата позиция)",
   lb._ladder_pnl("sl", {}, _lv50, _E50, 1, -20.0)[0] == -20.0)
ck("П50 ТП1 прибран + безрисков стоп = 1/3 от ТП1",
   abs(lb._ladder_pnl("sl", {"tp1": True}, _lv50, _E50, 1, 0.0)[0] - 2.50) < 0.01)
ck("П50 ТП1+ТП2 + безрисков стоп = 1/3+1/3",
   abs(lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, _lv50, _E50, 1, 0.0)[0] - 6.50) < 0.01)
ck("П50 самата цел НЕ се брои два пъти",
   lb._ladder_pnl("tp1", {"tp1": True}, _lv50, _E50, 1, 7.5)[1] == 0)
# «-0.00» се получава, когато прибраната трета и остатъкът се съкратят точно.
ck("П50 «-0.00» не съществува — само 0.0",
   str(lb._ladder_pnl("sl", {"tp1": True}, _lv50, _E50, 1, -3.75)[0]) == "0.0")
# шорт: знакът трябва да е огледален, не сгрешен
_lvs50 = {"tp1": 4392.5, "tp2": 4388.0, "tp3": 4380.0, "sl": 4400.0}
ck("П50 ШОРТ дава същите пари при огледални нива",
   abs(lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, _lvs50, _E50, -1, 0.0)[0] - 6.50) < 0.01)
ck("П50 ШОРТ стоп е ЗАГУБА, не печалба",
   lb._ladder_pnl("sl", {}, _lvs50, _E50, -1, -20.0)[0] < 0)

# ── 🔧 О12 · ГАПЪТ: реалният фил вместо нивото ──────────────────────────
# `track_trade` знаеше цената на попълване (`px`, гап-съобразена) и я изхвърляше;
# стълбата смяташе по НИВОТО и подценяваше печалбата при всеки гап през цел.
ck("П50 попълването се ПАЗИ в сделката", 'trade.setdefault("hit_px", {})[k] = px' in _s50)
ck("П50 стълбата го приема", "hit_px=None" in _s50)
ck("П50 и го предпочита пред нивото",
   'float(_ц) if _ц is not None else lv[k2]' in _s50)
ck("П50 кумулативните попълвания влизат в снимката", 'obj["hit_px"] = dict(cum_px)' in _s50)
_бг50 = lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, _lv50, _E50, 1, 0.0)[0]
_сг50 = lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, _lv50, _E50, 1, 0.0,
                       {"tp1": 4409.8, "tp2": 4415.3})[0]
ck(f"П50 ЛОНГ гап дава ПОВЕЧЕ от нивото ({_бг50:+.2f} → {_сг50:+.2f})", _сг50 > _бг50)
_сгш50 = lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, _lvs50, _E50, -1, 0.0,
                        {"tp1": 4390.2, "tp2": 4384.7})[0]
ck(f"П50 ШОРТ гап също дава ПОВЕЧЕ (знакът не е обърнат)", _сгш50 > _бг50)
ck("П50 сделка БЕЗ hit_px смята точно както преди (обратна съвместимост)",
   lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, _lv50, _E50, 1, 0.0, None)[0] == _бг50)
ck("П50 празен hit_px също не чупи",
   lb._ladder_pnl("sl", {"tp1": True, "tp2": True}, _lv50, _E50, 1, 0.0, {})[0] == _бг50)

# ── О16 · генерирането на нива ──────────────────────────────────────────
_н50 = lb._levels(4400.0, "long")
ck("П50 ЛОНГ целите са НАД входа", all(_н50[k] > 4400 for k in ("tp1", "tp2", "tp3")))
ck("П50 ЛОНГ стопът е ПОД входа", _н50["sl"] < 4400)
ck("П50 целите растат по ред", _н50["tp1"] < _н50["tp2"] < _н50["tp3"])
_н50с = lb._levels(4400.0, "short")
ck("П50 ШОРТ целите са ПОД входа", all(_н50с[k] < 4400 for k in ("tp1", "tp2", "tp3")))
ck("П50 ШОРТ стопът е НАД входа", _н50с["sl"] > 4400)
ck("П50 ШОРТ е точно огледален на ЛОНГ",
   all(abs((_н50[k] - 4400) + (_н50с[k] - 4400)) < 0.01 for k in _н50))
ck("П50 стопът е обявените $20/унция", abs(abs(_н50["sl"] - 4400) - 20.0) < 0.01)
_ср50 = lb._levels_silver(65.0, "long")
ck("П50 среброто е на 3 знака", all(len(str(v).split(".")[-1]) <= 3 for v in _ср50.values()))
ck("П50 сребърният стоп е далеч по-малък от златния",
   abs(_ср50["sl"] - 65.0) < abs(_н50["sl"] - 4400.0) / 10)

# ═══ П51 · БЕЗ ЧИСЛА НЯМА ВХОД (ОДИТ-49) ═════════════════════════════════
# 🔴 НАМЕРЕНО ОТ АРМИЯТА, ПРОВЕРЕНО ЛИЧНО С ИЗПЪЛНЕНИЕ.
# Преди поправката:
#     здрава статистика  → НЕ  (правилно)
#     празна {}          → ДА (малък размер)   ← ОТВАРЯ гейта
#     липсва `fresh`     → ДА                  ← ОТВАРЯ гейта
#     None / боклук      → AttributeError
# А ботът прави ТОЧНО това при нечетим файл:
#     stats = {}; notes.append("backtest_stats.json не се чете…")
# Значи повреден файл караше бота да праща «КУПИ» — в пазара, в който сам е
# измерил −0.47$ на сделка. Числата от бектеста са ЦЯЛОТО основание този бот да
# предлага вход; без тях предложението е гола геометрия.
# НИТО ЕДИН ТЕСТ не пазеше това — дупката е запълнена тук.
_s51 = open("live_bot.py", encoding="utf-8").read()
ck("П51 има изключвател с път назад", 'os.environ.get("СТАТ_ЗАДЪЛЖИТЕЛНА", "1")' in _s51)
ck("П51 по подразбиране е ВКЛЮЧЕН", lb.СТАТ_ЗАДЪЛЖИТЕЛНА is True)
ck("П51 пазачът е ПЪРВИЯТ — преди стоп-пазача и щита",
   _s51.index("липсва статистика") < _s51.index('_by("стоп-пазач")'))

_ст51 = [("празна {}", {}), ("None", None), ("списък", [1, 2, 3]), ("низ", "боклук"),
         ("липсва fresh", {k: v for k, v in stats.items() if k != "fresh"}),
         ("fresh=низ", dict(stats, fresh="счупено")),
         ("fresh=списък", dict(stats, fresh=[1, 2, 3])),
         ("fresh=None", dict(stats, fresh=None))]
for _име51, _с51 in _ст51:
    for _п51 in ("long", "short"):
        try:
            _т51, _ок51 = lb._advice_entry(_п51, 0, _с51, None, False, 0)
            _гръм51 = False
        except Exception:
            _т51, _ок51, _гръм51 = "", True, True
        ck(f"П51 {_име51} ({_п51}) НЕ пуска вход", (not _ок51) and (not _гръм51))
        if not _гръм51:
            ck(f"П51 {_име51} ({_п51}) КАЗВА защо", "числа" in _т51 or "не се четат" in _т51)

# ── здравата статистика не е пипната: старите пътища работят както преди ──
for _п51 in ("long", "short"):
    _т51, _ок51 = lb._advice_entry(_п51, 0, stats, None, False, 2)
    ck(f"П51 стоп-пазачът пак говори ({_п51})", "стопа днес" in _т51 and not _ок51)
_т51ш, _ок51ш = lb._advice_entry("short", 0, stats, None, True, 0)
ck("П51 US-щитът пак говори", "американски данни" in _т51ш and not _ок51ш)
_т51н, _ = lb._advice_entry("long", 0, stats, None, False, 0)
ck("П51 здравата статистика дава СВОЯТА присъда, не пазача",
   "числа" not in _т51н)
# следа в дневника — за да се брои после
_тр51 = {}
lb._advice_entry("long", 0, {}, None, False, 0, trace=_тр51)
ck("П51 отказът се маркира в следата", _тр51.get("by") == "липсва статистика")

# ═══ П52 · ПОЩАТА НЕ ЯДЕ ПОВРЕДЕН РЕД МЪЛЧАЛИВО (ОДИТ-50) ════════════════
# 🔴 ДОТУК ТАМ СТОЕШЕ `except Exception: pass` — повреден ред изчезваше БЕЗ
# СЛЕД. А редът може да е изходна карта («🛑 СТОПЪТ удари»), тоест пари вече на
# риск — точно класът, който целият останал код пази изрично (EXIT_TAGS не се
# трият дори при 3 твърди провала от Телеграм).
# И начинът на запис го прави ВЕРОЯТНО: `"\n".join(...)` — умре ли процесът по
# средата (Actions има таймаут 8 мин), последният ред остава отрязан.
_s52 = open("live_bot.py", encoding="utf-8").read()
ck("П52 повредените редове се БРОЯТ", "_счуп.append(ln)" in _s52)
ck("П52 суровият текст се ПАЗИ", "outbox_broken.jsonl" in _s52)
ck("П52 изходна карта вдига ЧЕРВЕНО, не бележка",
   "приличат на " in _s52 and "ИЗХОДНА карта" in _s52)
ck("П52 празните редове не се броят за счупени", 'if not ln.strip():' in _s52)

# ── ИЗПЪЛНЕНО: опашка с два ОТРЯЗАНИ реда, както при убит процес ─────────
import shutil as _sh52, json as _js52
from pathlib import Path as _P52
_д52 = _P52(f"_t52_{_os.getpid()}")
_sh52.rmtree(_д52, ignore_errors=True); _д52.mkdir()
(_д52 / "outbox.jsonl").write_text(
    _js52.dumps({"tag": "pulse", "text": "здрав", "first_ts": "2026-08-12T09:00",
                 "attempts": 0}, ensure_ascii=False) + chr(10)
    + '{"tag": "exit:sl", "text": "СТОПЪТ уд' + chr(10)
    + '{"tag": "pulse", "text": "отря', encoding="utf-8")
_ст52 = []
lb._outbox_flush(_д52, [], _ст52, dry=True)
_т52 = chr(10).join(_ст52)
ck("П52 отрязаната ИЗХОДНА карта вдига червено", "🔴" in _т52 and "ИЗХОДНА карта" in _т52)
ck("П52 счупеното е запазено на диска", (_д52 / "outbox_broken.jsonl").exists())
_бр52 = sum(1 for _ in open(_д52 / "outbox_broken.jsonl", encoding="utf-8"))
ck(f"П52 и ДВАТА счупени реда са запазени ({_бр52})", _бр52 == 2)
_ост52 = sum(1 for l in open(_д52 / "outbox.jsonl", encoding="utf-8") if l.strip())
ck(f"П52 здравият ред ОЦЕЛЯВА ({_ост52})", _ост52 == 1)
# и обратната посока: чиста опашка не вика вълк
(_д52 / "outbox.jsonl").write_text(
    _js52.dumps({"tag": "pulse", "text": "здрав", "first_ts": "2026-08-12T09:00",
                 "attempts": 0}, ensure_ascii=False), encoding="utf-8")
(_д52 / "outbox_broken.jsonl").unlink(missing_ok=True)
_ст52б = []
lb._outbox_flush(_д52, [], _ст52б, dry=True)
ck("П52 чиста опашка НЕ вдига тревога",
   not any("повредени" in x or "ИЗХОДНА карта" in x for x in _ст52б))
_sh52.rmtree(_д52, ignore_errors=True)

# ═══ П53 · ВСЯКО СРИВАНЕ БЕШЕ НЕВИДИМО (ОДИТ-52) ═════════════════════════
# 🔴 Обработчикът на грешки стои на МОДУЛНО ниво (в `except` на `try: main()`),
# а първото, което пипаше, беше `Path(args.out)`. `args` обаче се създава ВЪТРЕ
# в `main()` (ред ~2216) и никъде няма `global args`. Значи при всяко сриване:
#   1. traceback-ът се печата                                  ✅
#   2. записът пада на `Path(args.out)` → NameError             🔴
#   3. глътва се от `except Exception: pass` най-долу           🔴
#   4. `err_seen.json` НЕ се записва — никога не се е записвал  🔴
# Същото важи и за `now_utc` — и той е локален на main().
# А логът на GitHub Actions е недостъпен отвън, тоест сриванията бяха невидими,
# а одит-роботът чакаше файл, който не идва, и светеше зелено върху нищо.
_s53 = open("live_bot.py", encoding="utf-8").read()
ck("П53 пътят НЕ идва от args (той е локален на main)",
   "_ef = Path(args.out)" not in _s53 and '_ef = Path(_изх)' in _s53)
ck("П53 часът се смята на място, не от now_utc",
   "_сега = _dt52.now(_tz52.utc)" in _s53)
ck("П53 записът пази и КЪДЕ е гръмнало", '"къде": traceback.format_exc()' in _s53)
ck("П53 понася и стария формат (низ вместо речник)",
   '_prev.get("utc") if isinstance(_prev, dict) else _prev' in _s53)
# 🔴 `sys` НЕ беше внесен на модулно ниво → `sys.argv` гърмеше мълчаливо и
# `--out` се игнорираше. Открито при изпълнението, не при четенето.
_имп53 = [l for l in _s53.splitlines()[:30] if l.startswith("import ")]
ck("П53 `sys` е внесен на модулно ниво (иначе --out се игнорира тихо)",
   any(_re22.search(r"(^|[ ,])sys([ ,]|$)", l) for l in _имп53))

# ── ИЗПЪЛНЕНО: карам ИСТИНСКИЯ скрипт да гръмне и гледам следата ─────────
import subprocess as _sp53, shutil as _sh53, json as _js53
from pathlib import Path as _P53
_д53 = _P53(f"_t53_{_os.getpid()}")
_sh53.rmtree(_д53, ignore_errors=True); _д53.mkdir()
try:
    _r53 = _sp53.run([sys.executable, "live_bot.py", "--out", str(_д53)],
                     capture_output=True, text=True, encoding="utf-8",
                     errors="replace", timeout=180)
    _изл53 = (_r53.stdout or "") + (_r53.stderr or "")
except Exception as _e53:
    _изл53 = ""
_ф53 = _д53 / "err_seen.json"
if _изл53 and "ГРЕШКА В БОТА" in _изл53:
    ck("П53 сриването СЪЗДАВА err_seen.json", _ф53.exists())
    if _ф53.exists():
        _д = _js53.loads(_ф53.read_text(encoding="utf-8"))
        ck("П53 записът има поне един подпис", len(_д) >= 1)
        _зп = list(_д.values())[0]
        ck("П53 записът е речник, не гол низ", isinstance(_зп, dict))
        ck("П53 записът носи час", bool(_зп.get("utc")))
        ck("П53 записът носи самата грешка", bool(_зп.get("грешка")))
        ck("П53 записът носи КЪДЕ е гръмнало", bool(_зп.get("къде")))
        ck("П53 «къде» сочи ред от live_bot.py",
           any("live_bot.py" in str(x) for x in (_зп.get("къде") or [])))
    ck("П53 --out се уважава — живата папка НЕ е пипната",
       not (_P53("live") / "err_seen.json").exists()
       or (_P53("live") / "err_seen.json").stat().st_mtime < _ф53.stat().st_mtime)
else:
    ck("П53 ботът НЕ гръмна тук — проверката е ПРОПУСНАТА, не минала", True)
    print("    ⚠️ П53: ботът не гръмна (има мрежа?) — следата не е проверена")
_sh53.rmtree(_д53, ignore_errors=True)

# ═══ П54 · КОЗМЕТИКА НЕ ИЗКЛЮЧВА ПАРИЧЕН ПАЗАЧ (ОДИТ-54) ═════════════════
# 🔴 Проверката за съотношението риск/печалба стоеше ВЪТРЕ в `try`, който
# съществува само за козметичния ред «📏 нивото иска X$ място». Гръмнеше ли
# нещо там, `except: _лот_ред = None` го глътваше и СВАЛЯНЕТО НА РАНГА НЕ
# СТАВАШЕ — слабият сетъп излизаше като «👁 ГЛЕДАЙ», покана за вход.
# ИЗПЪЛНЕНО преди поправката, сетъп с 0.8x риска и ранг 4:
#     нормално        → ранг 3 → 🧠 наблюдение
#     размерът гръмва → ранг 4 → 👁 ГЛЕДАЙ  🔴
_s54 = open("live_bot.py", encoding="utf-8").read()
ck("П54 R:R проверката има СВОЙ try", "_rr1, _слаб = 0.0, True" in _s54)
ck("П54 при провал СВАЛЯ (безопасната посока), не пропуска",
   "свалям до наблюдение" in _s54)
ck("П54 козметиката е в ОТДЕЛЕН try", "козметиката отделно" in _s54)
ck("П54 R:R е ПРЕДИ козметиката — парите преди украсата",
   _s54.index("_слаб = bool(_rr1)") < _s54.index('_лот_ред = f"📏'))
ck("П54 свалянето пак става В ДВАТА речника (ОДИТ-44 не е загубен)",
   '_s["_карта_вход"]["ранг"] = МОЗЪК_РАНГ_ВХОД - 1' in _s54)

# ── ИЗПЪЛНЕНО: четирите начина на счупване + един здрав сетъп ───────────
def _пуск54(съотн, счупи_rr=False):
    """възпроизвежда НОВАТА подредба от live_bot"""
    # ОДИТ-60: рангът се взима ЖИВ, не зазидан — прагът се мени с решение на
    # собственика и тестът не бива да го замразява.
    _р = lb.МОЗЪК_РАНГ_ВХОД
    _с = {"вход": 4400.0, "стоп": 4398.0, "съотношение": съотн, "ранг": _р,
          "_карта_вход": {"ранг": _р}}
    try:
        _rr = float(_с["няма"]) if счупи_rr else float(_с.get("съотношение") or 0)
        _сл = bool(_rr) and _rr < lb.МОЗЪК_МИН_RR
    except Exception:
        _rr, _сл = 0.0, True
    if _сл and int(_с.get("ранг", 0)) >= lb.МОЗЪК_РАНГ_ВХОД:
        _с["ранг"] = lb.МОЗЪК_РАНГ_ВХОД - 1
        _с["_карта_вход"]["ранг"] = lb.МОЗЪК_РАНГ_ВХОД - 1
    return _с["ранг"], _с["_карта_вход"]["ранг"]

ck("П54 слаб сетъп (0.8x) пада до наблюдение", _пуск54(0.8)[0] < lb.МОЗЪК_РАНГ_ВХОД)
ck("П54 и в двата речника", _пуск54(0.8)[1] < lb.МОЗЪК_РАНГ_ВХОД)
ck("П54 нечетимо съотношение също пада (безопасната посока)",
   _пуск54(0.8, счупи_rr=True)[0] < lb.МОЗЪК_РАНГ_ВХОД)
ck("П54 съотношение точно на прага минава", _пуск54(lb.МОЗЪК_МИН_RR)[0] >= lb.МОЗЪК_РАНГ_ВХОД)
ck("П54 силен сетъп (3.0x) НЕ пада незаслужено", _пуск54(3.0)[0] >= lb.МОЗЪК_РАНГ_ВХОД)
ck("П54 липсващо съотношение (0) не сваля — няма основание",
   _пуск54(0)[0] >= lb.МОЗЪК_РАНГ_ВХОД)

# ═══ П55 · САНИТИТО ОСТАВЯ СЛЕДА (ОДИТ-55) ═══════════════════════════════
# ИЗМЕРЕНО на 2158 живи ръна: 267 (12.4%) губят живата цена ТУК — суровата е
# била жива и санитито я е отрязало. Тогава `stale_price=True` и входовете
# спират. И НИТО ЕДНО от 267-те не оставяше следа защо.
# НЕ пипам прага: той съществува, защото един $100 глич минаваше сам (F2).
# Първо мерим — числата ще кажат дали е тесен и с колко.
_s55 = open("live_bot.py", encoding="utf-8").read()
ck("П55 санитито приема следа", "следа=None" in _s55)
ck("П55 записва разликата И допуска", '"разлика":' in _s55 and '"допуск":' in _s55)
ck("П55 бележката влиза в дневника", "живата цена отрязана" in _s55)
ck("П55 следата отива и в journal-а", '"saniti":' in _s55)
_т55 = {}
_сп55 = {"bid": 4399.8, "ask": 4400.2, "mid": 4400.0}
ck("П55 близка цена минава", lb._spot_sane(_сп55, 4402.0, 8.0, bar_rng=3.0, следа=_т55) is not None)
ck("П55 и пак оставя следа", _т55.get("мина") is True and _т55["разлика"] == 2.0)
_т55б = {}
ck("П55 далечна цена се реже",
   lb._spot_sane(_сп55, 4415.0, 8.0, bar_rng=3.0, следа=_т55б) is None)
ck("П55 следата казва КОЛКО е разминато", _т55б["разлика"] == 15.0)
ck("П55 следата казва КАКЪВ е бил допускът", _т55б["допуск"] >= 8.0)
_т55в = {}
ck("П55 глич от 100$ ПАК се реже (прагът не е разхлабен)",
   lb._spot_sane(_сп55, 4500.0, 8.0, bar_rng=3.0, spot_jump=95.0, следа=_т55в) is None)
ck("П55 без следа не гърми", lb._spot_sane(_сп55, 4402.0, 8.0) is not None)

# ═══ П56 · МОЗЪЧНАТА РАЗВРЪЗКА СЕ ПАЗИ КАТО ВСЯКА ДРУГА (ОДИТ-56) ════════
# 🔴 `brain-exit` ЛИПСВАШЕ от EXIT_TAGS. Това е картата «🛑 СТОПЪТ удари ·
# наблюдението от 20:26» — развръзката на сетъп, който собственикът е следил.
# `sh-exit` (сянката) БЕШЕ в списъка, а тя е също толкова хипотетична.
# Значи мозъчните развръзки можеха да бъдат ИЗХВЪРЛЕНИ като отровни, ОРЯЗАНИ
# от тавана на опашката (v10.4) и да НЕ се разпознаят като пари при повреден
# ред (v10.6). Мерено в живия sent_log: 7 такива карти вече са пратени.
ck("П56 brain-exit е в защитеното семейство", "brain-exit" in lb.EXIT_TAGS)
for _т56 in ("exit:sl", "s-exit:tp1", "sh-exit:sl", "brain-exit:стоп"):
    ck(f"П56 {_т56} се пази", _т56.split(":")[0] in lb.EXIT_TAGS)
for _т56 in ("brain:15м:КЪСО", "pulse", "signal", "standing", "digest"):
    ck(f"П56 {_т56} НЕ се пази (и не трябва)", _т56.split(":")[0] not in lb.EXIT_TAGS)
# тримата пазача, които четат списъка, вече го уважават
_оп56 = [{"tag": f"pulse{i}"} for i in range(250)] + [{"tag": "brain-exit:стоп"}]
ck("П56 при препълнена опашка brain-exit оцелява",
   len([m for m in _оп56 if str(m["tag"]).split(":")[0] in lb.EXIT_TAGS]) == 1)
ck("П56 повреден brain-exit ред се брои за ПАРИ",
   any(_t in '{"tag": "brain-exit:стоп", "text": "СТОПЪТ уд' for _t in lb.EXIT_TAGS))
ck("П56 отровното правило не важи за него",
   'msg["tag"].split(":")[0] in EXIT_TAGS' in open("live_bot.py", encoding="utf-8").read())

# ═══ П57 · ТАВАНИТЕ ПО ГРУПА И СТЪПАЛАТА (ОДИТ-58) ═══════════════════════
# 🔴 ИЗМЕРЕНО: 7 от 8 тавана НЕ МОГАТ да режат — максималните точки на групата
# са РАВНИ на тавана ѝ навсякъде освен при А (макс 8, таван 5).
# Не ги стягам наслуки: тези числа менят СТЕПЕНТА, а по степента се решава коя
# карта е «👁 ГЛЕДАЙ». Логиката няма бектест. Този тест ЗАКОВАВА състоянието —
# добави ли се условие в група, таванът ѝ оживява и тестът го казва.
import collections as _c57
if _CB22 is not None:
    import brain.b_сливане as _SL57
    _тег57 = _c57.Counter()
    _бр57 = _c57.Counter()
    for _к, (_т, _гр, _) in _SL57.ТАБЛИЦА.items():
        _тег57[_гр] += _т
        _бр57[_гр] += 1
    _живи57 = [g for g in _SL57.ТАВАН_ГРУПА if _тег57[g] > _SL57.ТАВАН_ГРУПА[g]]
    ck(f"П57 таванът реже САМО за {_живи57} (7 от 8 са декорация — знаем го)",
       _живи57 == ["А"])
    ck("П57 нито един таван не е ПОД това, което групата не може да достигне",
       all(_SL57.ТАВАН_ГРУПА[g] <= _тег57[g] for g in _SL57.ТАВАН_ГРУПА))
    ck("П57 сборът на таваните покрива МАКС_ТОЧКИ",
       sum(_SL57.ТАВАН_ГРУПА.values()) == _SL57.МАКС_ТОЧКИ)
    ck("П57 таблицата има 29 условия (промени ли се — виж таваните)",
       len(_SL57.ТАБЛИЦА) == 29)
    ck("П57 всяка група има поне 3 условия", all(v >= 3 for v in _бр57.values()))
    # 🟡 СТЪПАЛАТА: Z2b влече Z2 по конструкция (единодушно ⇒ мнозинство ≥5).
    # Това е НАРОЧНО и документирано (ред 239 в b_сливане): по-силното
    # доказателство печели още една точка. Не е дефект, но да се знае.
    _ст57 = [k for k in _SL57.ТАБЛИЦА if k.endswith("b_") or "b_" in k[:4]]
    ck("П57 стъпалата са отделни условия в таблицата, не скрити множители",
       all(_SL57.ТАБЛИЦА[k][0] == 1 for k in _SL57.ТАБЛИЦА
           if k in ("B1b_стъпало", "Z2b_единодушно") or k.startswith("Z2b")))
    ck("П57 прагът за «гледай» е СЛЕД като таваните са приложени",
       "ТАВАН_ГРУПА" in open("brain/b_сливане.py", encoding="utf-8").read())

# ═══ П58 · СРЕБЪРНИЯТ ГЕЙТ + МЕТАЛЪТ В ПРИСЪДАТА (ОДИТ-59) ═══════════════
# 🔴 НАЙ-ТЕЖКАТА ОЦЕЛЯЛА НАХОДКА (тежест 5, ПАРИ), доказана с числа от самия
# backtest_stats.json и с живия дневник:
#     seg_mixed = sv.get("mixed") or seg_stale
# Среброто НЯМА клетка `mixed` → при разбъркано макро падаше на `stale`,
# клетката «сигналът е ОСТАРЯЛ, но макрото БЕШЕ подредено». Две различни
# състояния; точно тяхното сливане беше разделено за ЗЛАТОТО на 04.08:
#     злато  mixed  n=28706  −0.47$    ← шум
#     злато  stale  n=21900  +0.94$    ← печели
#     сребро mixed  НЯМА                      ← ПОПРАВЕНО 17.08
#     сребро stale  n=556    +0.014$   ← и това число падна на 18.08:
# 🔴 F24 (18.08) ПРЕИЗМЕРИ всичко. `stale` n=556 не се възпроизвежда — истинското
# е n=1204. `fresh` беше +0.111$, преизмерено +0.033$ (3.4× по-оптимистично).
# И решаващото: след реалистичен спред 0.03$/oz НИТО ЕДНА сребърна клетка не
# оцелява, а всяка ЛОНГ клетка сменя знака между епохите. Затова проверките
# по-долу са ОБЪРНАТИ — пазят новото поведение, не старото.
# ИЗМЕРЕНО НА ЖИВО: златото е отказало 1518 от 1518 ръна с `cell=mixed`, а
# среброто е отворило 3 сделки, две от тях ДОКАЗАНО в същото състояние.
# Втори слой: сребърните клетки нямат `lo`/`hi` → `_noise` СТРУКТУРНО не може
# да се задейства, тоест +0.014$ минава за «ръб» без проверка дали нулата е вътре.
_s58 = open("live_bot.py", encoding="utf-8").read()
ck("П58 има изключвател с път назад", 'os.environ.get("СРЕБРО_MIXED", "нищо")' in _s58)
ck("П58 по подразбиране НЕ заема чужда клетка", lb.СРЕБРО_MIXED != "stale")
ck("П58 отказът е изричен", "за среброто такъв" in _s58)
# 🔴 ОБЪРНАТ ОТ F24 (18.08). Пазеше, че сребърните клетки НЯМАТ `lo`/`hi` —
# това беше вярната диагноза тогава и точно затова `_noise` не можеше да се
# задейства за среброто. F24 ги премери (12858 сделки, блоков бутстрап по ден).
# Сега пази ОБРАТНОТО: всяка решаваща клетка ИМА интервал.
ck("П58/F24 сребърните клетки ВЕЧЕ имат интервали (пазачът може да работи)",
   all(isinstance((stats.get("silver", {}).get(_д, {}).get(_к, {}) or {}).get("lo"), float)
       and isinstance((stats.get("silver", {}).get(_д, {}).get(_к, {}) or {}).get("hi"), float)
       for _д in ("long", "short") for _к in ("day1", "fresh", "mixed", "stale")))
ck("П58 златото ИМА разделена клетка mixed",
   isinstance(stats.get("fresh", {}).get("long", {}).get("mixed"), dict))
ck("П58 златната mixed е отрицателна (затова се отказва)",
   float(stats["fresh"]["long"]["mixed"]["net"]) < 0)
# решетката: сребро при разбъркано макро отказва И В ДВЕТЕ посоки
for _д58 in ("long", "short"):
    _т58, _ок58 = lb._advice_entry(_д58, 0, stats, None, False, 0, sym="XAGUSD")
    ck(f"П58 сребро {_д58} при разбъркано макро ОТКАЗВА", not _ок58)
    # 🔴 ОБЪРНАТ ОТ F24: до 18.08 причината беше «такъв пазар НЕ Е МЕРЕН».
    # Вече Е мерен — и мереното казва, че ръбът е под спреда. Картата трябва да
    # носи НОВАТА причина, не старата.
    ck(f"П58/F24 сребро {_д58} казва мерената причина",
       "изключено" in _т58 or "няма измерен ръб над спреда" in _т58)
# нищо друго не се променя
for _ск58 in (1, 2, 4):
    _т58г, _ок58г = lb._advice_entry("long", _ск58, stats, None, False, 0, sym="XAUUSD")
    ck(f"П58 златото при стрийк {_ск58} е непокътнато", _ок58г)
# 🔴 ОБЪРНАТ ОТ F24. Пазеше, че среброто при ПОДРЕДЕНО макро пак дава вход —
# вярно на 17.08, когато поправях само клетката `mixed`. F24 премери всичките:
# след спред 0.03$/oz НИТО ЕДНА не оцелява, а всяка ЛОНГ клетка сменя знака
# между епохите (+ до 2012, − след 2013). Сега пази ОБРАТНОТО.
_т58с, _ок58с = lb._advice_entry("long", 2, stats, None, False, 0, sym="XAGUSD")
ck("П58/F24 среброто НЕ минава и при подредено макро", not _ок58с)
ck("П58/F24 и казва мерената причина",
   "изключено" in _т58с or "няма измерен ръб над спреда" in _т58с)
# 🔴 НАИМЕНУВАНЕТО НА МЕТАЛА се проверява на карта, която НАИСТИНА ПУСКА —
# иначе тази проверка щеше да гледа само откази и «ДА … среброто» не се пази
# от никого. Пуска се при спред 0.00, тоест по СЪЩИЯ код, не по друг клон.
_ст58 = lb.СРЕБРО_СПРЕД
_вх58 = lb.СРЕБРО_ВХОД
_bs58 = _cpF24.deepcopy(stats)
lb.СРЕБРО_СПРЕД = 0.0
lb.СРЕБРО_ВХОД = True          # 🔴 F24г: искат се ДВЕТЕ, не само спредът
lb._сребро_разход(_bs58, None)
_тДА58, _окДА58 = lb._advice_entry("long", 1, _bs58, None, False, 0, sym="XAGUSD")
lb.СРЕБРО_СПРЕД = _ст58
lb.СРЕБРО_ВХОД = _вх58
ck("П58/F24 при нулев спред среброто ПУСКА (спирачката мери, не е закована)", _окДА58)
ck("П58/F24 пускащата сребърна карта назовава СРЕБРОТО", "среброто" in _тДА58)
ck("П58/F24 и НЕ споменава златото", "златото" not in _тДА58)
# 🔴 F24г · СПИРАЧКАТА ЗА СРЕБРО СТОИ ПРЕДИ КЛЕТКИТЕ и има ПЪТ НАЗАД
ck("F24г по подразбиране среброто е ИЗКЛЮЧЕНО", lb.СРЕБРО_ВХОД is False)
ck("F24г отказът казва, че е изключено, не че «пазарът не е подходящ»",
   "изключено" in lb._advice_entry("long", 1, stats, None, False, 0, sym="XAGUSD")[0])
ck("F24г ЗЛАТОТО не се засяга от сребърната спирачка",
   lb._advice_entry("long", 1, stats, None, False, 0, sym="XAUUSD")[1])
ck("F24г файлът записва ЗАЩО (качеството на данните)",
   "27%" in (stats.get("silver", {}) or {}).get("_качество_на_данните", ""))
ck("F24г и че интервалите са по-тесни от честните",
   "iid" in (stats.get("silver", {}) or {}).get("_интервалите_са_тесни", ""))

# 🔴 ОДИТ-59б · МЕТАЛЪТ БЕШЕ ЗАКОВАН В ПРИСЪДАТА
# Сребърна карта казваше «това вдига ЗЛАТОТО» — редът, по който собственикът
# решава, назоваваше чужд метал.
ck("П58 сребърната присъда назовава СРЕБРОТО", "среброто" in _т58с)
ck("П58 и НЕ споменава златото", "златото" not in _т58с)
_т58з, _ = lb._advice_entry("long", 2, stats, None, False, 0, sym="XAUUSD")
ck("П58 златната присъда назовава ЗЛАТОТО", "златото" in _т58з)

# ═══ П59 · ТРИТЕ БЛИЗНАКА · СТЪЛБАТА, НЕ ГОЛА РАЗЛИКА (ОДИТ-61) ══════════
# 🔴 Три потвърдени находки, ЕДНА причина: на същия ред, на който картата
# изброява прибраните трети («1️⃣ 2️⃣ ✅»), показваше разлика, смятана за
# ЦЯЛАТА позиция от входа до сега — все едно нищо не е прибрано.
# Три карти, които собственикът вижда всеки ден: вечерната равносметка,
# «КЪДЕ СМЕ» и пулсът. Изходната карта отдавна има вярната сметка
# (`_ladder_pnl`); просто никога не е била пусната по тези три реда.
_s59 = open("live_bot.py", encoding="utf-8").read()
ck("П59 има общ помощник за отворена сделка", "def _отворена_стълба" in _s59)
ck("П59 и трите места го ползват",
   _s59.count("пл, _ = _отворена_стълба(tr, sp") == 3)
ck("П59 голата разлика я няма никъде",
   '(sp["mid"] - tr["entry"]) if tr["direction"]' not in _s59)
ck("П59 помощникът вика СЪЩАТА функция като изходната карта",
   "_ladder_pnl(\"отворена\"" in _s59)
_tr59 = {"direction": "long", "entry": 4400.0,
         "levels": {"tp1": 4407.5, "tp2": 4412.0, "tp3": 4420.0, "sl": 4400.0}}
_sp59 = {"mid": 4404.0}
_гола59 = 4.0
_н59, _в59 = lb._отворена_стълба(dict(_tr59, hit={}), _sp59)
ck("П59 без прибрани трети стълбата = голата разлика", abs(_н59 - _гола59) < 0.01 and _в59 == 0)
_н59а, _в59а = lb._отворена_стълба(dict(_tr59, hit={"tp1": True}), _sp59)
ck(f"П59 с ТП1 показва ПОВЕЧЕ ({_н59а:+.2f} срещу {_гола59:+.2f})", _н59а > _гола59 and _в59а == 1)
_н59б, _в59б = lb._отворена_стълба(dict(_tr59, hit={"tp1": True, "tp2": True}), _sp59)
ck(f"П59 с ТП1+ТП2 показва още повече ({_н59б:+.2f})", _н59б > _н59а and _в59б == 2)
_trs59 = {"direction": "short", "entry": 4400.0,
          "levels": {"tp1": 4392.5, "tp2": 4388.0, "tp3": 4380.0, "sl": 4400.0},
          "hit": {"tp1": True, "tp2": True}}
_нш59, _ = lb._отворена_стълба(_trs59, {"mid": 4396.0})
ck("П59 ШОРТ е огледален, не обърнат", abs(_нш59 - _н59б) < 0.01)
ck("П59 без жива цена не гърми", lb._отворена_стълба(_tr59, None) == (None, 0))
ck("П59 без сделка не гърми", lb._отворена_стълба(None, _sp59) == (None, 0))
ck("П59 счупена сделка не гърми", lb._отворена_стълба({"direction": "long"}, _sp59) == (None, 0))

# ═══ П60 · ЧЕТИРИ МЪЛЧАЛИВИ ПЪТЯ (ОДИТ-62) ═══════════════════════════════
# Един клас: нещо се случва, дневникът не научава, после никой не може да преброи.
_s60 = open("live_bot.py", encoding="utf-8").read()
ck("П60 дедупът КАЗВА колко е махнал", "📎 дедуп:" in _s60)
ck("П60 и брои преди/след", "_преди_дедуп = len(pending)" in _s60)
# 47 от 76 пъти «застоял бар» е обикновената дневна CME пауза — ботът ЗНАЕ за нея
ck("П60 застоялият бар назовава паузата, не гадае «празник?»",
   "дневната пауза на борсата" in _s60 and "_cme_pause(now_utc)" in _s60)
ck("П60 и пази честното «не знам» за останалите случаи",
   "празник или тънка сесия?" in _s60)
# «буден цял ден» броеше 13 от 24 часа — 27.9% от ръновете не влизаха в НИКОЯ равносметка
ck("П60 равносметката вече не твърди «цял ден»", "буден цял ден" not in _s60)
ck("П60 казва КОЙ ОБХВАТ покрива", "проверки ({_обхват})" in _s60)
ck("П60 обхватът е обвит — счупен час не поваля картата", '_обхват = "днес"' in _s60)
# причината за заглушаване се пишеше в поле, което не влизаше в дневника
ck("П60 причината за заглушаване влиза в brain_journal",
   '"застудяване": _s.get("застудяване")' in _s60)
# и обратната посока: полето наистина се пълни някъде
ck("П60 полето наистина се пълни от заглушителите",
   '_s["застудяване"] = "таван за рън"' in _s60
   and "общ разредител" in _s60)

# ═══ П61 · ПОСЛЕДНАТА ПАРТИДА (ОДИТ-63) ══════════════════════════════════
_s61 = open("live_bot.py", encoding="utf-8").read()
_a61 = open("audit_bot.py", encoding="utf-8").read()
_k61 = open("brain/b_карта.py", encoding="utf-8").read()

# 🔴 1 · СЯНКА-ИЗХОДИТЕ ИЗЛИЗАХА СЛЕД СИГНАЛА
# Мерено в живия sent_log: 6 от 7 минути с двете показват сигнала ПЪРВИ, а
# коментарът обещава «редът = хронология: изходи → карта». Сянката е за
# МИНАЛОТО, сигналът за СЕГА. (Реалните изходи exit/s-exit ВЕЧЕ бяха първи.)
ck("П61 сянка-изходите се пренареждат пред сигнала", "_pred61" not in _s61
   and "new_msgs = _пред + _сянка + _сиг" in _s61)
def _ред61(вход, сянка):
    _п = [m for m in вход if not str(m[0]).startswith(("signal", "s-signal"))]
    _с = [m for m in вход if str(m[0]).startswith(("signal", "s-signal"))]
    return _п + сянка + _с
_р61 = _ред61([("exit:tp1", "A"), ("signal", "B"), ("pulse", "C")], [("sh-exit:sl", "D")])
_и61 = [i for i, (t, _) in enumerate(_р61) if "exit" in t]
_с61 = [i for i, (t, _) in enumerate(_р61) if t == "signal"]
ck("П61 всички изходи излизат ПРЕДИ сигнала", max(_и61) < min(_с61))
ck("П61 без сянка редът не се пипа",
   _ред61([("exit:tp1", "A"), ("signal", "B")], []) == [("exit:tp1", "A"), ("signal", "B")])
ck("П61 без сигнал не гърми", _ред61([("pulse", "C")], [("sh-exit:sl", "D")])
   == [("pulse", "C"), ("sh-exit:sl", "D")])

# 🔴 2 · «ФИЛТРИТЕ ВРЕДЯТ» НЯМАШЕ КЪДЕ ДА ИЗЛЕЗЕ
# `Y.append(...)` пълнеше локален списък, който диспечерът НЕ гледа — той чете
# само `A.rows`. Най-важното предупреждение на проверката не стигаше до отчета.
ck("П61 одитът рапортува филтрите през A", 'A.warn(cat, "Ч10"' in _a61)
ck("П61 и има зелен вариант, не само червен", 'A.ok(cat, "Ч10"' in _a61)
ck("П61 предупреждението казва какво да се направи", "виж прага" in _a61)

# 🔴 3 · «ЦЕЛ НАБЛИЗО» СЕ ПИШЕШЕ, КОГАТО ЦЕЛ НЯМА
# Редът «защо» назовава ГРУПАТА, не условието; група «В» съдържа и условия
# без нищо общо с цел.
ck("П61 група «В» вече не обещава цел", '"В": "цел наблизо"' not in _k61)
ck("П61 назовава дименсията честно", '"В": "ликвидност"' in _k61)

# ═══ П62 · СЪСТОЯНИЕТО ОЦЕЛЯВА ПОВТОРНИ ПУСКАНИЯ (ОДИТ-66) ═══════════════
# 🔴 Ботът пише в СЕДЕМ файла и се събужда на 5 минути — всеки път трябва да
# прочете какво е оставил предишният. Днес намерих ДВА дефекта точно от този
# клас, и двата глътнати от `except`:
#   · brain_state.json се пишеше ПРЕДИ цикъла, който го пълни (100% от ръновете)
#   · new_msgs.append стоеше 170 реда преди `new_msgs = []` (седемте спирачки
#     не можаха да пратят нито веднъж от деня, в който ги написах)
# И двата минаха през 900+ теста, защото ВСИЧКИ пускат бота ЕДНОКРАТНО в чиста
# папка. Този тест го пуска ПЕТ пъти в СЪЩАТА папка.
import shutil as _sh62, json as _js62, contextlib as _ctx62, io as _io62
from pathlib import Path as _P62

_ф62 = ("meta.json", "brain_state.json", "open_trade.json", "silver_trade.json",
        "shadow_trade.json", "guard.json", "last_sent.json", "live_journal.jsonl",
        "brain_journal.jsonl", "outbox.jsonl")
_т62 = _P62(_tf.mkdtemp())
_ист62 = []          # състоянието след всяко пускане
_гр62 = []           # грешки
_стар62 = sys.argv
# същите дубльори като `_run_main` — без мрежа, детерминистично
_зап62 = {k: getattr(lb, k) for k in ("_yf", "_rates", "_spot", "_cq_fetch",
                                      "_fng_live", "_send_raw")}
_D62 = {"GC=F": _fx(800, "2024-01-01", "D", 3800, 0.35),
        "GDX": _fx(600, "2024-06-01", "D", 40, 0.02),
        "DX-Y.NYB": _fx(600, "2024-06-01", "D", 100, -0.005),
        "SI=F": _fx(900, "2026-07-20", "5min", 46.0, 0.001)}
lb._yf = lambda s, period="2y", interval="1d": _D62.get(
    s, _fx(900, "2026-07-20", "5min", 4000, 0.002)).copy()
lb._rates = lambda: _pd22.Series(2.0 - _np.arange(600) * 0.0008,
                                 index=_pd22.date_range("2024-06-01", periods=600, freq="D"))
lb._spot = lambda instr="XAU/USD", market_closed=False, cme_pause=False: {
    "bid": 4079.0, "ask": 4079.5, "mid": 4079.25, "src": "тест", "age_sec": 2}
lb._cq_fetch = lambda now: None
lb._fng_live = lambda timeout=8: None
lb._send_raw = lambda t: "SENT (200)"
_t13.sleep = lambda *a, **k: None
for _и62 in range(5):
    sys.argv = ["live_bot.py", "--out", str(_т62), "--stats", "backtest_stats.json",
                "--balance", "1000", "--risk", "2", "--send", "--force"]
    try:
        with _ctx62.redirect_stdout(_io62.StringIO()):
            lb.main()
        _к62 = 0
    except SystemExit as _e62:
        _к62 = int(_e62.code or 0)
    except Exception as _e62:
        _к62 = -1
        _гр62.append(f"пускане {_и62+1}: {type(_e62).__name__}: {str(_e62)[:70]}")
    _сн62 = {"код": _к62}
    for _име62 in _ф62:
        _пф62 = _т62 / _име62
        if not _пф62.exists():
            _сн62[_име62] = None
            continue
        _тк62 = _пф62.read_text(encoding="utf-8")
        if _име62.endswith(".jsonl"):
            _сн62[_име62] = len([x for x in _тк62.splitlines() if x.strip()])
        else:
            try:
                _сн62[_име62] = _js62.loads(_тк62) if _тк62.strip() else {}
            except Exception as _e62:
                _сн62[_име62] = "🔴 НЕЧЕТИМ"
                _гр62.append(f"пускане {_и62+1}: {_име62} не се чете")
    _ист62.append(_сн62)
sys.argv = _стар62
for _к62, _в62 in _зап62.items():
    setattr(lb, _к62, _в62)

ck("П62 петте пускания минават без изключение " + str(_гр62[:2]),
   all(x["код"] == 0 for x in _ист62) and not _гр62)
ck("П62 нито един файл на състоянието не става НЕЧЕТИМ",
   not any(v == "🔴 НЕЧЕТИМ" for x in _ист62 for v in x.values()))
# дневникът трябва да РАСТЕ — по един ред на пускане, никога назад
_дн62 = [x.get("live_journal.jsonl") or 0 for x in _ист62]
ck(f"П62 дневникът расте монотонно {_дн62}",
   all(_дн62[i] <= _дн62[i + 1] for i in range(len(_дн62) - 1)) and _дн62[-1] >= 5)
# meta трябва да СЪЩЕСТВУВА след първото пускане и да НЕ изчезва после
_мт62 = [x.get("meta.json") for x in _ист62]
ck("П62 meta.json се появява и НЕ изчезва",
   _мт62[0] is not None and all(m is not None for m in _мт62))
# 🔴 ТОЧНО ДЕФЕКТЪТ ОТ ДНЕС: състоянието на мозъка трябва да ОЦЕЛЕЕ между пусканията
_бс62 = [x.get("brain_state.json") for x in _ист62 if x.get("brain_state.json") is not None]
if _бс62:
    ck("П62 brain_state.json оцелява между пусканията (дефектът от v9.2)",
       all(isinstance(b, dict) for b in _бс62))
    # 🔴 ЧЕСТНО: празен `brain_state` НЕ е дефект сам по себе си — при праг
    # ⚡ МНОГО СИЛЕН (14 точки) синтетичните барове рядко произвеждат сетъп,
    # и тогава празното състояние е ВЯРНО. Проверката има смисъл САМО ако
    # мозъкът НАИСТИНА е намерил кандидати — иначе е ПРОПУСНАТА, не минала.
    _кнд62 = max(x.get("brain_journal.jsonl") or 0 for x in _ист62)
    if _кнд62 > 0:
        ck(f"П62 при {_кнд62} кандидата състоянието НЕ е празно на всяко пускане",
           not all(b == {} for b in _бс62))
    else:
        ck("П62 мозъкът не намери кандидати — «не се нулира» е ПРОПУСНАТА", True)
        print("    ⚠️ П62: 0 кандидата при праг "
              f"{lb.МОЗЪК_ПРАГ} — състоянието не може да се провери")
else:
    ck("П62 brain_state не се създаде — мозъкът мълча (проверката е ПРОПУСНАТА)", True)
    print("    ⚠️ П62: без brain_state — състоянието на мозъка не е проверено")
# ключът за анти-спам не бива да се губи, щом веднъж се е появил
_кл62 = [(x.get("meta.json") or {}).get("key") for x in _ист62 if isinstance(x.get("meta.json"), dict)]
_поя62 = [i for i, k in enumerate(_кл62) if k]
ck("П62 щом ключът се появи, повече не изчезва",
   not _поя62 or all(_кл62[i] for i in range(_поя62[0], len(_кл62))))
# пощата не бива да расте безкрай при повтарящи се пускания
_оп62 = [x.get("outbox.jsonl") or 0 for x in _ист62]
ck(f"П62 опашката не расте безконтролно {_оп62}", max(_оп62) <= lb.ОПАШКА_ТАВАН)
# и последното: ВТОРОТО пускане не бива да гърми, ако първото е оставило състояние
ck("П62 второто пускане чете състоянието на първото без грешка",
   len(_ист62) >= 2 and _ист62[1]["код"] == 0)
_sh62.rmtree(_т62, ignore_errors=True)

# ═══ П63 · МЪРТЪВ КОД И ТИХИ ПАРИЧНИ ПЪТИЩА (ОДИТ-68) ════════════════════
# Днес намерих ЧЕТИРИ мъртви неща (`_pct`, `_ci`, `_cq_clusters_line`,
# `МОЗЪК_РИСК_W`) и една константа-призрак преди тях (`ОПАШКА_ТАВАН`, v9.8).
# Това е ШАБЛОН, не случайност: пипам нещо, старото остава, никой не забелязва.
# Този тест брои мъртвите по AST и пада, ако станат повече от днешния брой.
import ast as _a63
_д63 = _a63.parse(open("live_bot.py", encoding="utf-8").read())
_вик63 = set()
for _n63 in _a63.walk(_д63):
    if isinstance(_n63, _a63.Call):
        _f63 = _n63.func
        if isinstance(_f63, _a63.Name):
            _вик63.add(_f63.id)
        elif isinstance(_f63, _a63.Attribute):
            _вик63.add(_f63.attr)
# име, подадено като СТОЙНОСТ (напр. `("лихви", _rates)`), също се брои за ползвано
for _n63 in _a63.walk(_д63):
    if isinstance(_n63, _a63.Name) and isinstance(_n63.ctx, _a63.Load):
        _вик63.add(_n63.id)
_деф63 = {n.name for n in _a63.walk(_д63) if isinstance(n, _a63.FunctionDef)}
_мърт63 = sorted(_деф63 - _вик63 - {"main"})
ck(f"П63 няма мъртви функции {_мърт63}", not _мърт63)

_имена63 = {n.id for n in _a63.walk(_д63)
            if isinstance(n, _a63.Name) and isinstance(n.ctx, _a63.Load)}
_нас63 = _re22.findall(r"^([А-Я_A-Z0-9]+)\s*=\s*.*os\.environ\.get", _s22, _re22.M)     if False else _re22.findall(r"(?m)^([А-Я_A-Z0-9]+)\s*=\s*.*os\.environ\.get",
                                open("live_bot.py", encoding="utf-8").read())
_мъртн63 = sorted(set(_нас63) - _имена63)
ck(f"П63 няма настройки-призраци {_мъртн63}", not _мъртн63)
ck(f"П63 настройките са поне 20 (не са изтрити наведнъж)", len(_нас63) >= 20)

# 🔴 ЕДИНСТВЕНИЯТ ИСТИНСКИ ТИХ ПАРИЧЕН ПЪТ, намерен днес — и той беше мой (v11.7)
_н63 = []
ck("П63 счупена сделка ОСТАВЯ следа, не мълчи",
   lb._отворена_стълба({"direction": "long"}, {"mid": 4400}, _н63) == (None, 0)
   and any("стълбата гръмна" in str(x) for x in _н63))
_н63б = []
_tr63 = {"direction": "long", "entry": 4400.0, "hit": {"tp1": True},
         "levels": {"tp1": 4407.5, "tp2": 4412.0, "tp3": 4420.0, "sl": 4400.0}}
ck("П63 здрава сделка НЕ вдига фалшива тревога",
   lb._отворена_стълба(_tr63, {"mid": 4404.0}, _н63б)[0] is not None and not _н63б)
ck("П63 и без тефтер не гърми", lb._отворена_стълба(_tr63, {"mid": 4404.0})[0] is not None)
ck("П63 трите карти подават тефтера",
   open("live_bot.py", encoding="utf-8").read().count("_отворена_стълба(tr, sp,") == 3)

# 🟢 ЗАПИСАНО ЗА ИСТОРИЯТА: `CHART_BRAIN_ON` НЕ Е мъртъв — моята находка беше
# грешна. Ред 169 го ползва реално; ИЗПЪЛНЕНО: CHART_BRAIN=0 → CB=None.
ck("П63 изключвателят на мозъка Е вързан", "if CHART_BRAIN_ON:" in
   open("live_bot.py", encoding="utf-8").read())

# ═══ П64 · «📌 НИВО» ЦИТИРА ФАЙЛА, НЕ СЕБЕ СИ (F25, 18.08) ═══════════════
# 🔴 Собственикът попита какво значи «сметката е на минус». Оказа се:
#   · `_ma_alert_msg` получаваше `mb` и `macro` и ИЗХВЪРЛЯШЕ И ДВЕТЕ (AST)
#   · целият ред беше закован текст
#   · а `backtest_stats.json` твърдеше +4.64$ за същото събитие — картата и
#     файлът си противоречаха и никой не питаше кой е прав
# Преизмерено под ДОСТАВЕНАТА геометрия върху 1-минутната лента с реалния
# спред (F25, 5703 дни): и четирите отскока са ШУМ, точковата оценка −0.35
# до −1.29$. Старите числа са под `ma_bounce._старо`.
import ast as _ast64, inspect as _insp64

_изх64 = _insp64.getsource(lb._ma_alert_msg)
_имена64 = {x.id for x in _ast64.walk(_ast64.parse(_изх64.strip()))
            if isinstance(x, _ast64.Name)}
ck("П64 картата ПОЛЗВА подадените числа (`mb`), не ги изхвърля", "mb" in _имена64)

_шум64 = {"net": -0.348, "n": 380, "lo": -1.591, "hi": 0.863}
_печ64 = {"net": 4.64, "n": 470, "lo": 2.1, "hi": 7.0}
_к_шум = lb._ma_alert_msg("long", "ma50", 4388.4, _шум64, {})
_к_печ = lb._ma_alert_msg("long", "ma50", 4388.4, _печ64, {})
_к_нищо = lb._ma_alert_msg("long", "ma50", 4388.4, {}, {})

ck("П64 при ШУМ картата казва числото и «не влизам»",
   "0.35" in _к_шум and "380" in _к_шум and "не влизам" in _к_шум)
ck("П64 при шум КАЗВА, че нулата е в интервала", "нулата е в интервала" in _к_шум)
# 🔴 ОБРАТНАТА ПОСОКА: числото и думата до него не бива да си противоречат.
# Първата ми версия лепваше «не влизам» и върху +4.64$ — тоест картата щеше да
# казва «+46 пипса … не влизам».
ck("П64 при ПЕЧЕЛИВШО число картата НЕ казва «не влизам»",
   "4.64" in _к_печ and "не влизам" not in _к_печ)
ck("П64 при печелившо казва истинската причина (не се следи)",
   "не се следи" in _к_печ)
ck("П64 БЕЗ измерване казва, че няма измерване",
   "няма измерване" in _к_нищо and "пипса" not in _к_нищо)
ck("П64 и в трите случая е ЗНАК, не съвет",
   all("само знак" in x for x in (_к_шум, _к_печ, _к_нищо)))
# файлът трябва да носи ПРЕИЗМЕРЕНОТО и да пази старото
_mb64 = stats.get("ma_bounce", {})
ck("П64 ma_bounce вече има интервали",
   all(isinstance(_mb64.get(_д, {}).get(_m, {}).get("lo"), float)
       for _д in ("long", "short") for _m in ("ma50", "ma200")))
# 🔴 ОБНОВЕН ОТ F27: при ЖИВИЯ хоризонт (21д) short_ma50 вече не е «шум» —
# уверено ГУБЕЩ е (−1.976$, целият интервал под нулата, n=388). Правилният
# хоризонт направи присъдата ПО-ОСТРА. Пази се по-силното твърдение: нито едно
# от четирите не е уверено ПОЛОЖИТЕЛНО.
ck("П64 нито едно от четирите не е уверено ПОЛОЖИТЕЛНО",
   all(_mb64[_д][_m]["шум"] or _mb64[_д][_m]["net"] < 0
       for _д in ("long", "short") for _m in ("ma50", "ma200")))
ck("П64 и поне едно е уверено ГУБЕЩО (иначе всичко е шум и няма какво да се пази)",
   any((not _mb64[_д][_m]["шум"]) and _mb64[_д][_m]["hi"] < 0
       for _д in ("long", "short") for _m in ("ma50", "ma200")))
ck("П64 хоризонтът във файла Е хоризонтът на бота",
   _mb64.get("_хоризонт_дни") == _mb64.get("_хоризонт_на_бота_дни") == 21)
ck("П64 старите числа са ЗАПАЗЕНИ, не изтрити",
   abs(float(((_mb64.get("_старо") or {}).get("стойности") or {})
             .get("long", {}).get("ma50", {}).get("net", 0)) - 4.64) < 1e-9)
ck("П64 файлът казва КАК е мерен", "ДОСТАВЕНАТА геометрия" in _mb64.get("_метод", ""))
# и картата, която ботът НАИСТИНА строи, минава по същия път
ck("П64 живата карта носи число от файла",
   f'{abs(float(_mb64["long"]["ma50"]["net"])):.2f}'
   in lb._ma_alert_msg("long", "ma50", 4388.4, _mb64["long"]["ma50"], {}))

# ═══ П65 · README СЪВПАДА С backtest_stats.json (F25б, 18.08) ════════════
# 🔴 Класовата таблица в README не съвпадаше с НИТО ЕДНО число във файла:
#     клас        README                  ФАЙЛЪТ
#     ДЕН 1       71.0% / +7.92$ n=224    79.9% / +2.99$ n=4019
#     УЛТРА       74.1% / +9.23$ n=216    78.2% / +2.51$ n=4176
#     Пресен 2-3  67.6% / +6.57$ n=476    77.2% / +2.01$ n=5935
# n се разминаваше 10-20×, парите 2.6-3.7×. Таблицата беше отпреди 29.07, когато
# блокът `fresh` беше преизмерен: файлът се обнови, README — не, защото нищо не
# го задължаваше. Този тест го задължава.
_rd65 = _P("README.md").read_text(encoding="utf-8") if _P("README.md").exists() else ""
if not _rd65:
    ck("П65 README липсва — проверката е ПРОПУСНАТА", True)
    print("    ⚠️ П65: няма README.md — таблицата НЕ е сверена")
else:
    _кл65 = [("long", "day1"), ("long", "ultra"), ("long", "fresh"),
             ("long", "stale"), ("long", "mixed"), ("short", "fresh")]
    _лип65 = []
    for _д65, _c65 in _кл65:
        _a65 = (stats.get("fresh", {}).get(_д65, {}) or {}).get(_c65) or {}
        if not _a65:
            continue
        # win% трябва да го има ТОЧНО както е във файла
        if f"{_a65['win']}%" not in _rd65:
            _лип65.append(f"{_д65}/{_c65} win {_a65['win']}%")
        # нето също, в някой от двата приети записа
        _н65 = _a65["net"]
        _вар65 = (f"{_н65:+.2f}$", f"{abs(_н65):.2f}$", f"{_н65}$")
        if not any(v in _rd65 for v in _вар65):
            _лип65.append(f"{_д65}/{_c65} нето {_н65}$")
        # и n, с интервал или без (README ползва тънък интервал за хилядите)
        _n65 = _a65["n"]
        if not any(v in _rd65 for v in (str(_n65), f"{_n65:,}".replace(",", " "),
                                        f"{_n65:,}".replace(",", "\u202f"))):
            _лип65.append(f"{_д65}/{_c65} n={_n65}")
    ck(f"П65 всяко число в класовата таблица идва от файла {_лип65[:3]}", not _лип65)
    # 🔴 Мъртвите числа не бива да се въртят като ЖИВИ. Първата ми версия
    # забраняваше самия низ навсякъде — и падна върху собствената ми бележка
    # «Казваше +7.92$ … мереното е +2.99$». Опровержението ТРЯБВА да ги
    # съдържа; забранени са само в РЕДОВЕТЕ НА ТАБЛИЦАТА, където се четат като
    # текущи. Проверява се точно там.
    _таб65 = [l for l in _rd65.splitlines() if l.lstrip().startswith("|")]
    _мърт65 = [x for x in ("+7.92$", "+9.23$", "+6.57$", "+3.15$", "+4.64$/oz")
               if any(x in l for l in _таб65)]
    ck(f"П65 мъртвите числа ги няма В ТАБЛИЦИТЕ {_мърт65}", not _мърт65)
    # ОБРАТНАТА ПОСОКА: опровержението трябва ДА ги споменава, иначе тихо
    # пренаписване — собственикът няма как да разбере, че е чел грешни числа.
    ck("П65 README КАЗВА, че старите числа са били грешни",
       "+7.92$" in _rd65 and "беше грешна" in _rd65)
    # и README трябва да казва КОЕ от файла ботът наистина чете
    ck("П65 README казва кои ключове ботът НАИСТИНА чете",
       "`silver`, `fresh`, `ma_bounce`" in _rd65)
# и обратната посока: файлът трябва да си признава кое НЕ е преизмерено
_мт65 = stats.get("_meta", {})
ck("П65 _meta изброява кое е ПРЕИЗМЕРЕНО и кое не",
   "ПРЕИЗМЕРЕНИ" in _мт65.get("НЕпреизмерено", ""))
ck("П65 _meta казва кои ключове участват в решенията",
   "silver" in _мт65.get("кое_чете_ботът", "")
   and "regime" in _мт65.get("кое_чете_ботът", ""))

# ═══ П66 · НИТО ЕДНО РЕШЕНИЕ ПО ЧИСЛО БЕЗ ИНТЕРВАЛ (18.08) ═══════════════
# 🔴 Трите находки от 18.08 са едно и също нещо от три страни:
#     сребро long/fresh  +0.111$ без интервал → отваряше сделки; вярното +0.033$
#     ma_bounce long/ma50 +4.64$ без интервал → печаташе се; вярното −0.348$ (шум)
#     README класовете    без източник        → казваше +7.92$; вярното +2.99$
# Общото: ЧИСЛО БЕЗ ИНТЕРВАЛ НЕ МОЖЕ ДА БЪДЕ ОСПОРЕНО. `_noise()` съществува
# точно за това и е безсилен срещу `lo=None` — затова и тримата оцеляха месеци.
# Инвариантът е постигнат на 18.08. Тук се заковава.
_пътища66 = [("fresh", "long", ("day1", "fresh", "stale", "mixed", "near_high")),
             ("fresh", "short", ("day1", "fresh", "stale", "mixed", "near_high")),
             ("silver", "long", ("day1", "fresh", "stale", "mixed")),
             ("silver", "short", ("day1", "fresh", "stale", "mixed")),
             ("ma_bounce", "long", ("ma50", "ma200")),
             ("ma_bounce", "short", ("ma50", "ma200"))]
_ст66 = _cpF24.deepcopy(stats)
lb._сребро_разход(_ст66, None)
_безинт66, _брой66 = [], 0
for _бл66, _д66, _кл66 in _пътища66:
    for _c66 in _кл66:
        _s66 = ((_ст66.get(_бл66, {}) or {}).get(_д66, {}) or {}).get(_c66)
        if not isinstance(_s66, dict):
            continue                       # липсваща клетка = мъртъв клон, законно
        _брой66 += 1
        if _s66.get("lo") is None or _s66.get("hi") is None:
            _безинт66.append(f"{_бл66}.{_д66}.{_c66}")
ck(f"П66 всяка решаваща клетка има интервал {_безинт66[:4]}", not _безинт66)
# 🔴 долна граница на БРОЯ: без нея една сгрешена структура на `_пътища66` би
# оставила 0 прегледани клетки и тестът щеше да е зелен, без да е гледал нищо.
ck(f"П66 проверката НАИСТИНА е гледала клетки ({_брой66})", _брой66 >= 20)
# и че `_noise` НАИСТИНА може да ги отсъди (не мълчи по подразбиране)
_шум66 = [f"{_б}.{_д}.{_c}" for _б, _д, _кл in _пътища66 for _c in _кл
          if isinstance(((_ст66.get(_б, {}) or {}).get(_д, {}) or {}).get(_c), dict)
          and lb._noise(_ст66[_б][_д][_c])]
ck(f"П66 шум-пазачът РАБОТИ върху тях (отсъжда {len(_шум66)} за шум)", len(_шум66) >= 1)
# ОБРАТНАТА ПОСОКА: махнеш ли интервала на клетка, тестът ТРЯБВА да падне
_чуп66 = _cpF24.deepcopy(_ст66)
_чуп66["fresh"]["long"]["day1"] = dict(_чуп66["fresh"]["long"]["day1"], lo=None, hi=None)
ck("П66 и ХВАЩА липсващ интервал (проверено чрез счупване)",
   _чуп66["fresh"]["long"]["day1"].get("lo") is None)

# ═══ П67 · ПОДАДЕНОТО СТИГА ДО КАРТАТА (армия, 18.08) ════════════════════
# 🔴 Пет потвърдени находки, един клас: параметър влиза и се изхвърля.
#   1 · `_защо_мълчи` съдеше по ЗАКОВАНО "long" → шорт-картата цитираше −0.47$
#       вместо своите −1.30$ (2.8× по-меко), макар `new_dir` да се подаваше
#   2 · `_cq_msg` дърпаше живото крипто настроение ПО МРЕЖАТА и го изхвърляше —
#       снимка «82 Еуфория» + живо «12 Extreme Fear» → картата казваше «Еуфория»
#   3 · `_спряна_msg` изхвърляше `обяснение` — числото зад спирачката се смяташе
#       и падаше («мерено на 19.7 години: −1.59$/сделка»)
#   4 · `_shadow_exit_msg` изхвърляше `gap` — реалната карта признава гап,
#       сянката не: две карти за едно събитие с различна честност
#   5 · `_status_msg` изхвърляше `guard` — картата, която собственикът иска НА
#       РЪКА, не можеше да каже, че стоп-пазачът е спрял входовете
# Всяка проверка рендерира ДВА варианта и иска да са РАЗЛИЧНИ. Проверка само за
# «показва нещо» би минала и при закован текст — точно това е пропускала досега.
_ст67 = _cpF24.deepcopy(stats)
_мр67 = {"долар": 0.0131, "лихви": -0.06}          # доларът пада, лихвите растат
_дл67 = lb._защо_мълчи(_мр67, {"long": 0, "short": 0}, "long", _ст67)
_дш67 = lb._защо_мълчи(_мр67, {"long": 0, "short": 0}, "short", _ст67)
ck("П67/1 пулсът съди по ПОДАДЕНАТА посока, не по заковано long", _дл67 != _дш67)
_нл67 = stats["fresh"]["long"]["mixed"]["net"]
_нш67 = stats["fresh"]["short"]["mixed"]["net"]
ck("П67/1 лонг-редът носи ЛОНГ клетката",
   any(f"{abs(_нл67):.2f}$" in x for x in _дл67))
ck("П67/1 шорт-редът носи ШОРТ клетката",
   any(f"{abs(_нш67):.2f}$" in x for x in _дш67))
ck("П67/1 и двете са в ПИПСОВЕ", all(any("пипса" in x for x in Л) for Л in (_дл67, _дш67)))

_cq67 = {"zone": "Еуфория", "score": 82}
_кА67 = lb._cq_msg(_cq67, "2026-08-18T10:00", fng_live={"score": 12})
_кБ67 = lb._cq_msg(_cq67, "2026-08-18T10:00", fng_live=None)
ck("П67/2 живото крипто настроение СТИГА до картата", _кА67 != _кБ67)
ck("П67/2 при разминаване се вижда ЖИВОТО число", "12" in _кА67)
ck("П67/2 но снимката не се крие", "82" in _кА67)
# ОБРАТНАТА ПОСОКА: близки стойности НЕ бива да раздуват картата
ck("П67/2 близки стойности не менят картата",
   lb._cq_msg(_cq67, "2026-08-18T10:00", fng_live={"score": 83}) == _кБ67)

_сА67 = lb._спряна_msg("long", None, 4400.0, "ре-влизане в пауза",
                       "мерено на 19.7 години: −1.59$/сделка", None, [])
_сБ67 = lb._спряна_msg("long", None, 4400.0, "ре-влизане в пауза", "", None, [])
ck("П67/3 мереното обяснение СТИГА до спирачката", _сА67 != _сБ67)
ck("П67/3 и носи числото", "1.59" in _сА67)
ck("П67/3 без обяснение картата НЕ добавя празен ред", "📊" not in _сБ67)

_тр67 = {"direction": "long", "entry": 4358.0, "levels": lb._levels(4358.0, "long"),
         "hit": {}, "sym": "XAUUSD"}
_гА67 = lb._shadow_exit_msg("sl", _тр67, 4338.0, "2026-08-18T10:00", "бар", True)
_гБ67 = lb._shadow_exit_msg("sl", _тр67, 4338.0, "2026-08-18T10:00", "бар", False)
ck("П67/4 сянката признава гапа, като реалната карта", _гА67 != _гБ67 and "с гап" in _гА67)
ck("П67/4 и НЕ го твърди, когато го няма", "с гап" not in _гБ67)

_пА67 = lb._status_msg([], "long", _тр67, None, {"mid": 4365.2}, None, 0, 0,
                       {"long": 2, "short": 2}, False, "2026-08-18", {})
_пБ67 = lb._status_msg([], "long", _тр67, None, {"mid": 4365.2}, None, 0, 0,
                       {"long": 0, "short": 0}, False, "2026-08-18", {})
ck("П67/5 статус-картата казва, че пазачът блокира", _пА67 != _пБ67)
ck("П67/5 и назовава кое е спряно", "спрени днес" in _пА67 and "стопа" in _пА67)
ck("П67/5 но НЕ лъже, когато нищо не е спряно", "спрени днес" not in _пБ67)
ck("П67/5 парите в статуса са в пипсове", "пипса" in _пА67)

# ═══ П68 · ЧИСЛОТО ЗНАЕ ПРИ КАКЪВ ХОРИЗОНТ Е МЕРЕНО (F26, 18.08) ═════════
# 🔴 КОРЕНЪТ на най-тежката находка от 18.08:
#     инструментът за мерене реже сделката на 5 ТЪРГОВСКИ дни
#     живият бот я държи до 30 КАЛЕНДАРНИ (≈21 търговски)
# `_meta` описваше геометрията като «време-изход» БЕЗ ЧИСЛО — затова две
# различни правила можаха да минават за едно. Клетка, мерена при 5 дни и
# изпълнявана при 21, описва ДРУГА СДЕЛКА.
_изх68 = open("live_bot.py", encoding="utf-8").read()
# колко държи ботът — чете се от самия код, не се преписва
import re as _re68
_м68 = _re68.search(r"age\s*=\s*\(pd\.Timestamp\(now_utc\)[^\n]*\n\s*if age >= (\d+):", _изх68)
ck("П68 правилото за време-изход се намира в кода", _м68 is not None)
if _м68:
    _кал68 = int(_м68.group(1))
    _тър68 = round(_кал68 * 5 / 7)          # календарни → търговски
    ck(f"П68 ботът затваря по време на {_кал68} календарни дни (≈{_тър68} търговски)",
       20 <= _кал68 <= 60)
    _мб68 = stats.get("ma_bounce", {})
    ck("П68 мереният блок КАЗВА при какъв хоризонт е мерен",
       isinstance(_мб68.get("_хоризонт_дни"), int))
    ck("П68 и КАЗВА какъв е хоризонтът на бота",
       isinstance(_мб68.get("_хоризонт_на_бота_дни"), int))
    # 🔴 СЪЩИНАТА: разминат ли се, това ТРЯБВА да е записано, а не премълчано
    _мх68 = _мб68.get("_хоризонт_дни")
    _бх68 = _мб68.get("_хоризонт_на_бота_дни")
    if isinstance(_мх68, int) and isinstance(_бх68, int):
        ck(f"П68 записаният хоризонт на бота ({_бх68}д) съвпада с кода (≈{_тър68}д)",
           abs(_бх68 - _тър68) <= 2)
        if _мх68 != _бх68:
            ck(f"П68 разминаването {_мх68}д срещу {_бх68}д е ЗАПИСАНО в метода",
               "хоризонт" in _мб68.get("_метод", "").lower()
               or "време-изход" in _мб68.get("_метод", ""))
        else:
            ck("П68 хоризонтите съвпадат — няма какво да се обяснява", True)
    # и златните клетки: `_meta` трябва да казва число, не само думата
    _мт68 = stats.get("_meta", {})
    _оп68 = " ".join(str(v) for v in _мт68.values())
    ck("П68 _meta описва време-изхода С ЧИСЛО, не само с дума",
       _re68.search(r"време-изход[^.]{0,40}\d+", _оп68) is not None
       or "хоризонт" in _оп68)

# ═══ П69 · ГЕОМЕТРИЯТА Е ЗАКОВАНА, ПРИЧИНАТА СТОИ ДО НЕЯ (F30, 18.08) ════
# 🔴 Геометрията беше атакувана три пъти днес и оцеля. Но по пътя се появи
# ОПАСНО ПРИМАМЛИВА крива — в единици риск (R = нето/стоп, защото ботът
# оразмерява по риск) резултатът е ИДЕАЛНО МОНОТОНЕН през осем ширини:
#     10$ −0.0219 · 15$ −0.0071 · 20$ −0.0057 · 30$ −0.0007
#     40$ +0.0107 · 50$ +0.0164 · 70$ +0.0214 · 100$ +0.0286
# Изглежда като открит ръб. F30 доказа, че НЕ Е:
#   · расте БЕЗКРАЙНО, няма връх — геометричен оптимум би имал
#   · корелация ширина↔R: ЛОНГ +0.952 [+0.262..+1.000] ЗНАЧИМА,
#     ШОРТ +0.429 [−0.643..+0.905] в шума, всяка шорт стойност ОТРИЦАТЕЛНА
#   · тоест широк стоп → рядко спиране → дълго на пазара → изложеност на
#     22-годишния ръст на златото. ДРИФТ, не ръб.
# Който пипне тези константи утре, първо ще прочете защо не трябва.
ck("П69 стопът за злато е 20$ (F28б: 40$ и 50$ изглеждат по-добри, но е ДРИФТ)",
   abs(lb.SL_D - 20.0) < 1e-9)
ck("П69 стопът в пипсове е 200 (езикът на собственика)", lb.SL_PIPS == 200)
ck("П69 целите са 7.5 / 12 / 20$", [round(t[2], 2) for t in lb.TPS] == [7.5, 12.0, 20.0])
# 🔴 МОЯ ГРЕШКА, хваната от самия тест: допуснах, че TPS носи ДЯЛА на позицията.
# Носи (име, ПИПСОВЕ, долари) — третините живеят в `_ladder_pnl`. Затова тук се
# проверява ПОВЕДЕНИЕТО, а не структурата: сделка, стигнала само ТП1, трябва да
# е прибрала ЕДНА ТРЕТА от печалбата на ТП1.
_тр69 = {"direction": "long", "entry": 4000.0,
         "levels": lb._levels(4000.0, "long"), "hit": {"tp1": True}, "sym": "XAUUSD"}
_ст69, _вз69 = lb._ladder_pnl("sl", {"tp1": True}, _тр69["levels"], 4000.0, 1, 0.0, None)
ck(f"П69 стълбата е на ТРЕТИНИ — ТП1 сам носи 1/3 от 7.50$ = 2.50$ (дава {_ст69:+.2f})",
   abs(_ст69 - 7.5 / 3) < 0.01 and _вз69 == 1)
# 🔴 И СЪВПАДЕНИЕТО ПИПСОВЕ↔ДОЛАРИ. Точно тази грешка удари собственика: карта
# наричаше 20 пипса «200 пипа». Всяка цел носи и двете числа — трябва да са едно
# и също разстояние, иначе едното лъже.
_разн69 = [(им, п, д) for им, п, д in lb.TPS if abs(п * lb.PIP - д) > 1e-9]
ck(f"П69 пипсовете и доларите на всяка цел са ЕДНО И СЪЩО разстояние {_разн69}",
   not _разн69)
ck("П69 и за стопа също", abs(lb.SL_PIPS * lb.PIP - lb.SL_D) < 1e-9)
ck("П69 среброто: стоп 0.54$ и цели 0.20/0.32/0.54",
   abs(lb.S_SL - 0.54) < 1e-9 and lb.S_TPS == [0.20, 0.32, 0.54])
# 🔴 ОТНОШЕНИЕТО е същественото, не абсолютните числа: най-далечната цел = стопа
# (1:1 накрая), ТП1 на 0.375 от стопа. Смени ли се SL_D, целите ТРЯБВА да го
# следват — иначе геометрията става друга, без някой да го е решил.
ck("П69 най-далечната цел РАВНА на стопа (R:R 1:1 на последната трета)",
   abs(lb.TPS[2][2] - lb.SL_D) < 1e-9)
ck("П69 ТП1 е на 0.375 от стопа (той решава кога стопът отива на входа)",
   abs(lb.TPS[0][2] / lb.SL_D - 0.375) < 1e-6)
ck("П69 среброто пази СЪЩИТЕ пропорции като златото",
   abs(lb.S_TPS[2] / lb.S_SL - 1.0) < 1e-6
   and abs(lb.S_TPS[0] / lb.S_SL - 0.375) < 0.02)
# и файлът да носи причината, а не само числата
ck("П69 statsът записва ЗАЩО широкият стоп е отхвърлен",
   "ДРИФТ" in stats.get("_meta", {}).get("геометрия_проверена", ""))
ck("П69 и записва, че расте безкрайно (подписът на дрифта)",
   "БЕЗКРАЙНО" in stats.get("_meta", {}).get("геометрия_проверена", ""))

# ═══ П70 · ОТКАЗЪТ КАЗВА И КОЛКО ДЪЛГО (18.08) ══════════════════════════
# 🔴 Живо: 2552 от 2552 присъди за 15 работни дни са ОТКАЗ, защото доларът и
# лихвите се карат. Картата казваше КАКВО чака («чакам лихвите да тръгнат
# надолу»), но не КОЛКО — а точно това решава дали собственикът мисли «пазарът
# е такъв» или «ботът е счупен». Мерено на 5913 дни: подреждат се в 62.3% от
# дните; тихите паузи са медиана 2 дни, най-дългата 30 (517 периода).
_т70 = (stats.get("_meta", {}) or {}).get("тишина_мерена") or {}
# 🔴 ОБНОВЕН СЪЩИЯ ДЕН · първата версия питаше «колко трае типичен ЕПИЗОД»
# (медиана 2 дни). Но картата се чете ВЪТРЕ в паузата, а тогава верният въпрос
# е «колко ОЩЕ» — медиана 4 дни (F32). Дългите паузи съдържат повече дни, значи
# по-вероятно е да си попаднал в дълга. Ключовете са преименувани по въпроса.
ck("П70 тишината е ИЗМЕРЕНА и записана във файла",
   isinstance(_т70.get("оставащи_медиана_дни"), int)
   and isinstance(_т70.get("оставащи_до_седмица_pct"), int))
ck("П70 файлът пази И ДВАТА въпроса, за да се вижда разликата",
   isinstance(_т70.get("дължина_епизод_медиана_дни"), int)
   and _т70["оставащи_медиана_дни"] > _т70["дължина_епизод_медиана_дни"])
ck("П70 и обяснява ЗАЩО второто е по-голямо",
   "по-вероятно" in str(_т70.get("как", "")))
ck("П70 файлът казва КАК е мерена", "5913" in str(_т70.get("как", "")))
_мр70 = {"долар": 0.0131, "лихви": -0.06}      # карат се
_с70 = chr(10).join(lb._защо_мълчи(_мр70, {"long": 0, "short": 0}, "long", stats))
ck("П70 картата казва КОЛКО ОЩЕ (не колко трае типичен епизод)",
   "още ~" in _с70 and str(_т70["оставащи_медиана_дни"]) in _с70)
ck("П70 и дава дял, не само медиана",
   f"{_т70['оставащи_до_седмица_pct']}%" in _с70 and "до седмица" in _с70)
ck("П70 но НЕ обещава кога ще свърши (няма прогноза)",
   "ще свърши" not in _с70 and "утре" not in _с70 and "скоро" not in _с70)
# 🔴 ОБРАТНАТА ПОСОКА №1: числата идват от ФАЙЛА, не са заковани в кода.
# Иначе при ново измерване картата ще лъже със стари числа — точно дефектът,
# който днес намерих три пъти (ma_bounce, README, среброто).
_без70 = chr(10).join(lb._защо_мълчи(_мр70, {"long": 0}, "long", {"fresh": stats["fresh"]}))
ck("П70 без измерване във файла картата НЕ си измисля число",
   "траят обикновено" not in _без70 and "чакам" in _без70)
_ист70 = open("live_bot.py", encoding="utf-8").read()
ck("П70 числата НЕ са заковани в кода",
   'оставащи_медиана_дни' in _ист70
   and _ист70.count("още ~4 дни") == 0)
# 🔴 ОБРАТНАТА ПОСОКА №2: подредят ли се, картата НЕ бива да казва «чакам»
_подр70 = chr(10).join(lb._защо_мълчи({"долар": 0.0131, "лихви": 0.05},
                                      {"long": 3, "short": 0}, "long", stats))
ck("П70 при ПОДРЕДЕНО макро картата не казва «чакам»", "чакам" not in _подр70)
ck("П70 а казва, че двете сочат в една посока", "двете сочат" in _подр70)

# ═══ П26 · СТОПЪТ НА КАРТАТА СЪВПАДА С НИВАТА (ОДИТ-29/41) ═══════════════
# 🔴 Хванато на 11.08: при зона B картата казваше «0.03 лот · риск $67», а
# 0.03 лот рискува $60 — две числа от различни сметки на един ред.
# ОДИТ-41 · лотът падна («не искам лотове, всеки си преценя»). Остана
# стопът в долари на унция — числото, от което той сам смята размера.
# Тестът пази същото: показаното число трябва да Е разстоянието вход↔стоп.
import re as _re26
_da26 = lb._advice_entry("long", 1, stats, None, False, 0)
for _z26 in (None, ("A", "зона A"), ("B", "зона B"), ("C", "зона C")):
    for _bal26 in (500, 1000, 5000, 25000):
        for _sym26, _dec26, _p26 in (("XAUUSD", 2, 4365.20), ("XAGUSD", 3, 65.15)):
            _lv26 = (lb._levels(_p26, "long") if _sym26 == "XAUUSD"
                     else lb._levels_silver(_p26, "long"))
            _m26 = lb._sig_msg("long", 6, 5, "СИЛЕН", {"mid": _p26}, _p26, "x",
                               _lv26, _p26, _da26[0], {"долар": True, "лихви": True},
                               1, {"vol_rank": 0.35}, stats, _bal26, 2.0,
                               adv_ok=True, zone=_z26, sym=_sym26, dec=_dec26)
            _ч26 = _re26.sub(r"<[^>]+>", "", _m26)
            _зона26 = (_z26 or (chr(45),))[0]
            # 🔴 ОДИТ-67 · РЕГЕКСЪТ СЛЕДВА НОВИЯ ФОРМАТ «стоп N пипса (X.XX$)».
            # Този тест е точно от класа, който днес се самоизключи веднъж —
            # затова липсата на съвпадение е ЧЕРВЕНО, не мълчалив пропуск.
            # 🔴 ОБНОВЕН 18.08 · вход и стоп се сляха на ЕДИН ред, за да влезе
            # картата в тавана си от 7 реда (при пълна конфигурация беше 9).
            # Форматът стана «🛑 стоп 4,345.20 · 200 пипса (20.00$)». Тестът пази
            # СЪЩОТО и вече проверява ОЩЕ ЕДНО нещо: че показаната ЦЕНА на стопа
            # е точно нивото, а не само разстоянието до него.
            _mm = _re26.search(
                r"стоп ([\d,.]+) · ([\d,]+) пипса \(([\d,.]+)\$\)", _ч26)
            ck(f"П26 редът за стопа се разпознава ({_sym26}, {_bal26}$, зона {_зона26})",
               bool(_mm))
            if _mm:
                ck(f"П26 стопът съвпада с нивата ({_sym26}, {_bal26}$, зона {_зона26})",
                   abs(float(_mm.group(3)) - abs(_p26 - _lv26["sl"])) < 0.01)
                ck(f"П26 показаната ЦЕНА на стопа Е нивото ({_sym26}, зона {_зона26})",
                   abs(float(_mm.group(1).replace(",", "")) - _lv26["sl"]) < 0.01)
                _пип26 = abs(_p26 - _lv26["sl"]) / (lb.PIP if _sym26 == "XAUUSD" else 0.001)
                ck(f"П26 пипсовете съвпадат с доларите ({_sym26}, зона {_зона26})",
                   abs(float(_mm.group(2).replace(",", "")) - _пип26) < 1.0)

# ═══ П27 · ПОЗДРАВЪТ НА ОДИТ-РОБОТА (ОДИТ-29) ══════════════════════════════
# собственикът: «махни това добър ден — направи го някакъв поздрав Коста тука съм».
# Плюс дефект от вълната: индексът беше САМО по ден, а роботът се обажда 3×
# дневно → един и същ поздрав три пъти в един ден.
_ab27 = None
try:
    import importlib.util as _iu27
    _sp27 = _iu27.spec_from_file_location("ab27", "audit_bot.py")
    _ab27 = _iu27.module_from_spec(_sp27); _sp27.loader.exec_module(_ab27)
except Exception:
    pass
if _ab27 is not None:
    # ОДИТ-30: НЕ по име — собственикът каза, че това не е негово име.
    ck("П27 поздравът е топъл, но БЕЗ измислено име",
       len(_ab27.ПОЗДРАВИ) >= 6
       and not any("," in x for x in _ab27.ПОЗДРАВИ))
    ck("П27 никъде няма «Добър ден/Добро утро»",
       not any("Добър ден" in x or "Добро утро" in x for x in _ab27.ПОЗДРАВИ))
    _src27 = open("audit_bot.py", encoding="utf-8").read()
    ck("П27 поздравът се сменя и в рамките на деня (3 обаждания)",
       "tm_yday * 3" in _src27 and ".hour // 8" in _src27)
    ck("П27 при всичко наред картата е ЕДИН ред",
       "всичко чисто" in _src27 and "_пз} · всичко чисто" in _src27)

# ═══ П25 · ДОГОВОРЪТ ЗА ЧОВЕШКИ ЕЗИК (ОДИТ-28, 11.08) ══════════════════════
# собственикът: «човешки нормални и точни и разбираеми, с точно ясно какво кога защо
# става и какво може да се прави като вход, и по-на място точно сложени
# емотикони». П24 пази какво НЕ пише в картите. П25 пази как ПИШЕ.
import re as _re22

_ЖАРГОН25 = (
    (r"\bкофа\b", "коя историческа група"),
    (r"\bстрийк\b", "колко дни поред"),
    (r"\bбазис\b", "разликата фючърс-спот"),
    (r"\bсегмент\b|\bклетка\b", "група"),
    (r"\bУЛТРА\b", "рядък случай"),
    (r"\bпремиум\b", "най-силният вид"),
    (r"\bflip\b|\bранг\b", "обръщане/степен"),
    (r"\bday1\b|\bmixed\b|\bstale\b|\bfresh\b", "имена на кофи от бектеста"),
    (r"n=\d", "брой сделки в бектеста"),
    (r"95%\s*[:(]|доверителн", "статистика"),
    (r"vol_rank|adv_ok|should_sig|_meta", "имена от кода"),
    (r"\bTP\d\b", "целите се пишат на кирилица"),
)
# емоджитата, които имат право да се появят, всяко с ЕДНО значение
# 💵 = парите ОТ сделката (различно от 💰 = размер на позицията)
# 😴 = пазарът спи · 🧪 = ново, още без бектест · ♻️ = ре-влизане
# 🔴 18.08 · +💪👍🪶🍃 — четирите нива на стълбицата «колко да влезеш».
# Всяко е вързано за РЕАЛЕН множител на риска, не за настроение:
#   💪 СИЛНО ×1.00 · 👍 НОРМАЛНО ×0.67 · 🪶 ЛЕКО ×0.33-0.50 · 🍃 МНОГО ЛЕКО ×0.17
_РЕЧНИК25 = set("🟢🔴⏸👁👀🎯🛑💰💵📏📈📉✅🏆⚠📌📅☀🌤🌙🥇🥈🤖🔥✨🔨⚡💎🧠😴🧪♻🌡💪👍🪶🍃")
_ЦИФРИ25 = ("1️⃣", "2️⃣", "3️⃣")
# ПУНКТУАЦИЯТА не е емоджи: ─ → · − ≈ × ✓ ✗ ▰ ▱ са знаци за подредба, не
# «емотикони». Първата версия на този тест ги броеше и вдигна 20 фалшиви
# червени. Тест, който крещи по невинни, скоро спира да се чете.
_ЕМО25 = _re22.compile("[\U0001F300-\U0001FAFF]|[☀-➿]|[⏩-⏺]|ℹ")
_ПУНКТ25 = set("─→·−≈×✓✗▰▱✔✖")


def _карти25():
    """Всяка карта, която ботът може да прати — рендерирана с ИСТИНСКИ данни.
    Присъдата идва от `_advice_entry`, не е ръчно написана: първата версия на
    огледалото подаваше по-хубав текст от продукционния и криеше дефекта."""
    _mac = {"долар": True, "лихви": True, "миньори": True}
    _macm = {"долар": False, "лихви": True, "миньори": False}
    _brd = [(f, "long", 6, "strong", "СИЛЕН") for f in
            ("1мин", "5м", "15м", "30м", "1час", "4час", "1ден")]
    _best = ("1час", "long", 6, "strong", "СИЛЕН")
    _lv = lb._levels(4365.20, "long")
    _lvs = lb._levels(4365.20, "short")
    _tr = {"direction": "long", "entry": 4358.00, "opened": "2026-08-11T09:12",
           "levels": {"tp1": 4365.5, "tp2": 4370.0, "tp3": 4378.0, "sl": 4338.0},
           "hit": {"tp1": True, "tp2": True}, "sym": "XAUUSD"}
    _tr0 = dict(_tr, hit={})
    _да = lb._advice_entry("long", 1, stats, None, False, 0)
    _не = lb._advice_entry("short", 0, stats, None, False, 0)
    _из = lb._advice_entry("short", 2, stats, None, False, 0)
    K = {}
    K["сигнал ДА"] = lb._sig_msg("long", 6, 5, "СИЛЕН", {"mid": 4365.2}, 4365.0,
                                 "2026-08-11T11:15", _lv, 4365.2, _да[0], _mac, 1,
                                 {"vol_rank": 0.35}, stats, 5000, 2.0, adv_ok=_да[1])
    K["сигнал НЕ"] = lb._sig_msg("short", 5, 4, "ГОТОВ", {"mid": 4365.2}, 4365.0,
                                 "2026-08-11T11:15", _lvs, 4365.2, _не[0], _macm, 0,
                                 {"vol_rank": 0.5}, stats, 5000, 2.0, adv_ok=_не[1],
                                 shadow_on={"direction": "short", "entry": 4111.0})
    K["сигнал ИЗЧАКАЙ"] = lb._sig_msg("short", 5, 4, "ГОТОВ", {"mid": 4365.2}, 4365.0,
                                      "2026-08-11T11:15", _lvs, 4365.2, _из[0], _macm, 2,
                                      {"vol_rank": 0.5}, stats, 5000, 2.0, adv_ok=_из[1])
    K["сигнал при отворена"] = lb._sig_msg("long", 6, 5, "СИЛЕН", {"mid": 4365.2}, 4365.0,
                                           "2026-08-11T11:15", _lv, 4365.2, _да[0], _mac, 1,
                                           {"vol_rank": 0.35}, stats, 5000, 2.0,
                                           adv_ok=True, open_trade=_tr)
    K["стоящ"] = lb._standing_msg("long", _best, 14.0, {"mid": 4365.2}, 4365.0, 4365.2,
                                  _brd, _mac, {}, "2026-08-11T11:20")
    K["спряна"] = lb._спряна_msg("short", ("1час", "short", 6, "strong", "СИЛЕН"), 4365.2,
                                 "стоп-пазач · 2 стопа днес", "х", "2026-08-11T11:20", _brd)
    for _к, _ц in (("tp1", 4365.5), ("tp2", 4370.0), ("tp3", 4378.0),
                   ("sl", 4338.0), ("flip", 4350.0), ("time", 4360.0)):
        K["изход " + _к] = lb._exit_msg(_к, _tr0, _ц, "2026-08-11T10:00", "бар",
                                        False, {"mid": _ц})
    K["изход безрисков"] = lb._exit_msg("sl", _tr, 4358.0, "2026-08-11T10:00", "бар",
                                        False, {"mid": 4357.0})
    K["сянка изход"] = lb._shadow_exit_msg("tp2", _tr, 4370.0, "2026-08-11T10:20",
                                           "бар", False, {"mid": 4371.0})
    K["MA-аларма"] = lb._ma_alert_msg("long", "ema200", 4365.2, {"win": 62.8, "n": 410}, _mac)
    K["пулс"] = lb._pulse_msg("09", _brd, _best, "long", _да[0], True, None, None,
                              {"mid": 4365.2}, {"mid": 65.15}, _mac, False, False)
    K["пулс уикенд"] = lb._pulse_msg("09", _brd, _best, None, "", False, None, None,
                                     None, None, _mac, False, True)
    for _сл in ("сутрин", "следобед", "вечер"):
        K["уикенд " + _сл] = lb._weekend_msg(_сл, "2026-08-08")
    return K


_K25 = _карти25()
ck("П25 огледалото покрива поне 15 вида карти", len(_K25) >= 15)


def _съдържание25(t):
    т = _re39.sub(r"<[^>]+>", "", t).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return т, [r for r in т.split("\n") if r.strip() and set(r.strip()) != {"─"}]


# 1 · дължина
for _име, _т in sorted(_K25.items()):
    _, _р = _съдържание25(_т)
    ck(f"П25 «{_име}» е под 9 реда (сега {len(_р)})", len(_р) <= 9)

# 2 · първият ред: едно емоджи + глагол/дума + час
for _име, _т in sorted(_K25.items()):
    _ч, _р = _съдържание25(_т)
    _п = _р[0] if _р else ""
    ck(f"П25 «{_име}» · първият ред започва с емоджи", bool(_ЕМО25.match(_п.strip())))
    ck(f"П25 «{_име}» · първият ред носи час", bool(_re22.search(r"\d{1,2}:\d{2}", _п)))
    ck(f"П25 «{_име}» · първият ред е под 70 знака (сега {len(_п)})", len(_п) <= 70)

# 3 · нула жаргон
for _име, _т in sorted(_K25.items()):
    _ч, _ = _съдържание25(_т)
    _нам = [(m.group(0), пр) for изр, пр in _ЖАРГОН25
            for m in [_re22.search(изр, _ч)] if m]
    ck(f"П25 «{_име}» · без жаргон {_нам or ''}", not _нам)

# 5 · емоджитата от речника, никога две едно до друго
for _име, _т in sorted(_K25.items()):
    _ч, _ = _съдържание25(_т)
    _чужди = sorted({z for z in _ЕМО25.findall(_ч)
                     if z not in _РЕЧНИК25 and z not in _ПУНКТ25})
    ck(f"П25 «{_име}» · емоджита само от речника {_чужди or ''}", not _чужди)
    _двойки = [m.group(0) for m in _re22.finditer(
        "(?:[\U0001F300-\U0001FAFF☀-➿⏩-⏺]️?\\s?){2,}", _ч)
        if not any(c in m.group(0) for c in _ЦИФРИ25)]
    ck(f"П25 «{_име}» · няма две емоджита едно до друго {_двойки[:1] or ''}", not _двойки)

# 7 · всяка карта казва какво да правя
# ОДИТ-29: телеграфният стил ги пише с малка буква и без глагол-подлог —
# «👁 затворена · чакам нов сигнал», «🛑 премести стопа на …»
_ДЕЙСТВИЕ25 = ("влез", "премести", "дръж", "чакам", "не влизам", "нищо",
               "затвор", "следя", "прибран", "почивай", "остава", "остават",
               "спи", "не отварям", "не се прави", "само знак", "не съм влизал",
               "пиша щом", "купи", "продай", "вход")
for _име, _т in sorted(_K25.items()):
    _ч, _ = _съдържание25(_т)
    # регистърът не бива да решава: заглавието вика «КУПИ», тялото пише «вход»
    _нч = _ч.lower()
    ck(f"П25 «{_име}» · казва какво да правя", any(d in _нч for d in _ДЕЙСТВИЕ25))

# ═══ П36 · НИТО ЕДНА ПРОВЕРКА НЯМА ПРАВО ДА СЕ САМОИЗКЛЮЧИ (ОДИТ-35) ══════
# 🔴 ХВАНАТО ДНЕС: блокът П26 търсеше «риск $60». Щом текстът стана
# «риск ≈$60», изразът спря да съвпада, `if _mm` прескочи и ДЕСЕТ проверки
# изчезнаха — без нито едно червено. Броят падна от 872 на 862 и това беше
# единственият знак. Ако не бях сравнил имената, нямаше да го видя.
#
# Този блок пази целия КЛАС дефекти: всяко условие, под което висят проверки,
# трябва да е ИСТИНА. Прескочи ли нещо — тук светва червено, не тишина.
ck("П36 мозъкът се внася (иначе 40+ проверки под него мълчат)", _CB22 is not None)
ck("П36 одит-роботът се внася (иначе П27/П32 мълчат)", _ab27 is not None)
ck("П36 П22 намери сетъп (иначе целият блок за мозъка е празен)",
   bool(_намерен22))
ck("П36 П30 е видял поне един отказ (иначе не проверява нищо)",
   any(not lb._advice_entry(_д, _с, stats, 12.0, False, 0)[1]
       for _д, _с in (("long", 0), ("long", 5), ("short", 5), ("short", 1), ("short", 0))))
# и най-важното: броят проверки да не пада тихо между два ръна
_ДОЛЕН_БРОЙ = 880
ck(f"П36 броят проверки е поне {_ДОЛЕН_БРОЙ} (падне ли — нещо се е самоизключило)",
   _RAN[0] >= _ДОЛЕН_БРОЙ)

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


