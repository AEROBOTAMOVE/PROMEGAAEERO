# -*- coding: utf-8 -*-
import sys, io, json, os, pathlib, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE=r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0,BASE); os.chdir(BASE)
import live_bot as lb, pandas as pd
нов = {"лонг": True, "рамка":"5м","степен":"🔥","точки":15,
       "залог":{"вход":4610.0,"стоп":4605.0,"цел":4620.0,"цел2":4630.0}}
база = {"посока":"long","рамка":"15м","степен":"🔥","точки":14,
        "вход":4600.0,"стоп":4500.0,"цел1":4700.0,"цел2":4800.0,"цел1_взета":False}

def проба(име, отворен, now="2027-06-01T12:00", махни=False):
    d=pathlib.Path(tempfile.mkdtemp()); f=d/"brain_track.json"; j=d/"brain_result.jsonl"
    т=dict(база)
    if махни: т.pop("отворен",None)
    else: т["отворен"]=отворен
    f.write_text(json.dumps(т,ensure_ascii=False),encoding="utf-8")
    for _ in range(300):
        lb._мозък_следене(f,j,4650.0,now,нов=нов,бар=(4652.0,4648.0))
    жив = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    прието = (жив or {}).get("рамка")=="5м"
    print("   %-42s -> файл:%s  ново прието:%s  дневник:%d" %
          (име, "има" if f.exists() else "изтрит",
           "ДА" if прието else "НЕ",
           (j.read_text(encoding='utf-8').count('\n') if j.exists() else 0)))
    return прието

print("### Б · ОСТАВА ЛИ ЗАКЛЮЧВАНЕ В НОВИЯ КОД (текущ v14.0)?")
проба("нормален ISO ('2026-01-01T00:00')", "2026-01-01T00:00")
проба("ключът 'отворен' ЛИПСВА", None, махни=True)
проба("'отворен' = null", None)
проба("'отворен' = боклук ('---')", "---")
проба("'отворен' с часова зона (+00:00)", "2026-01-01T00:00:00+00:00")
print()
print("   pd.Timestamp(None) =", repr(pd.Timestamp(None)))
try:
    print("   (now - NaT).total_seconds() =", (pd.Timestamp("2027-06-01T12:00")-pd.Timestamp(None)).total_seconds())
except Exception as e:
    print("   гърми:", type(e).__name__, e)
try:
    (pd.Timestamp("2027-06-01T12:00")-pd.Timestamp("2026-01-01T00:00:00+00:00"))
except Exception as e:
    print("   naive − tz-aware:", type(e).__name__, str(e)[:80])
