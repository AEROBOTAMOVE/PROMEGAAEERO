# -*- coding: utf-8 -*-
"""№39: санитито съди 0.2-сек котировка по 10-минутен бар — колко живи цени изхвърля?"""
import sys, json, collections
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb
rows=[json.loads(l) for l in open('live/live_journal.jsonl',encoding='utf-8') if l.strip()]
рей=[r for r in rows if r.get("spot_rejected")]
сн =[r for r in rows if r.get("saniti")]
print("ръна общо:", len(rows), "| с попълнена следа saniti:", len(сн),
      "| spot_rejected:", len(рей), f"({100*len(рей)/len(rows):.1f}%)")
изх=[r for r in сн if r.get("saniti",{}).get("мина") is False]
print("следи с «мина»=False:", len(изх))
if изх:
    import statistics as st
    d=[x["saniti"]["разлика"] for x in изх]; t=[x["saniti"]["допуск"] for x in изх]
    print("  разлика: медиана %.2f  макс %.2f" % (st.median(d), max(d)))
    print("  допуск : медиана %.2f  макс %.2f" % (st.median(t), max(t)))
    for x in изх[-5:]:
        print("  ", x["run_utc"], x["saniti"], "| bar_age_min", x.get("bar_age_min"))
# ВЪЗПРОИЗВЕЖДАНЕ на механизма с реални мащаби
print()
print("=== механизмът, пуснат ===")
# тих пазар: базис 6.0, среден диапазон на 5-те бара 1.2$ → допуск = max(6.0, 2.16)=6.0
for име, ref, spot_mid, base, rng, jump in (
    ("тих пазар, спот +5$ от очакваното", 4000.0, 4005.0, 6.0, 1.2, None),
    ("НОВИНА: барът е стар 10 мин, спотът е скочил +12$", 4000.0, 4012.0, 6.0, 1.2, None),
    ("същото, но със знание за скока (spot_jump=12)", 4000.0, 4012.0, 6.0, 1.2, 12.0),
    ("новина, барът вече я е видял (rng 8$)", 4000.0, 4012.0, 6.0, 8.0, None),
):
    сл={}
    r = lb._spot_sane({"mid":spot_mid,"bid":spot_mid-.1,"ask":spot_mid+.1}, ref, base, rng, jump, сл)
    print(f"  {име:52s} → {'ЗАПАЗЕН' if r else 'ИЗХВЪРЛЕН'} {сл}")
