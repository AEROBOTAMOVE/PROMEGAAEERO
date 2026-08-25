# -*- coding: utf-8 -*-
"""ОБОРВАНЕ на находка 36: пулсът над 7 реда при отворена сделка.
Правило: ползвам РЕАЛНИТЕ форми от живия път (call site 3573):
  board = списък от кортежи (lbl, dir, score, strength, label)  [ред 3056]
  trade = ФАЙЛОВАТА форма от out/open_trade.json, прекарана през _migrate_trade
  stats = истинският backtest_stats.json
  macro_raw = macro_health (речник долар/лихви)
Присъдата дава замразеният пазач стил.провери (МАКС_РЕДОВЕ=7)."""
import sys, json, io
sys.argv = ["x"]
sys.stdout.reconfigure(encoding="utf-8")
import live_bot as lb, стил

stats = json.load(open("backtest_stats.json", encoding="utf-8"))

# РЕАЛНА файлова форма (копие от _o37_18392/trade.json — жив запис)
_raw = json.load(open("_o37_18392/trade.json", encoding="utf-8"))
trade = lb._migrate_trade(json.loads(json.dumps(_raw)), 0.0, notes=[])
s_raw = dict(_raw, sym="XAGUSD", entry=37.5,
             levels={"tp1": 38.0, "tp2": 38.5, "tp3": 39.0, "sl": 37.0})
s_trade = lb._migrate_trade(json.loads(json.dumps(s_raw)), 0.0, notes=[])

board = [(l, "long", 5, "medium", "СРЕДЕН") for l in
         ("1мин", "5м", "15м", "30м", "1час", "4час", "1ден")]
spot_g = {"mid": 4370.12, "src": "binance"}
spot_s = {"mid": 64.821, "src": "binance"}
macro = {"миньори": True, "долар": True, "лихви": False}

СЪСТ = [
    ("макро РАЗБЪРКАНО", {"долар": 0.0145, "лихви": -0.07}, {"long": 0}),
    ("макро ПОДРЕДЕНО ", {"долар": 0.0145, "лихви": 0.07}, {"long": 6}),
]
СДЕЛКИ = [
    ("без сделка (както го тества selftest)", None, None),
    ("само ЗЛАТО отворено            ", trade, None),
    ("злато И сребро отворени        ", trade, s_trade),
]

for имес, мр, ст in СЪСТ:
    for имет, tr, sr in СДЕЛКИ:
        for час in ("09", "14", "22"):
            txt = lb._pulse_msg(час, board, board[-1], "long", "ДА", True, tr, sr,
                                spot_g, spot_s, macro, False, False,
                                macro_raw=мр, streaks=ст, stats=stats)
            чист = стил.чист(txt)
            n = len([r for r in чист.split("\n") if r.strip()])
            нах = стил.провери("пулс", txt)
            дълги = [x for x in нах if x[0] == "дълга"]
            флаг = "🔴 НАД ТАВАНА" if n > стил.МАКС_РЕДОВЕ else "✅"
            print(f"{имес} | {имет} | {час}ч → {n} реда  {флаг}   пазач:{дълги}")
            if час == "09" and n > стил.МАКС_РЕДОВЕ:
                for i, l in enumerate(чист.split("\n"), 1):
                    print(f"      {i:2d} {l}")
    print()
