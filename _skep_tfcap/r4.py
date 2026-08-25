# -*- coding: utf-8 -*-
import json, collections, statistics
r=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
by=collections.defaultdict(list)
for x in r:
    if x.get("tf_basis") is None: continue
    by[str(x.get("date"))[:10]].append((float(x["tf_basis"]), float(x.get("bar") or 0)))
print("ден         n   медиана tf   цена     |tf|% от цена   таван max(120,3%)   запас до тавана")
for d in sorted(by):
    v=[a for a,_ in by[d]]; pr=[b for _,b in by[d] if b]
    med=statistics.median(v); c=(sum(pr)/len(pr)) if pr else 0
    cap=max(120.0, 0.03*c)
    print("%s %4d  %+8.2f  %7.0f   %6.2f%%        %7.2f        %7.2f$ (%.1f×)"
          % (d,len(v),med,c,(100*abs(med)/c if c else 0),cap,cap-abs(med),(cap/abs(med) if med else 0)))
# най-екстремната стойност изобщо
allv=[float(x["tf_basis"]) for x in r if x.get("tf_basis") is not None]
print("\nмакс |tf_basis| ЗА ЦЕЛИЯ ДНЕВНИК: %.3f   най-нисък дневен таван: %.2f  ->  ползвано %.1f%% от тавана"
      % (max(abs(a) for a in allv), 120.0, 100*max(abs(a) for a in allv)/120.0))
# бележки за заклещване?
kw=[x for x in r if any("извън диапазон" in str(n) or "ЗАКЛЮЧЕН" in str(n) or "не се пресмята" in str(n) for n in (x.get("notes") or []))]
print("ръна с бележка за отказ/заключване на контрактния базис:", len(kw))
