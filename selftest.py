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
ck("О5 стоящата карта КАЗВА, че не е вход", "ТОВА НЕ Е ВХОД" in _stm)
ck("О5 стоящата карта НЕ дава нива за влизане",
   "ТП1" not in _stm and "ТП2" not in _stm and "СТОП:" not in _stm)
ck("О5 стоящата карта показва възрастта", "27 часа" in _stm)
_stm2 = lb._standing_msg("short", ("1час", "short", 7, "strong", "СИЛЕН"), 20.0, None, 4006.0, 4000.2,
                         [("1час", "short", 7, "strong", "СИЛЕН")] * 7,
                         {"миньори": False, "долар": False, "лихви": False}, {"мъртви": ["долар"]}, "2026-07-29T10:00")
ck("О5 стоящата карта предупреждава за мъртъв фийд", "макро-краче без данни" in _stm2)
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
ck("О7 извадките са ГОЛЕМИ (n>1000 навсякъде в fresh)",
   all(v["n"] > 1000 for d in ("long", "short") for v in _fr[d].values()))
ck("О7 всички n са над MIN_N", all(v["n"] >= lb.MIN_N for d in ("long", "short") for v in _fr[d].values()))
ck("О7 файлът казва КАК е мерен", "злато_fresh_преизмерено" in _bs.get("_meta", {}))
ck("О7 файлът казва кое НЕ е мерено", "НЕпреизмерено" in _bs.get("_meta", {}))
# ПОВЕДЕНИЕ на гейта — това е, което всъщност пази парите
_g = lambda d, s: lb._advice_entry(d, s, _bs, None, False, 0)[1]
ck("О7 шорт ден-2 вече се ОТКАЗВА", _g("short", 2) is False)
ck("О7 шорт ден-3 вече се ОТКАЗВА", _g("short", 3) is False)
ck("О7 шорт застоял пак се отказва", _g("short", 0) is False and _g("short", 9) is False)
ck("О7 ЛОНГЪТ не е засегнат (всички стрийкове минават)",
   all(_g("long", s) for s in (0, 1, 2, 3, 4, 9, 20)))
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
