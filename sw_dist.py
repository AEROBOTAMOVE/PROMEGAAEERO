# -*- coding: utf-8 -*-
import sys, json; sys.argv=["x"]
import live_bot as lb, pandas as pd
ts=[]
for p in ["live/archive/live_journal-2026-07.jsonl","live/live_journal.jsonl"]:
    for ln in open(p, encoding="utf-8"):
        ln=ln.strip()
        if ln:
            try: ts.append(str(json.loads(ln)["run_utc"]))
            except: pass
ts=sorted(set(ts))
g=[(pd.Timestamp(b)-pd.Timestamp(a)).total_seconds()/60 for a,b in zip(ts,ts[1:])]
s=pd.Series(g)
print("СТЕННИ дупки между съседни ръна (мин):")
print(f"  n={len(s)} медиана={s.median():.1f} p95={s.quantile(.95):.1f} p99={s.quantile(.99):.1f} МАКС={s.max():.1f} ({s.max()/60:.1f}ч)")
print(f"  дупки >24ч стенно: {(s>1440).sum()}   >12ч: {(s>720).sum()}   >8ч: {(s>480).sum()}")
# работи ли ботът през уикенда?
зат=sum(1 for t in ts if lb._market_closed(t))
print(f"\nръна при ЗАТВОРЕН пазар: {зат} от {len(ts)} ({100*зат/len(ts):.1f}%) -> ботът НЕ спира за уикенда")
# уикенд-преходи: последен петъчен -> първи понеделнишки
дни=pd.Series([pd.Timestamp(t).date() for t in ts]).value_counts().sort_index()
print("\nръна на ден (последни 30 дни):")
print(" ", " ".join(f"{d.strftime('%d.%m')}={n}" for d,n in дни.items()))
