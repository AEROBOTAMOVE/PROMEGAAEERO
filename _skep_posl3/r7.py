# -*- coding: utf-8 -*-
import sys, io, json, os, pathlib, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE=r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0,BASE); os.chdir(BASE)
import live_bot as lb

d=pathlib.Path(tempfile.mkdtemp()); f=d/"brain_track.json"; j=d/"brain_result.jsonl"
# ЛОНГ, ЦЕЛ1 ВЕЧЕ ВЗЕТА (половината прибрана на +20$), после изтича по ВРЕМЕ на цена под входа
т={"посока":"long","рамка":"15м","степен":"🔥","точки":14,"отворен":"2026-08-01T00:00",
   "вход":4600.0,"стоп":4580.0,"цел1":4620.0,"цел2":4700.0,"цел1_взета":True}
f.write_text(json.dumps(т,ensure_ascii=False),encoding="utf-8")
lb._мозък_следене(f,j,4590.0,"2026-08-10T00:00",нов=None,бар=None)
зап=json.loads(j.read_text(encoding="utf-8").strip())
print("### Д · ЗАПИСЪТ, КОЙТО НОВИЯТ ИЗХОД «ВРЕМЕ» ОСТАВЯ В ЕДИНСТВЕНИЯ ФОРУЪРД-ТЕСТ")
print("   ", json.dumps(зап,ensure_ascii=False))
print("   ключ 'резултат' има ли?", "резултат" in зап, " · ключ 'пари':", зап.get("пари"))
print("   цел1 беше взета на +20.00$; честната стълба = 20/2 + (4590−4600)/2 = %.2f$" % (20/2 + (4590-4600)/2))
print("   записаното 'пари' = %s$  → разлика %.2f$ на ЕДИН запис" % (зап.get("пари"), зап.get("пари") - (20/2+(4590-4600)/2)))
print()
живи=[json.loads(l) for l in open("live/brain_result.jsonl",encoding="utf-8") if l.strip()]
print("### Д · как чете дневника всеки анализ досега (17-те живи записа ползват 'резултат'):")
print("   sum(r['резултат']) по живите =", round(sum(r["резултат"] for r in живи),2),"$ на",len(живи),"записа")
смес=живи+[зап]
print("   след ЕДИН запис 'време' същият сбор =", round(sum(r.get("резултат") or 0 for r in смес),2),
      "$ на",len(смес),"записа  → новият запис е НЕВИДИМ (брои се за 0)")
