# -*- coding: utf-8 -*-
import json, collections, sys
sys.argv=["x"]; import live_bot as lb
rows=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
g=[r for r in rows if isinstance(r.get("gate"),dict)]
print("ръна с гейт:", len(g), "| ok=True:", sum(1 for r in g if r["gate"].get("ok")),
      "| ok=False:", sum(1 for r in g if not r["gate"].get("ok")))
print("причини (by):", collections.Counter(r["gate"].get("by") for r in g).most_common())
print()
print("== БИ ЛИ ВЛЯЗЪЛ, АКО СПОТЪТ БЕШЕ ПРИЕТ? ==")
print("   (пускам _advice_entry със СЪЩИТЕ dir/streak, но stale_price=False)")
stats=json.load(open("backtest_stats.json",encoding="utf-8"))
би=collections.Counter(); прич=collections.Counter()
for r in g:
    if r["gate"].get("by")!="стара цена": continue
    gg=r["gate"]; tr={}
    txt,ok=lb._advice_entry(gg.get("dir"), gg.get("streak") or 0, stats, None, bool(r.get("shield")),
                            0, sym="XAUUSD", stale_price=False, dd20=gg.get("dd20"), trace=tr)
    би[ok]+=1; прич[tr.get("by") or txt[:40]]+=1
print("  резултат:", dict(би))
print("  какво го спира ВМЕСТО това:", прич.most_common(5))
