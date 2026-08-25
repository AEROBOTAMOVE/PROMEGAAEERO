# -*- coding: utf-8 -*-
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
os.chdir(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import pandas as pd, numpy as np

ls = [json.loads(l) for l in open("live/live_journal.jsonl", encoding="utf-8") if l.strip()]
S = [(pd.Timestamp(r["run_utc"]), float(r["spot"])) for r in ls if r.get("spot") is not None]
S.sort()
print("живи спот-наблюдения:", len(S), "от", S[0][0], "до", S[-1][0])

# ГЕОМЕТРИЯТА НА ИСТИНСКИТЕ НАБЛЮДЕНИЯ: разстояния вход→стоп и вход→цел от brain_journal
bj = [json.loads(l) for l in open("live/brain_journal.jsonl", encoding="utf-8") if l.strip()]
ds = [abs(float(r["живо_вход"])-float(r["живо_стоп"])) for r in bj if r.get("живо_вход") and r.get("живо_стоп")]
dt = [abs(float(r["живо_вход"])-float(r["живо_цел"]))  for r in bj if r.get("живо_вход") and r.get("живо_цел")]
print("истински разстояния (n=%d): стоп медиана %.2f$ (p5 %.2f, p95 %.2f) · цел медиана %.2f$ (p95 %.2f)"
      % (len(ds), np.median(ds), np.percentile(ds,5), np.percentile(ds,95), np.median(dt), np.percentile(dt,95)))

ts = np.array([x[0].value for x in S]); px = np.array([x[1] for x in S])

def dwell(band):
    """за всяко начало: часове до първо излизане от ±band$; None ако не излезе до края"""
    out = []
    n = len(px)
    for i in range(n):
        j = i+1
        while j < n and abs(px[j]-px[i]) < band:
            j += 1
        if j < n:
            out.append((ts[j]-ts[i])/3.6e12)
        else:
            out.append(None)
    return out

for band, име in ((np.median(ds), "медианният стоп"), (np.percentile(ds,95), "p95 стоп"), (100.0, "синтетичните 100$ от находката")):
    d = dwell(band)
    ок = [x for x in d if x is not None]
    непр = sum(1 for x in d if x is None)
    print()
    print("### банд ±%.2f$ (%s) — n=%d начала" % (band, име, len(d)))
    if ок:
        print("   часове до излизане: медиана %.2f · p95 %.2f · max %.2f" % (np.median(ок), np.percentile(ок,95), max(ок)))
        print("   ≥24ч: %d (%.2f%%)   ≥72ч: %d (%.2f%%)   не излиза до края на данните: %d"
              % (sum(1 for x in ок if x>=24), 100*sum(1 for x in ок if x>=24)/len(d),
                 sum(1 for x in ок if x>=72), 100*sum(1 for x in ок if x>=72)/len(d), непр))
