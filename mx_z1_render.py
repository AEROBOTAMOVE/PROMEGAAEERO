# -*- coding: utf-8 -*-
"""РЕНДИРА ЖИВО петте карти: КЪДЕ СМЕ · пулс · вечерна равносметка · БОТЪТ СПА · уикенд.
САМО ЧЕТЕНЕ на live_bot.py."""
import sys, io, json, os, pathlib, tempfile
sys.stdout.reconfigure(encoding="utf-8")
sys.argv = ["x"]
import live_bot as lb

def show(име, т):
    р = т.split("\n")
    print("=" * 78)
    print(f"### {име}   [{len(р)} реда · {len(т)} знака]")
    print("-" * 78)
    print(т)
    print()

stats = json.load(io.open("backtest_stats.json", encoding="utf-8"))

# ---- общи фикстури -------------------------------------------------------
spot_g = {"mid": 4365.20, "bid": 4365.0, "ask": 4365.4, "src": "twelve"}
spot_s = {"mid": 65.150, "src": "twelve"}
trade = {"direction": "long", "entry": 4358.00, "sym": "XAUUSD",
         "opened": "2026-08-19T09:00:00",
         "levels": {"tp1": 4365.50, "tp2": 4370.00, "tp3": 4378.00, "sl": 4358.00},
         "hit": {"tp1": True, "tp2": True}}
board = [("H1", "long", 3, "A")] * 7
guard = {"long": 2, "short": 0}
macro = {"долар": 1, "лихви": 1}
macro_raw_kavga = {"долар": 0.0031, "лихви": -0.02}     # бият се
macro_raw_edno  = {"долар": 0.0031, "лихви": 0.02}      # подредени нагоре
streaks = {"long": 3, "short": 0}

print("### СВЕРКА НА КОНСТАНТИ")
print("PIP", lb.PIP, "| SL_PIPS", lb.SL_PIPS, "| ДНИ_МАКС", lb.ДНИ_МАКС,
      "| MIN_N", lb.MIN_N, "| REOFFER_MAX_AGE_H", lb.REOFFER_MAX_AGE_H)
пл, n = lb._отворена_стълба(trade, spot_g)
print("_отворена_стълба =>", пл, n, "|", lb._пари(пл))
print("_съгласни(7 еднакви рамки, long) =>", lb._съгласни(board, "long"))
т = ((stats.get("_meta") or {}).get("тишина_мерена"))
print("тишина_мерена =>", json.dumps(т, ensure_ascii=False))
for пос in ("long", "short"):
    for кофа in ("day1", "stale", "mixed"):
        с = stats.get("fresh", {}).get(пос, {}).get(кофа, {})
        print(f"  fresh/{пос}/{кофа}: win={с.get('win')} net={с.get('net')} "
              f"n={с.get('n')} lo={с.get('lo')} hi={с.get('hi')} дни={с.get('дни')}")
print()

# ---- 1 · КЪДЕ СМЕ --------------------------------------------------------
show("СТАР · КЪДЕ СМЕ (сделка тече, пазач спрял покупките, US щит)",
     lb._status_msg(board, "long", trade, None, spot_g, spot_s, None, None,
                    guard, True, "2026-08-21", macro))
show("СТАР · КЪДЕ СМЕ (празно: няма сделки, посока разбъркана, без пазач)",
     lb._status_msg([], None, None, None, spot_g, spot_s, None, None,
                    {}, False, "2026-08-21", macro))

# ---- 2 · ПУЛС ------------------------------------------------------------
for part in ("09", "14", "22"):
    show(f"СТАР · ПУЛС {part} (макрото се бие, няма сделка)",
         lb._pulse_msg(part, board, None, "long", "", False, None, None,
                       spot_g, spot_s, macro, False, False,
                       macro_raw_kavga, streaks, stats))
show("СТАР · ПУЛС 14 (макрото подредено, сделка тече)",
     lb._pulse_msg("14", board, None, "long", "", True, trade, None,
                   spot_g, spot_s, macro, False, False,
                   macro_raw_edno, streaks, stats))
show("СТАР · ПУЛС (уикенд)",
     lb._pulse_msg("09", board, None, None, "", False, None, None,
                   spot_g, spot_s, macro, False, True,
                   macro_raw_edno, streaks, stats))

# ---- 3 · ВЕЧЕРНА РАВНОСМЕТКА --------------------------------------------
tmp = pathlib.Path(tempfile.mkdtemp(prefix="mxz1_"))
with (tmp / "live_journal.jsonl").open("w", encoding="utf-8") as fh:
    for h in range(6, 21):
        fh.write(json.dumps({"date": "2026-08-21",
                             "run_utc": f"2026-08-21T{h:02d}:07:00"},
                            ensure_ascii=False) + "\n")
with (tmp / "sent_log.jsonl").open("w", encoding="utf-8") as fh:
    for h in (9, 13, 14):
        fh.write(json.dumps({"utc": f"2026-08-21T{h:02d}:00:00"},
                            ensure_ascii=False) + "\n")
show("СТАР · ВЕЧЕРНА РАВНОСМЕТКА (сделка тече, 2 стопа днес)",
     lb._digest_msg(tmp, "2026-08-21", trade, None, spot_g, spot_s, guard))
show("СТАР · ВЕЧЕРНА РАВНОСМЕТКА (петък → седмична, без сделки, без стопове)",
     lb._digest_msg(tmp, "2026-08-21", None, None, spot_g, spot_s, {}, True))

# ---- 4 · БОТЪТ СПА -------------------------------------------------------
show("СТАР · БОТЪТ СПА (187 мин)",
     lb._спал_msg(187, "2026-08-21T06:13:00", "2026-08-21T09:20:00"))
show("СТАР · БОТЪТ СПА (46 мин)",
     lb._спал_msg(46, "2026-08-21T06:13:00", "2026-08-21T06:59:00"))

# ---- 5 · УИКЕНД ----------------------------------------------------------
for slot in ("сутрин", "следобед", "вечер"):
    show(f"СТАР · УИКЕНД · {slot}", lb._weekend_msg(slot, "2026-08-22"))

# ---- проверчик стил ------------------------------------------------------
print("=" * 78)
try:
    import importlib.util
    сп = importlib.util.spec_from_file_location("стил", "стил.py")
    ст = importlib.util.module_from_spec(сп); сп.loader.exec_module(ст)
    print("стил.py зареден. Публични имена:",
          [x for x in dir(ст) if not x.startswith("__")])
except Exception as e:
    print("стил.py:", type(e).__name__, e)
