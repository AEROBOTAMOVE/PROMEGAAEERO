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
   and "КИБЕР КВАНТ" in _cqm and "&" not in _cqm.replace("&amp;", "") and "FOMC" in _cqm)   # П9: преименувана
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
ck("L2-01 изходите включват трите семейства", set(lb.EXIT_TAGS) == {"exit", "s-exit", "sh-exit"})
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
   "🛑 стоп" in _stm and _stm.count("️⃣") == 3)
ck("О5 стоящата карта пак казва, че НЕ Е ПОКАНА за вход",
   "не покана" in _stm or "НЕ Е ВХОД" in _stm)
ck("О5 стоящата карта казва ИЗМЕРЕНОТО за късните входове",
   "12 часа" in _stm and "1.59" in _stm)
ck("О5 стоящата карта показва възрастта", "27 часа" in _stm)
_stm2 = lb._standing_msg("short", ("1час", "short", 7, "strong", "СИЛЕН"), 20.0, None, 4006.0, 4000.2,
                         [("1час", "short", 7, "strong", "СИЛЕН")] * 7,
                         {"миньори": False, "долар": False, "лихви": False}, {"мъртви": ["долар"]}, "2026-07-29T10:00")
ck("О5 стоящата карта предупреждава за мъртъв фийд", "макро-краче" in _stm2 and "мълчи" in _stm2)
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
ck("О6 затворен пазар пак не ползва крипто-прокси", "if market_closed:" in _spotsrc)

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
ck("О7 среброто НЕ е пипано", _bs["silver"]["long"]["fresh"]["net"] == 0.111)
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
ck("burst: 1/3 сметка вярна при ТП1+ТП2+СТОП в 1 рън",     # ОДИТ-7: текстът е пренаписан
   "+6.50$/oz" in _em and "TP1, TP2" in _em                # числото и кои ТП — както преди
   and "БЕЗРИСКОВ ИЗХОД" in _em.split("\n")[0]             # + вече не се нарича «СТОП»
   and "Стопът НЕ е ударен" in _em)                        # + казва го изрично

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
   "_ladder_pnl(kind, hit, lv, e, sign, dol)" in _src.split("def _shadow_exit_msg")[0].split("def _exit_msg")[1])

# --- сянка-картата вече показва сметката ---
_sh1 = lb._shadow_exit_msg("sl", _shtr({"tp1": True, "tp2": True}), _E, "2026-08-03T03:01:00", "бар", False)
ck("П7 сянка-стоп след 2 ТП показва +6.50$", "+6.50$/oz" in _sh1)
ck("П7 сянка-стоп след 2 ТП НЕ се води загуба (без 🛑)", "🛑" not in _sh1.split("\n")[0])
ck("П7 сянка-стоп след 2 ТП казва «безрисков изход»", "безрисков изход" in _sh1)
ck("П7 сянка-картата казва кои ТП са прибрани", "TP1" in _sh1 and "TP2" in _sh1)
ck("П7 сянка-картата пак показва голия крак, но етикетиран", "само този крак" in _sh1)
_sh2 = lb._shadow_exit_msg("sl", _shtr({}), _E + 20.0, "2026-08-03T03:01:00", "бар", False)
ck("П7 чист сянка-стоп СИ ОСТАВА 🛑", _sh2.split("\n")[0].startswith("🛑"))
ck("П7 чист сянка-стоп показва −20.00", "-20.00$/oz" in _sh2)
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

ck("П8 присъдата е в първите 3 реда (беше 9-и)", any("НЕ" in x for x in _ln[:3]))
ck("П8 присъдата е НАД входа", next(i for i, x in enumerate(_ln) if "НЕ" in x)
   < next(i for i, x in enumerate(_ln) if "ВХОД" in x or "ВЛЕЗЕШ" in x))
ck("П8 «ДА» картата също слага присъдата горе", any("ДА" in x for x in _ly[:3]))
ck("П8 отказ → 🛑 в заглавието", _ln[0].startswith("🛑"))
ck("П8 «ДА» → ✅ в заглавието", _ly[0].startswith("✅"))
ck("П8 ИЗЧАКАЙ → ⏳ в заглавието", _card("ИЗЧАКАЙ — пресен, но без ръб", False).split("\n")[0].startswith("⏳"))
ck("П8 🔴 вече НЕ значи «шорт» (беше обратно на действието)", "🔴" not in _cn and "🔴" not in _cy)
ck("П8 посоката пак се вижда с думи", "SHORT (продажба)" in _cn)
ck("П8 при отказ лотът е условен", "само ако въпреки това влезеш" in _cn)
ck("П8 при ДА лотът НЕ е условен", "само ако въпреки това влезеш" not in _cy)
ck("П8 «макс» вече е «макс ≈» + гап-уговорка", "макс ≈" in _cn and "при гап може повече" in _cn)
ck("П8 картата е балансиран HTML", _cn.count("<b>") == _cn.count("</b>") and _cn.count("<i>") == _cn.count("</i>"))
ck("П8 картата е под лимита на Телеграм", len(_cn) < 4096 and len(_cy) < 4096)
ck("П8 нивата пак са на картата", all(k in _cn for k in ("ТП1", "ТП2", "ТП3", "СТОП")))
# сянката: обещанието «този сетъп» само когато е вярно
_shon = {"direction": "short", "entry": 4111.0, "opened": "2026-08-03T05:00:00"}
_cs = _card(_NO, False, shadow_on=_shon)
ck("П8 сянка на ДРУГ сетъп → картата го признава", "ПЪРВИЯ сетъп" in _cs and "4,111.00" in _cs)
ck("П8 сянка на ДРУГ сетъп → НЕ обещава «този сетъп»", "Следя този сетъп" not in _cs)
ck("П8 сянка на СЪЩИЯ вход → пак «този сетъп»",
   "Следя този сетъп" in _card(_NO, False, shadow_on={"direction": "short", "entry": 4088.9}))
ck("П8 без сянка → пак «този сетъп»", "Следя този сетъп" in _cn)


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
ck("П9 картата носи индекса", "28.1 от 100" in _q)
ck("П9 картата носи ЧЕТИРИТЕ клъстера",
   all(x in _q for x in ("валуация 36", "моментум 10", "настроения 23", "on-chain 49")))
ck("П9 картата носи тежестите", "валуация 35%" in _q)
ck("П9 картата носи базовата честота на зоната", "16% от дните" in _q)
ck("П9 базовата честота е обявена за честота, НЕ прогноза", "не прогноза" in _q)
ck("П9 картата пази уговорката, че е BTC не злато", "НЕ сигнал за злато" in _q)
ck("П9 живият страх-алчност се показва при разминаване ≥2", "крипто сега: 25" in _q)
ck("П9 при съвпадение НЕ дублира",
   "крипто сега" not in lb._cq_msg(_CQ, "2026-08-04T09:00:00", fng_live={"value": 28, "cls": "Fear"}))
ck("П9 без жив фийд картата пак излиза", "28.1 от 100" in lb._cq_msg(_CQ, "2026-08-04T09:00:00"))
ck("П9 картата води към живата страница", "kiber-kvant.vercel.app" in _q)
ck("П9 картата е балансиран HTML",
   _q.count("<b>") == _q.count("</b>") and _q.count("<i>") == _q.count("</i>") and _q.count("<a ") == _q.count("</a>"))
ck("П9 картата е под лимита", len(_q) < 4096)
# устойчивост: старият кеш няма 'clusters' → картата пак трябва да излиза
_old = dict(_CQ); _old.pop("clusters")
ck("П9 стар кеш без клъстери НЕ чупи картата", "28.1 от 100" in lb._cq_msg(_old, "2026-08-04T09:00:00"))
ck("П9 празни клъстери → празен ред, не грешка", lb._cq_clusters_line({"clusters": {}}) == "")
ck("П9 частични клъстери минават", lb._cq_clusters_line({"clusters": {"1": 36.0}}) == "валуация 36")
ck("П9 непозната зона не чупи", "от 100" in lb._cq_msg(dict(_CQ, zone=""), "2026-08-04T09:00:00"))
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
ck("П10 картата казва кои крака решават", "решаващи: долар+лихви" in _c23)
_c33 = lb._sig_msg("short", 6, 7, "СРЕДЕН", sp, 4093.5, pd.Timestamp("2026-08-03 12:31:00"),
                   lb._levels(4088.9, "short"), 4088.9, _YES,
                   {"миньори": False, "долар": False, "лихви": False}, 1, _RG, stats, 1000, 2, adv_ok=True)
ck("П10 при съгласни долар+лихви → ✓ подредено", "2/2 ✓ подредено" in _c33 or "✓ подредено" in _c33)
_c03 = lb._sig_msg("short", 6, 7, "СРЕДЕН", sp, 4093.5, pd.Timestamp("2026-08-03 12:31:00"),
                   lb._levels(4088.9, "short"), 4088.9, _NO,
                   {"миньори": True, "долар": True, "лихви": True}, 0, _RG, stats, 1000, 2, adv_ok=False)
ck("П10 при несъгласни решаващи крака → ⚠ против", "⚠" in _c03 and "решаващи" in _c03)
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
ck("П11 стоп след 2 ТП се нарича БЕЗРИСКОВ ИЗХОД", "БЕЗРИСКОВ ИЗХОД" in _be2.split("\n")[0])
ck("П11 стоп след 2 ТП брои +6.50 по стълбата", "+6.50$/oz" in _be2)
ck("П11 стоп след 1 ТП брои +2.50 по стълбата", "+2.50$/oz" in _be1)
ck("П11 картата ИЗРИЧНО казва, че стопът не е ударен", "Стопът НЕ е ударен" in _be2 and "Стопът НЕ е ударен" in _be1)
ck("П11 картата казва КОИ ТП са прибрани", "TP1, TP2" in _be2 and "TP1" in _be1)
ck("П11 голото число е етикетирано като последната 1/3", "само последната 1/3" in _be2)
ck("П11 ИСТИНСКИЯТ стоп СИ ОСТАВА 🛑 СТОП", _hard.split("\n")[0].startswith("🛑 СТОП"))
ck("П11 истинският стоп показва −20.00 и в двете сметки",
   "-20.00$/oz" in _hard and "цяла позиция" in _hard)
ck("П11 истинският стоп НЕ твърди, че е безрисков", "БЕЗРИСКОВ" not in _hard and "Стопът НЕ е ударен" not in _hard)
ck("П11 реалният и сянката ползват ЕДНА функция за сметката",
   _src.count("_ladder_pnl(kind, hit, lv, e, sign, dol)") == 2)
ck("П11 изходните карти са балансиран HTML",
   all(c.count("<b>") == c.count("</b>") and c.count("<i>") == c.count("</i>") for c in (_be2, _be1, _hard)))
ck("П11 ТП3 след ТП1+ТП2 брои 13.17, не 20.00",
   "+13.17$/oz" in lb._exit_msg("tp3", _rtr({"tp1": True, "tp2": True}), _E - 20.0, "2026-08-03T09:41:00", "бар", False))


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
ck("П12 long/mixed казва че макрото е СМЕСЕНО", "СМЕСЕНО" in _g("long", 0)[0])
ck("П12 long/mixed казва че класът не носи нищо", "не носи нищо" in _g("long", 0)[0])
ck("П12 long/stale (стрийк 4+) ПРОДЪЛЖАВА да пуска", _g("long", 5)[1])
ck("П12 long/stale се нарича застоял, НЕ смесено", "застоял" in _g("long", 5)[0] and "СМЕСЕНО" not in _g("long", 5)[0])
ck("П12 long/day1 пуска (+2.57)", _g("long", 1)[1] and "+2.57" in _g("long", 1)[0])
ck("П12 long/fresh пуска (+1.84)", _g("long", 2)[1] and "+1.84" in _g("long", 2)[0])
# ОДИТ-10: short/day1 вече минава през ШУМ-пазача и се ОТКАЗВА (интервалът обхваща нулата)
ck("П12 short/day1 при ШУМ вече ОТКАЗВА", not _g("short", 1)[1])
ck("П12 short/fresh отказва", not _g("short", 2)[1])
ck("П12 short/mixed отказва", not _g("short", 0)[1])
ck("П12 short/stale отказва", not _g("short", 5)[1])
ck("П12 отказите носят 95% интервал (проверимо число)", "95%:" in _g("long", 0)[0] and "95%:" in _g("short", 5)[0])
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
    lb._spot = lambda instr="XAU/USD", market_closed=False: spot
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
   not any("ВЛИЗАЙ" in x or "ВХОД" in x for x in _s3))
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
ck("П14 картата казва «решаващи: долар+лихви»", "решаващи: долар+лихви" in _c14)
ck("П14 картата обявява миньорите за КОНТЕКСТ", "само контекст" in _c14)
ck("П14 картата вече НЕ брои «/3» за решението", "/3 ✓" not in _c14 and "/3 ⚠" not in _c14)
# шум-пазачът важи и за пресните клетки
_noisy_fresh = json.loads(json.dumps(_G))
_noisy_fresh["fresh"]["short"]["day1"] = {"win": 71.5, "net": 0.44, "n": 3100, "lo": -1.071, "hi": 1.850}
_t14, _p14 = lb._advice_entry("short", 1, _noisy_fresh, None, False, 0)
ck("П14 ПРЕСЕН клас с нула в интервала → ОТКАЗ (беше пускане на голо нето>0)", not _p14)
ck("П14 отказът обяснява защо", "не носи нищо" in _t14 and "95%:" in _t14)
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
ck("П17 zone=None НЕ пипа размера (тежест 1.0)",
   "0.10 лот" in lb._sig_msg("long", 6, 7, "ПРЕМИУМ", sp, 4081.0,
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
ck("П17 клас A → пълен лот (0.10 при 10000$@2%)", "0.10 лот" in _a)
ck("П17 клас B → две трети (0.07 лот)", "0.07 лот" in _b17)
ck("П17 клас C → една трета (0.03 лот)", "0.03 лот" in _c17)
ck("П17 A НЕ обявява намаление (пълен е)", "зона A →" not in _a)
ck("П17 B и C КАЗВАТ намалението честно",
   "зона B → 67% от 2% = 1.34%" in _b17 and "зона C → 33% от 2% = 0.66%" in _c17)
ck("П17 текстът на зоната стои на картата", "зона A" in _a and "зона C" in _c17)
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
ck("П20 картата казва ШОРТ, не ЛОНГ", "SHORT" in _m20 or "ШОРТ" in _m20)

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
    ck(f"П21 картичка «{_sl21}» КАЗВА, че ботът е здрав, не счупен",
       "здрав" in _m21 and "затворена" in _m21)
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
        ck("П22 картата НОСИ задължителния ред за неизмереното",
           "НОВО · още не е мерено" in _т22)
        ck("П22 картата показва КОЕ съвпада и КОЕ липсва",
           "КАКВО СЪВПАДНА" in _т22 and ("липсва" in _т22 or "✗" in _т22))
        ck("П22 картата има отделен ред за СТАРОТО мерено правило",
           "СТАРОТО ПРАВИЛО" in _т22)
        ck("П22 без подадено мерено картата казва, че старото правило мълчи",
           "мълчи" in _т22)

        # мереното НЕ бива да мени точките — двете числа не се смесват
        _stats22 = {"fresh": {"long": {"day1": {"win": 79.9, "net": 2.99, "n": 4019,
                                                "lo": 1.655, "hi": 4.196}},
                              "short": {"day1": {"win": 71.5, "net": 0.44, "n": 3100,
                                                 "lo": -1.07, "hi": 1.85}}}}
        _м22 = _CB22.мерено_от_стата(_stats22, "day1", _намерен22["лонг"])
        _т22б = _CB22.карта(_намерен22, мерено=_м22)
        ck("П22 мереното НЕ променя точките (двете числа не се смесват)",
           _намерен22["точки"] == _намерен22["точки"] and str(_намерен22["точки"]) in _т22б)
        ck("П22 мереният ред цитира n и доверителния интервал",
           "n=" in _т22б and "95%" in _т22б)
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

        def _yf22(s, period="2y", interval="1d"):
            if s == "GC=F" and interval in ("1m", "5m"):
                return _D5.copy()
            return _DD.get(s, _fx(900, "2026-07-20", "5min", 4000, 0.002)).copy()
        lb._yf = _yf22
        lb._rates = lambda: _pd22.Series(
            2.0 - _np22.arange(600) * 0.0008,
            index=_pd22.date_range("2024-06-01", periods=600, freq="D"))
        lb._spot = lambda instr="XAU/USD", market_closed=False: _SP
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
       any("НОВО · още не е мерено" in x for x in _sB22))
    ck("П22 без мозък такава карта НЯМА (сравнението не е самозаблуда)",
       not any("НОВО · още не е мерено" in x for x in _sA22))
    _jA22 = [json.loads(x) for x in
             (_tA22 / "live_journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    _jB22 = [json.loads(x) for x in
             (_tB22 / "live_journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    _клк22б = ("dir", "score", "tier", "trade", "spot", "macro", "board", "regime",
               "advice", "cell")
    ck("П22 при РАБОТЕЩ мозък решението на бота е СЪЩОТО (посока/клас/сделка/борд)",
       all(_jA22[0].get(k) == _jB22[0].get(k) for k in _клк22б if k in _jA22[0]))
    _новиA22 = [x for x in _sA22 if "НОВО · още не е мерено" in x]
    _новиB22 = [x for x in _sB22 if "НОВО · още не е мерено" in x]
    ck("П22 старите карти са дума по дума същите с и без мозък",
       [x for x in _sA22 if x not in _новиA22] == [x for x in _sB22 if x not in _новиB22])
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
        _стари22 = [x for x in _s_с22 if "НОВО · още не е мерено" not in x]
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
    ck("П22 прагът е 0 — праща и «искрите» (изрично поискано)",
       "състояние=_bstate, праг=0" in _src)
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


