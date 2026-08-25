# -*- coding: utf-8 -*-
"""ОПИС · рендерира ВСЯКО съобщение, което двата бота могат да пратят."""
import importlib.util, sys, json, io, re, html, datetime as dt

sp = importlib.util.spec_from_file_location("lb", "live_bot.py")
lb = importlib.util.module_from_spec(sp); sys.modules["lb"] = lb; sp.loader.exec_module(lb)
st = json.load(open("backtest_stats.json", encoding="utf-8"))

mac = {"долар": True, "лихви": True, "миньори": True}
macx = {"долар": False, "лихви": False, "миньори": False}
brd = [("1мин", "long", 5, "medium", "ГОТОВ"), ("5м", "long", 6, "strong", "СИЛЕН"),
       ("15м", "long", 6, "strong", "СИЛЕН"), ("30м", "long", 5, "medium", "ГОТОВ"),
       ("1час", "long", 6, "strong", "СИЛЕН"), ("4час", "short", 4, "weak", "ОФОРМЯ СЕ"),
       ("1ден", "long", 5, "medium", "ГОТОВ")]
best = ("1час", "long", 6, "strong", "СИЛЕН")
lv = lb._levels(4365.20, "long")
lvs = lb._levels(4365.20, "short")
tr = {"direction": "long", "entry": 4358.00, "opened": "2026-08-11T09:12",
      "levels": {"tp1": 4365.5, "tp2": 4370.0, "tp3": 4378.0, "sl": 4338.0},
      "hit": {"tp1": True, "tp2": True}, "sym": "XAUUSD"}
tr0 = dict(tr, hit={})

К = {}
К["1 · СИГНАЛ ДА (нов вход)"] = lb._sig_msg(
    "long", 6, 5, "СИЛЕН", {"mid": 4365.2}, 4365.0, "2026-08-11T11:15", lv, 4365.2,
    "ДА — пресен клас, макрото е подредено", mac, 1, {"vol_rank": 0.35}, st, 5000, 2.0,
    adv_ok=True, zone=("B", "зона B"))
К["2 · СИГНАЛ НЕ (+сянка)"] = lb._sig_msg(
    "short", 5, 4, "ГОТОВ", {"mid": 4365.2}, 4365.0, "2026-08-11T11:15", lvs, 4365.2,
    "НЕ — макрото е против шорта", macx, 0, {"vol_rank": 0.5}, st, 5000, 2.0,
    adv_ok=False, shadow_on={"direction": "short", "entry": 4111.0, "opened": "2026-08-10T09:00"})
К["3 · СИГНАЛ при ОТВОРЕНА сделка"] = lb._sig_msg(
    "long", 6, 5, "СИЛЕН", {"mid": 4365.2}, 4365.0, "2026-08-11T11:15", lv, 4365.2,
    "ДА", mac, 1, {"vol_rank": 0.35}, st, 5000, 2.0, adv_ok=True, open_trade=tr)
К["4 · СТОЯЩ СЕТЪП"] = lb._standing_msg(
    "long", best, 14.0, {"mid": 4365.2}, 4365.0, 4365.2, brd, mac, {}, "2026-08-11T11:20")
К["5 · СПРЯНА (виждам, не предлагам)"] = lb._спряна_msg(
    "short", ("1час", "short", 6, "strong", "СИЛЕН"), 4365.2,
    "стоп-пазач · 2 стопа днес в тази посока", "х", "2026-08-11T11:20", brd)
К["6 · ИЗХОД ТП1"] = lb._exit_msg("tp1", tr0, 4365.5, "2026-08-11T10:00", "спот", False, {"mid": 4366.0})
К["7 · ИЗХОД ТП3"] = lb._exit_msg("tp3", tr, 4378.0, "2026-08-11T10:40", "спот", False, {"mid": 4378.2})
К["8 · ИЗХОД СТОП (истински)"] = lb._exit_msg("sl", tr0, 4338.0, "2026-08-11T10:00", "бар", True, {"mid": 4337.0})
К["9 · ИЗХОД безрисков"] = lb._exit_msg("sl", tr, 4358.0, "2026-08-11T10:00", "бар", False, {"mid": 4357.0})
К["10 · СЯНКА изход"] = lb._shadow_exit_msg("tp2", tr, 4370.0, "2026-08-11T10:20", "бар", False, {"mid": 4371.0})
К["11 · MA-АЛАРМА"] = lb._ma_alert_msg("long", "ema200", 4365.2, {"win": 62.8, "n": 410}, mac)
К["12 · ПУЛС сутрин"] = lb._pulse_msg("09", brd, best, "long", "ДА — пресен клас", True,
                                      None, None, {"mid": 4365.2}, {"mid": 65.15}, mac, False, False)
К["13 · ПУЛС с отворена сделка"] = lb._pulse_msg("14", brd, best, "long", "ДА", True,
                                                 tr, None, {"mid": 4365.2}, None, mac, False, False)
К["14 · ПУЛС уикенд"] = lb._pulse_msg("09", brd, best, None, "", False, None, None,
                                      None, None, mac, False, True)
try:
    К["15 · СТАТУС"] = lb._status_msg(brd, "long", tr, None, {"mid": 4365.2}, {"mid": 65.15},
                                      57.7, 0.2, {"stops": 1}, False, "2026-08-11", mac)
except Exception as e:
    К["15 · СТАТУС"] = f"[не се рендерира: {type(e).__name__}: {e}]"
try:
    К["16 · ДАЙДЖЕСТ"] = lb._digest_msg(*([None] * 0))
except Exception:
    import inspect
    К["16 · ДАЙДЖЕСТ"] = f"[подпис: {inspect.signature(lb._digest_msg)}]"
К["17 · УИКЕНД карта"] = lb._weekend_msg(lb._weekend_slot(dt.datetime(2026, 8, 8, 9, 0)) or "сутрин",
                                         dt.datetime(2026, 8, 8, 9, 0)) if hasattr(lb, "_weekend_msg") else "—"

out = []
for име, т in К.items():
    if not isinstance(т, str):
        т = str(т)
    чист = re.sub(r"<[^>]+>", "", html.unescape(т))
    out.append("╔" + "═" * 62)
    out.append(f"║ {име}   [{len(т.splitlines())} реда · {len(т)} знака]")
    out.append("╚" + "═" * 62)
    out.append(чист)
    out.append("")
io.open("ОПИС_КАРТИ.txt", "wb").write("\n".join(out).encode("utf-8"))
print("\n".join(out))
