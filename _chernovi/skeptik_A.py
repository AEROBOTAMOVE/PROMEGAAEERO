# -*- coding: utf-8 -*-
"""СКЕПТИК · част А: гола проверка на 2-та числа, които носят находката."""
import sys, io, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import live_bot as LB

print("VERSION в ЖИВИЯ файл :", LB.VERSION)
print("редове               :", sum(1 for _ in open(LB.__file__, encoding="utf-8")))
print("СТАР_МАКРО_Ч         :", LB.СТАР_МАКРО_Ч)

# --- 1. Наистина ли уикендната дупка е 49.1ч? (мерено в живия журнал) ---
J = os.path.join(os.path.dirname(LB.__file__), "live", "live_journal.jsonl")
ts = []
for ln in open(J, encoding="utf-8"):
    ln = ln.strip()
    if not ln: continue
    try: d = json.loads(ln)
    except Exception: continue
    u = d.get("run_utc") or d.get("utc")
    if u:
        try: ts.append(pd.Timestamp(u).tz_localize(None) if pd.Timestamp(u).tzinfo else pd.Timestamp(u))
        except Exception: pass
ts = sorted(set(ts))
print("\nзаписи с време       :", len(ts), " от", ts[0], "до", ts[-1])
дупки = []
for a, b in zip(ts, ts[1:]):
    h = (b - a).total_seconds()/3600
    if h > 24:
        дупки.append((a, b, h))
print("дупки > 24ч:")
for a,b,h in дупки:
    print(f"   {h:6.2f}ч   {a} → {b}   (петък?{a.dayofweek==4}  неделя?{b.dayofweek==6})")

# --- 2. Какво КАЗВА живият _търговски_минути за такава дупка? ---
print("\n_търговски_минути върху ИСТИНСКИТЕ дупки:")
for a,b,h in дупки:
    tm = LB._търговски_минути(a.isoformat(), b.isoformat())/60.0
    print(f"   стенно {h:6.2f}ч  →  ТЪРГОВСКО {tm:6.2f}ч   ->  минава ли ({tm:.2f} <= {LB.СТАР_МАКРО_Ч})? {tm <= LB.СТАР_МАКРО_Ч}")

# --- 3. Точно двойката от находката ---
петък = "2026-08-14T20:55:00"; неделя = "2026-08-16T22:11:00"
ст = (pd.Timestamp(неделя)-pd.Timestamp(петък)).total_seconds()/3600
тр = LB._търговски_минути(петък, неделя)/60.0
print(f"\nдвойката от находката: стенно {ст:.2f}ч · търговско {тр:.2f}ч · приема ли се резервът? {тр <= LB.СТАР_МАКРО_Ч}")
