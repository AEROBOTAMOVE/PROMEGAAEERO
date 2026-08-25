# -*- coding: utf-8 -*-
import sys, io, json, datetime as dt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rs = [json.loads(l) for l in open("live/brain_result.jsonl", encoding="utf-8") if l.strip()]
СИЛНИ = ("⚡ МНОГО СИЛЕН", "💎 РЯДЪК")   # = ранг >= МОЗЪК_РАНГ_ВХОД (5)
def свод(sel, име):
    r = [x["резултат"] for x in sel if x.get("резултат") is not None]
    if not r: print(име, "празно"); return
    д = sorted(set(str(x["отворен"])[:10] for x in sel))
    print(f"{име}: n={len(r)} · на плюс {sum(1 for x in r if x>0)} · сбор {sum(r):+.2f}$ "
          f"({sum(r)/0.10:+,.0f} пипса) · средно {sum(r)/len(r):+.2f}$ ({sum(r)/len(r)/0.10:+,.0f} пипса) "
          f"· дни {len(д)} ({д[0]}..{д[-1]})")
свод(rs, "ВСИЧКИ")
свод([x for x in rs if x.get("степен") in СИЛНИ], "САМО ⚡/💎 (тези, които днес стават ГЛЕДАЙ)")
свод([x for x in rs if x.get("степен") not in СИЛНИ], "ПОД прага")
