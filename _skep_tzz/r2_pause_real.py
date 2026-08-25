# -*- coding: utf-8 -*-
"""СКЕПТИК Р2: достижим ли е ИЗОБЩО клонът, който _cme_pause пази — по ЖИВИ данни."""
import json, io, sys, statistics as st
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "..")

r = [json.loads(l) for l in io.open("../live/brain_journal.jsonl", encoding="utf-8") if l.strip()]
r = [x for x in r if x.get("базис") is not None]
r.sort(key=lambda x: x["utc"])
print("записи с базис:", len(r), " от", r[0]["utc"], "до", r[-1]["utc"])

ALPHA = 0.25
скокове = []          # (utc, оценка на СУРОВИЯ скок now_b-old)
for a, b in zip(r, r[1:]):
    d = b["базис"] - a["базис"]
    скокове.append((b["utc"], d / ALPHA))     # обратно от EMA: now_b-old = ΔEMA/α

def праг(цена=4639.0):
    return max(8.0, 0.0040 * цена)

П = праг()
print(f"\nпраг _roll_jump при злато 4639$: {П:.2f}$")

абс = sorted(abs(x[1]) for x in скокове)
n = len(абс)
print(f"оценени скокове: {n}")
print(f"  p50 {абс[n//2]:.2f}$ · p95 {абс[int(n*0.95)]:.2f}$ · p99 {абс[int(n*0.99)]:.2f}$ · МАКС {абс[-1]:.2f}$")
над = [x for x in скокове if abs(x[1]) > П]
print(f"  над прага {П:.2f}$: {len(над)} от {n} = {100*len(над)/n:.2f}%")

# --- САМО в CME паузата (17:00-17:59 NY = 21:00-21:59 UTC лятно) ---
пауза = [x for x in скокове if x[0][11:13] == "21"]
print(f"\nв часа на CME паузата (21:xx UTC): {len(пауза)} наблюдения")
if пауза:
    ап = sorted(abs(x[1]) for x in пауза)
    m = len(ап)
    print(f"  p50 {ап[m//2]:.2f}$ · МАКС {ап[-1]:.2f}$")
    надп = [x for x in пауза if abs(x[1]) > П]
    print(f"  над прага: {len(надп)} от {m}")
    for u, v in надп[:10]:
        print(f"     {u}  {v:+.2f}$")
