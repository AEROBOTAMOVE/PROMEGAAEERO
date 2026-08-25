# -*- coding: utf-8 -*-
import sys, json, pathlib, tempfile
sys.argv=["x"]; import live_bot as lb
sys.stdout.reconfigure(encoding='utf-8')
CB=lb.CB
out=pathlib.Path(tempfile.mkdtemp())

# 1) точно каквото прави main: карта в new_msgs, после навиване на часовника
_s={"рамка":"15м","посока":"long","ранг":5,"точки":20,
    "_чака_запис":("15м|long",{"ранг":5,"точки":20,"време":"2026-08-19T10:00"})}
_bstate={}
new_msgs=[("brain:15м:long","🧠 карта")]
_bstate["_последна_карта"]={"utc":"2026-08-19T10:00","ранг":5}
CB.запиши_застудяване(_s,_bstate)                # live_bot.py:3766
(out/"brain_state.json").write_text(json.dumps(_bstate,ensure_ascii=False),encoding="utf-8")

# 2) СУХ рън — точно `python live_bot.py --out live` без --send
st=[]
sent=lb._outbox_flush(out,new_msgs,st,dry=True)   # live_bot.py:3806 dry=not args.send
print("СУХ РЪН")
print("  реално пратени тагове :",sent)
print("  статуси               :",st)
print("  brain_state.json      :",(out/"brain_state.json").read_text(encoding="utf-8"))
print("  → часовникът е навит за карта с НУЛА доставки")

# 3) същото, но картата е УНИЩОЖЕНА от тавана (brain:* НЕ е в EXIT_TAGS)
out2=pathlib.Path(tempfile.mkdtemp())
стари=[{"tag":f"info{i}","text":"x","first_ts":"2026-08-19T00:00:00","attempts":0} for i in range(300)]
(out2/"outbox.jsonl").write_text("\n".join(json.dumps(m,ensure_ascii=False) for m in стари),encoding="utf-8")
lb._send_raw=lambda t:"SOFT_FAIL: тест"
_b2={}; CB.запиши_застудяване(_s,_b2)
(out2/"brain_state.json").write_text(json.dumps(_b2,ensure_ascii=False),encoding="utf-8")
st2=[]; sent2=lb._outbox_flush(out2,[("brain:15м:long","🧠 карта")],st2,dry=False)
rem=[json.loads(l) for l in (out2/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
print("\nПРЕЛЯЛА ОПАШКА")
print("  картата оцеля ли      :", any(m["tag"]=="brain:15м:long" for m in rem))
print("  пратени тагове        :", sent2)
print("  brain_state.json      :", (out2/"brain_state.json").read_text(encoding="utf-8"))
print("\nЗА СРАВНЕНИЕ — как е гейтнат digest в main (ред 3810):")
print("   ", [l.strip() for l in open("live_bot.py",encoding="utf-8").read().splitlines()[3809:3814]])
