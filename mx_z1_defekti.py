# -*- coding: utf-8 -*-
"""МЕРИ ДЕФЕКТИТЕ в петте карти. Само четене."""
import sys, io, json, pathlib, tempfile, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
sys.argv = ["x"]
import live_bot as lb
import pandas as pd

сп = importlib.util.spec_from_file_location("стил", "стил.py")
ст = importlib.util.module_from_spec(сп); сп.loader.exec_module(ст)

print("### 1 · ЕДНО И СЪЩО ЗАГЛАВИЕ: равносметка (21ч) срещу пулс-22 (22ч)")
tmp = pathlib.Path(tempfile.mkdtemp(prefix="mxz1b_"))
(tmp / "live_journal.jsonl").write_text("", encoding="utf-8")
(tmp / "sent_log.jsonl").write_text("", encoding="utf-8")
d = lb._digest_msg(tmp, "2026-08-21", None, None, None, None, {})
p = lb._pulse_msg("22", [], None, None, "", False, None, None, None, None,
                  {}, False, False, {"долар": 0.003, "лихви": 0.02}, {}, None)
print("  равносметка ред 1:", repr(d.split("\n")[0]))
print("  пулс-22     ред 1:", repr(p.split("\n")[0]))
print("  ЕДНАКВИ ЛИ СА:", d.split("\n")[0] == p.split("\n")[0])
print()

print("### 2 · КОГА ОТВАРЯ ПАЗАРЪТ (спрямо думите «до неделя вечер»)")
for iso in ["2026-08-23T18:00:00", "2026-08-23T19:00:00", "2026-08-23T20:00:00",
            "2026-08-23T21:00:00", "2026-08-23T21:59:00", "2026-08-23T22:00:00",
            "2026-08-23T23:00:00"]:
    з = lb._market_closed(iso)
    print(f"  UTC {iso[11:16]} · София {lb._sofia(iso)} · неделя · затворен={з} "
          f"· уикенд-слот={lb._weekend_slot(iso)}")
print()

print("### 3 · «БОТЪТ СПА»: търговски минути СРЕЩУ стенен часовник")
случаи = [("2026-08-21T06:13:00", "2026-08-21T09:20:00", "делник, без затваряне"),
          ("2026-08-21T19:00:00", "2026-08-22T02:00:00", "петък вечер → събота (пазарът затваря)")]
for a, b, име in случаи:
    тм = lb._търговски_минути(a, b)
    стена = (pd.Timestamp(b) - pd.Timestamp(a)).total_seconds() / 60
    т = lb._спал_msg(тм, a, b)
    print(f"  {име}: търговски={тм:.0f}мин · стена={стена:.0f}мин")
    for r in т.split("\n"):
        print("     ", r)
print()

print("### 4 · СТИЛ.PY върху СТАРИТЕ пет карти (таван 7 реда / 400 знака)")
spot_g = {"mid": 4365.20, "src": "twelve"}; spot_s = {"mid": 65.150, "src": "twelve"}
trade = {"direction": "long", "entry": 4358.00, "sym": "XAUUSD",
         "opened": "2026-08-19T09:00:00",
         "levels": {"tp1": 4365.50, "tp2": 4370.00, "tp3": 4378.00, "sl": 4358.00},
         "hit": {"tp1": True, "tp2": True}}
board = [("H1", "long", 3, "A")] * 7
stats = json.load(io.open("backtest_stats.json", encoding="utf-8"))
with (tmp / "live_journal.jsonl").open("w", encoding="utf-8") as fh:
    for h in range(6, 21):
        fh.write(json.dumps({"date": "2026-08-21", "run_utc": f"2026-08-21T{h:02d}:07:00"}) + "\n")
К = {
 "КЪДЕ СМЕ (пълна)": lb._status_msg(board, "long", trade, None, spot_g, spot_s,
                                    None, None, {"long": 2}, True, "2026-08-21", {}),
 "КЪДЕ СМЕ (празна)": lb._status_msg([], None, None, None, spot_g, spot_s,
                                     None, None, {}, False, "2026-08-21", {}),
 "ПУЛС 09 (кавга)": lb._pulse_msg("09", board, None, "long", "", False, None, None,
                                  spot_g, spot_s, {}, False, False,
                                  {"долар": 0.0031, "лихви": -0.02}, {"long": 3}, stats),
 "ПУЛС 14 (подредено+сделка)": lb._pulse_msg("14", board, None, "long", "", True, trade, None,
                                  spot_g, spot_s, {}, False, False,
                                  {"долар": 0.0031, "лихви": 0.02}, {"long": 3}, stats),
 "РАВНОСМЕТКА": lb._digest_msg(tmp, "2026-08-21", trade, None, spot_g, spot_s, {"long": 2}),
 "БОТЪТ СПА": lb._спал_msg(187, "2026-08-21T06:13:00", "2026-08-21T09:20:00"),
 "УИКЕНД сутрин": lb._weekend_msg("сутрин", "2026-08-22"),
}
for име, т in К.items():
    н = ст.провери(име, т)
    print(f"  {име}: {len(н)} находки" + ("" if н else "  ✓ чиста"))
    for вид, txt in н:
        print(f"      [{вид}] {txt}")
print()

print("### 5 · ПАРИТЕ НА ЕДНА И СЪЩА СДЕЛКА, В ТРИ КАРТИ, В ЕДИН И СЪЩ МИГ")
for име, т in (("КЪДЕ СМЕ", К["КЪДЕ СМЕ (пълна)"]),
               ("ПУЛС", К["ПУЛС 14 (подредено+сделка)"]),
               ("РАВНОСМЕТКА", К["РАВНОСМЕТКА"])):
    for r in т.split("\n"):
        if "4,358.00" in r and ("$" in r):
            print(f"  {име:14s} → {ст.чист(r)}")
print()

print("### 6 · КОЛКО ПАРИ Е СТРУВАЛ СТОПЪТ — има ли го изобщо в равносметката?")
print("  ред за стоповете:", [ст.чист(r) for r in К["РАВНОСМЕТКА"].split("\n") if "стоп" in r])
print("  'сребро изключено' обяснението (от _advice_entry:1016):")
print("   ", lb._advice_entry("long", 0, stats, False, False, 0, sym="XAGUSD")[0])
