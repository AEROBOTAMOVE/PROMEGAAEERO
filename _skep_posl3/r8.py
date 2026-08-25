# -*- coding: utf-8 -*-
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
os.chdir(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import pandas as pd, numpy as np
ls=[json.loads(l) for l in open("live/live_journal.jsonl",encoding="utf-8") if l.strip()]
B=sorted((pd.Timestamp(r["run_utc"]), float(r["basis"])) for r in ls if r.get("basis") is not None)
print("### Е · КОЛКО СЕ МЕСТИ БАЗИСЪТ ПРЕЗ ЖИВОТА НА ЕДНО НАБЛЮДЕНИЕ")
print("   n=%d базиса, %s → %s, диапазон %.2f..%.2f$" % (len(B),B[0][0],B[-1][0],min(b for _,b in B),max(b for _,b in B)))
ts=np.array([x[0].value for x in B]); bv=np.array([x[1] for x in B])
for ч in (1.58, 8.64, 24, 72):
    d=[]
    for i in range(len(bv)):
        j=np.searchsorted(ts, ts[i]+int(ч*3.6e12))
        if j<len(bv): d.append(abs(bv[j]-bv[i]))
    d=np.array(d)
    print("   за %5.2fч (n=%d): медиана %.2f$ · p95 %.2f$ · max %.2f$   [медианен стоп на наблюдение = 6.84$]"
          % (ч,len(d),np.median(d),np.percentile(d,95),d.max()))
