# -*- coding: utf-8 -*-
import sys, io, json, os, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
os.chdir(BASE)
import pandas as pd
L = pathlib.Path("live")
print("файлове в live/:", sorted(p.name for p in L.iterdir()))
print("brain_track.json съществува в продукцията?", (L/"brain_track.json").exists())
print()
rs = [json.loads(x) for x in (L/"brain_result.jsonl").read_text(encoding="utf-8").strip().split("\n") if x.strip()]
print("brain_result.jsonl записи:", len(rs))
d = []
for r in rs:
    try:
        h = (pd.Timestamp(r["затворен"]) - pd.Timestamp(r["отворен"])).total_seconds()/3600
    except Exception as e:
        h = None
    d.append((r.get("рамка"), r.get("изход"), h, r.get("резултат"), r.get("пари")))
    print(f"  рамка={r.get('рамка'):>5} изход={str(r.get('изход')):>5} часове={h if h is None else round(h,2):>6} "
          f"резултат={r.get('резултат')} пари={r.get('пари')} ключове={sorted(r.keys())[:0] or ''}")
hs = [x[2] for x in d if x[2] is not None]
print()
print("часове: n=%d min=%.2f медиана=%.2f max=%.2f" % (len(hs), min(hs), sorted(hs)[len(hs)//2], max(hs)))
бързи = [x[2] for x in d if x[0] in ("1мин","5м")]
бавни = [x[2] for x in d if x[0] not in ("1мин","5м")]
print("бързи (1мин/5м) n=%d max=%.2f  — праг 24ч" % (len(бързи), max(бързи) if бързи else -1))
print("бавни (15м+)   n=%d max=%.2f  — праг 72ч" % (len(бавни), max(бавни) if бавни else -1))
print("колко биха стигнали до изход ВРЕМЕ при 24/72ч:",
      sum(1 for f,_,h,_,_ in d if h is not None and h >= (24 if f in ("1мин","5м") else 72)))
print()
print("ключове на записите:", sorted({k for r in rs for k in r}))
