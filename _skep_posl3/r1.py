# -*- coding: utf-8 -*-
import sys, io, json, hashlib, os, pathlib, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE); os.chdir(BASE)
raw = open("live_bot.py","rb").read()
print("live_bot.py sha1:", hashlib.sha1(raw).hexdigest(), "байта:", len(raw), "редове:", raw.count(b"\n"))
import live_bot as lb
print("VERSION:", lb.VERSION)
print("МОЗЪК_ЧАСОВЕ_БЪРЗИ/БАВНИ:", getattr(lb,"МОЗЪК_ЧАСОВЕ_БЪРЗИ","НЯМА"), getattr(lb,"МОЗЪК_ЧАСОВЕ_БАВНИ","НЯМА"))

def mk(d, отворен="2026-01-01T00:00", рамка="15м"):
    f = d/"brain_track.json"; j = d/"brain_result.jsonl"
    т = {"посока":"long","рамка":рамка,"степен":"🔥","точки":14,
         "отворен":отворен,"вход":4600.0,"стоп":4500.0,"цел1":4700.0,"цел2":4800.0,"цел1_взета":False}
    f.write_text(json.dumps(т, ensure_ascii=False), encoding="utf-8")
    return f, j

нов = {"лонг": True, "рамка":"5м","степен":"🔥","точки":15,
       "залог":{"вход":4610.0,"стоп":4605.0,"цел":4620.0,"цел2":4630.0}}

print()
print("### А · ТОЧНО СЦЕНАРИЯТ НА НАХОДКАТА срещу ТЕКУЩИЯ файл (17 месеца)")
d = pathlib.Path(tempfile.mkdtemp()); f, j = mk(d)
msgs = []
for i in range(500):
    msgs = lb._мозък_следене(f, j, 4650.0, "2027-06-01T12:00", нов=нов, бар=(4652.0,4648.0))
print("   файлът съществува ли още?", f.exists())
if f.exists():
    т = json.loads(f.read_text(encoding="utf-8"))
    print("   държи:", {k: т.get(k) for k in ("посока","рамка","отворен","вход","стоп","цел1")})
    print("   новото прието ли е?", "да" if т.get("рамка")=="5м" else "НЕ")
print("   дневник редове:", (j.read_text(encoding="utf-8").count("\n") if j.exists() else 0))
if j.exists():
    for ln in j.read_text(encoding="utf-8").strip().split("\n"):
        r = json.loads(ln); print("   запис:", {k:r.get(k) for k in ("рамка","изход","цена_изход","пари","затворен")})
print("   карти от последния рън:", [m[0] for m in msgs])
