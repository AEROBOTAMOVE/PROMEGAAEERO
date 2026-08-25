# -*- coding: utf-8 -*-
import sys, io, json, re
sys.argv=["x"]; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
import live_bot as lb
ч = lambda t: re.sub(r"</?(b|i|code)>","",t)

# 1 · дупка ПРЕЗ уикенда: стенно време срещу търговско
for a,b,ет in (("2026-08-07T20:00","2026-08-10T06:00","петък вечер → понеделник сутрин"),
               ("2026-08-06T15:36","2026-08-06T23:03","делнична, 447 мин"),
               ("2026-08-07T15:00","2026-08-10T08:00","петък следобед → понеделник")):
    т = lb._търговски_минути(a,b)
    стен = (lb.pd.Timestamp(b)-lb.pd.Timestamp(a)).total_seconds()/60
    print(f"{ет:38s} стенни {стен:7.0f} мин · търговски {т:7.0f} мин")
    if т >= lb.СПАЛ_МИН:
        print("   КАРТА:"); print("   " + ч(lb._спал_msg(т,a,b)).replace("\n","\n   "))
print()
# 2 · пулс с adv_ok=False при каращо се макро (реалният случай)
print("ПУЛС 09 · каращо се макро · adv_ok=False (реалният случай):")
t = ч(lb._pulse_msg("09",[("1д","long",5,"medium",None)],None,"long","НЕ",False,None,None,
     {"mid":4365.2},{"mid":65.15},{"долар":True,"лихви":True},False,False,
     macro_raw={"долар":0.0131,"лихви":-0.06},streaks={"long":0},stats=json.load(io.open("backtest_stats.json",encoding="utf-8"))))
print(t); print(f"→ {len(t.splitlines())} реда")
print()
# 3 · може ли ДВА пъти 👁 (adv_ok=True + разбъркано)?
print("грепва ли се adv_ok=True при mixed? — _advice_entry на живо:")
st = json.load(io.open("backtest_stats.json",encoding="utf-8"))
for д in ("long","short"):
    txt,ok = lb._advice_entry(д,1,st,None,False,0,"XAUUSD",False,None,None)
    print(f"  {д} streak=1 (mixed макро не влиза тук) → ok={ok} · {txt[:70]}")
print()
# 4 · заглавията на ПУЛС22 и РАВНОСМЕТКА — първи ред
p22 = ч(lb._pulse_msg("22",[("1д","long",5,"medium",None)],None,"long","x",False,None,None,
        {"mid":4365.2},None,{"долар":True},False,False,macro_raw={"долар":0.01,"лихви":0.05},
        streaks={"long":2},stats=st)).split("\n")[0]
import pathlib,tempfile
tmp=pathlib.Path(tempfile.mkdtemp())
(tmp/"live_journal.jsonl").write_text("",encoding="utf-8")
(tmp/"sent_log.jsonl").write_text("",encoding="utf-8")
d = ч(lb._digest_msg(tmp,"2026-08-21",None,None,None,None,{})).split("\n")[0]
print("ПУЛС 22 първи ред :", p22)
print("РАВНОСМЕТКА първи ред:", d)
print("ЕДНАКВИ ЛИ СА (без часа):", p22.split("·")[0].strip()==d.split("·")[0].strip())
print()
# 5 · digest при празни файлове
print("РАВНОСМЕТКА при 0 ръна:"); print(ч(lb._digest_msg(tmp,"2026-08-21",None,None,None,None,{})))
