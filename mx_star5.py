# -*- coding: utf-8 -*-
"""СТАРИТЕ пет карти: КЪДЕ СМЕ · пулс · вечерна равносметка · БОТЪТ СПА · уикенд.
Само ЧЕТЕ live_bot.py. Изпълнено рендиране, не скица."""
import sys, json, io, re, os, pathlib, tempfile
sys.argv = ["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import live_bot as lb

ч = lambda t: re.sub(r"</?(b|i|code)>", "", t)
st = json.load(io.open("backtest_stats.json", encoding="utf-8"))

mac  = {"долар": True, "лихви": True, "миньори": True}
macr_подр  = {"долар": 0.0131, "лихви": 0.06}    # плюс = добро за златото
macr_карат = {"долар": 0.0131, "лихви": -0.06}
board = [("1мин","long",5,"medium",None), ("5м","long",5,"medium",None),
         ("15м","long",5,"medium",None), ("30м","long",5,"medium",None),
         ("1ч","long",5,"medium",None), ("4ч","long",5,"medium",None),
         ("1д","long",5,"medium",None)]
TRg = {"direction":"long","entry":4358.0,"levels":lb._levels(4358.0,"long"),
       "hit":{"tp1":True,"tp2":True},"status":"open","sym":"XAUUSD",
       "opened":"2026-08-19T09:00:00+00:00"}
spg = {"bid":4365.0,"ask":4365.4,"mid":4365.2}
sps = {"bid":65.14,"ask":65.16,"mid":65.150}

print("="*72); print("СТАР · КЪДЕ СМЕ (статус, guard 2 стопа покупки, без щит)"); print("="*72)
t = ч(lb._status_msg(board,"long",TRg,None,spg,sps,0,0,{"long":2,"short":0},False,"2026-08-21",mac))
print(t); print(f"→ {len(t.splitlines())} реда · {len(t)} знака")

print(); print("="*72); print("СТАР · КЪДЕ СМЕ (без сделка, макро разбъркано, без guard)"); print("="*72)
t = ч(lb._status_msg(board,None,None,None,spg,sps,0,0,{},False,"2026-08-21",mac))
print(t); print(f"→ {len(t.splitlines())} реда · {len(t)} знака")

for сл, им in (("09","ПУЛС 09 · подредено макро · няма сделка"),
               ("14","ПУЛС 14 · КАРАЩО СЕ макро · няма сделка"),
               ("22","ПУЛС 22 · подредено · отворена сделка")):
    mr = macr_карат if сл=="14" else macr_подр
    tr = TRg if сл=="22" else None
    print(); print("="*72); print("СТАР · "+им); print("="*72)
    t = ч(lb._pulse_msg(сл, board, None, "long", "ДА — макрото се подрежда", True,
                        tr, None, spg, sps, mac, False, False,
                        macro_raw=mr, streaks={"long":1,"short":0}, stats=st))
    print(t); print(f"→ {len(t.splitlines())} реда · {len(t)} знака")

print(); print("="*72); print("СТАР · ПУЛС в уикенд"); print("="*72)
t = ч(lb._pulse_msg("09", board, None, "long", "", True, None, None, spg, sps, mac, False, True,
                    macro_raw=macr_подр, streaks={"long":1}, stats=st))
print(t); print(f"→ {len(t.splitlines())} реда · {len(t)} знака")

# --- вечерна равносметка: истински файлове ---
tmp = pathlib.Path(tempfile.mkdtemp(prefix="mx_dig_"))
with (tmp/"live_journal.jsonl").open("w",encoding="utf-8") as f:
    for h in range(22*60, 22*60+8*60, 15):      # 22:00 UTC предната вечер нататък
        f.write(json.dumps({"date":"2026-08-21","run_utc":f"2026-08-21T{(h//60)%24:02d}:{h%60:02d}:00"},ensure_ascii=False)+"\n")
with (tmp/"sent_log.jsonl").open("w",encoding="utf-8") as f:
    for i in range(3):
        f.write(json.dumps({"utc":f"2026-08-21T1{i}:00:00"},ensure_ascii=False)+"\n")
print(); print("="*72); print("СТАР · ВЕЧЕРНА РАВНОСМЕТКА (сделка + 2 стопа)"); print("="*72)
t = ч(lb._digest_msg(tmp,"2026-08-21",TRg,None,spg,sps,{"long":2,"short":0}))
print(t); print(f"→ {len(t.splitlines())} реда · {len(t)} знака")
print(); print("="*72); print("СТАР · ВЕЧЕРНА РАВНОСМЕТКА (петък, без сделка, без стопове)"); print("="*72)
t = ч(lb._digest_msg(tmp,"2026-08-21",None,None,spg,sps,{},weekly_part=True))
print(t); print(f"→ {len(t.splitlines())} реда · {len(t)} знака")

print(); print("="*72); print("СТАР · БОТЪТ СПА (3ч 47мин)"); print("="*72)
t = ч(lb._спал_msg(227,"2026-08-21T06:13:00+00:00","2026-08-21T10:00:00+00:00"))
print(t); print(f"→ {len(t.splitlines())} реда · {len(t)} знака")
print(); print("="*72); print("СТАР · БОТЪТ СПА (52 мин)"); print("="*72)
t = ч(lb._спал_msg(52,"2026-08-21T09:08:00+00:00","2026-08-21T10:00:00+00:00"))
print(t); print(f"→ {len(t.splitlines())} реда · {len(t)} знака")

for sl in ("сутрин","следобед","вечер"):
    print(); print("="*72); print(f"СТАР · УИКЕНД · {sl}"); print("="*72)
    t = ч(lb._weekend_msg(sl,"2026-08-22"))
    print(t); print(f"→ {len(t.splitlines())} реда · {len(t)} знака")

print(); print("КОНСТАНТИ:", "СПАЛ_МИН=",lb.СПАЛ_МИН, "PIP=",lb.PIP, "SL_PIPS=",lb.SL_PIPS)
print("тишина_мерена:", st["_meta"]["тишина_мерена"])
