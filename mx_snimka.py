# -*- coding: utf-8 -*-
"""СНИМКА НА ВСИЧКИ КАРТИ · базата, срещу която ще докажа, че тръбите не менят нищо."""
import sys, json, io, re, hashlib
sys.argv = ["x"]
import live_bot as lb
import pandas as pd

st = json.load(io.open("backtest_stats.json", encoding="utf-8"))
ч = lambda t: re.sub(r"</?(b|i|code)>", "", t)
mac = {"долар": True, "лихви": True, "миньори": True}
macm = {"долар": True, "лихви": False, "миньори": True}
board = [("1мин", "long", 5, "medium", None), ("5м", "long", 5, "medium", None)]
TRg = {"direction": "long", "entry": 4358.0, "levels": lb._levels(4358.0, "long"),
       "hit": {}, "status": "open", "sym": "XAUUSD"}
sp = {"bid": 4365.0, "ask": 4365.4, "mid": 4365.2}
K = {}
_б = dict(direction="long", score=6, agree_n=7, tier_name="ПРЕМИУМ", spot=sp,
          bar_price=4365.0, bar_ts=None, lv=lb._levels(4365.2, "long"), entry=4365.2,
          macro=mac, streak_n=1, regime={"streaks": {"long": 1}, "vol_rank": .5},
          stats=st, balance=1000, risk_pct=2)
for им, доп in (("сигнал_A", dict(advice_txt="ДА — макрото се подрежда", zone=("A", "🟩 чисто"))),
                ("сигнал_B", dict(advice_txt="ДА — макрото се подрежда", zone=("B", "🟨 едно от двете"))),
                ("сигнал_C", dict(advice_txt="ДА (малък размер) — отпреди 5 дни", zone=("C", "🟧 нищо"))),
                ("отказ", dict(advice_txt="НЕ — доларът и лихвите се карат днес", adv_ok=False)),
                ("тече", dict(advice_txt="ДА", open_trade=dict(TRg, hit={"tp1": True})))):
    K[им] = lb._sig_msg(**_б, **доп)
for k, ц, h in (("tp1", 4365.5, {}), ("tp2", 4370.0, {"tp1": True}),
                ("tp3", 4378.0, {"tp1": True, "tp2": True}), ("sl", 4338.0, {}),
                ("time", 4360.0, {}), ("flip", 4360.0, {})):
    K["изход_" + k] = lb._exit_msg(k, dict(TRg, hit=h), ц, "2026-08-21T10:00", "бар", False, dec=2)
K["сянка"] = lb._shadow_exit_msg("sl", TRg, 4338.0, "2026-08-21T10:00", "бар", False)
K["стои"] = lb._standing_msg("long", None, 3.0, 4396.6, 4448.0, 4396.6, board, macm, None,
                             "2026-08-21T10:00")
K["спряна"] = lb._спряна_msg("long", None, 4400.0, "ре-влизане в пауза", "мерено: −1.59$", None, board)
K["ниво"] = lb._ma_alert_msg("long", "ma50", 4388.4, st["ma_bounce"]["long"]["ma50"], {})
K["статус"] = lb._status_msg(board, "long", TRg, None, sp, None, 0, 0,
                             {"long": 0, "short": 0}, False, "2026-08-21", mac)
K["мълчи"] = "\n".join(lb._защо_мълчи({"долар": 0.0131, "лихви": -0.06},
                                      {"long": 0, "short": 0}, "long", st))
K["крипто"] = lb._cq_msg({"zone": "Неутрална", "score": 50}, "2026-08-21T10:00")

изх = {им: ч(т) for им, т in K.items()}
json.dump(изх, io.open("mx_baza.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
h = hashlib.sha256(json.dumps(изх, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
print(f"снимани {len(изх)} карти · отпечатък {h}")
for им in sorted(изх):
    print(f"  {им:12s} {len(изх[им].splitlines()):2d} реда · {len(изх[им]):4d} знака")
