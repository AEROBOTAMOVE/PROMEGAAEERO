# -*- coding: utf-8 -*-
import sys, io, os, json, shutil, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE); os.chdir(BASE)
import live_bot as lb
print("БАР_САНИТИ_ПЦТ =", lb.БАР_САНИТИ_ПЦТ, "→ при злато 4591$ допускът е",
      round(lb.БАР_САНИТИ_ПЦТ*4591.465, 2), "$ · скокът на базиса е 30.22$")
БАР_H, БАР_L, БАР_C = 4648.0, 4646.4, 4647.2
СПОТ = 4591.465; Б1 = БАР_C - СПОТ

def сц(име, б_следене):
    SAND = pathlib.Path(BASE)/"_skep_posl2"/("q_"+име.replace(" ","_"))
    if SAND.exists(): shutil.rmtree(SAND)
    SAND.mkdir(parents=True)
    ф, дн = SAND/"bt.json", SAND/"br.jsonl"
    сур = {"вход":БАР_C,"стоп":БАР_C-10,"цел":БАР_C+10,"цел2":БАР_C+15}
    нов = {"посока":"long","рамка":"1час","степен":"злато","точки":9,"повод":"т","ниво":БАР_C,
           **сур, "залог":{k: round(v-Б1,2) for k,v in сур.items()}, "лонг":True}
    lb._мозък_следене(ф,дн,СПОТ,"2026-08-21T10:00",нов=нов,бар=(БАР_H-Б1,БАР_L-Б1))
    беж = []
    m = lb._мозък_следене(ф,дн,СПОТ,"2026-08-21T10:05",нов=None,
                          бар=(БАР_H-б_следене, БАР_L-б_следене), бележки=беж)
    print(f"  {име:30} карти={[t for t,_ in m] or 'НЯМА'}  бележки={беж or '—'}")

print()
сц("базисът не мърда",      Б1)
сц("ре-анкер +30.22",       Б1+30.22)
сц("ре-анкер -30.22",       Б1-30.22)
сц("дребно мърдане +5",     Б1+5)
