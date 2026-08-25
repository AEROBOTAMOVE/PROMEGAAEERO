# -*- coding: utf-8 -*-
import sys, io, os, json, shutil, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE); os.chdir(BASE)
import live_bot as lb

SAND = pathlib.Path(BASE) / "_skep_posl2" / "sand"
if SAND.exists(): shutil.rmtree(SAND)
SAND.mkdir(parents=True)
файл = SAND / "brain_track.json"; дн = SAND / "brain_result.jsonl"

БАР_H, БАР_L = 4648.0, 4646.4          # ПЛОСЪК бар, пазарът не мърда
СПОТ = 4591.465                         # живата цена — СЪЩАТА в двата свята
СТАР, ИСТИНА = 25.515, БАР_H - 0.8 - СПОТ

# сетъпът се ПРАЩА, докато базисът е замразен на 25.515 → нивата се свалят с него
_изм_посл = СТАР
сур = {"вход": 4647.2, "стоп": 4637.2, "цел": 4657.2, "цел2": 4662.2}
залог = {k: round(v - _изм_посл, 2) for k, v in сур.items()}
нов = {"посока":"long","рамка":"1час","степен":"злато","точки":9,"повод":"тест",
       "ниво":4647.2, **сур, "залог": залог, "лонг": True}
print("базис при пращане =", СТАР, " → нива в «живата» скала:", залог)
print("истински базис    =", round(ИСТИНА,3), " скок =", round(ИСТИНА-СТАР,2), "$")
print()

# рън 1: отваря наблюдението, барът се чете със ЗАМРАЗЕНИЯ базис
бар1 = (БАР_H-СТАР, БАР_L-СТАР)
m = lb._мозък_следене(файл, дн, СПОТ, "2026-08-21T10:00", нов=нов, бар=бар1)
print("рън1 (замразен базис) карти:", [t for t,_ in m])
print("   brain_track.json:", json.loads(файл.read_text(encoding='utf-8')) if файл.exists() else "НЯМА")
print()
# рън 2: базисът се ПРЕЗАКОТВЯ. Спотът НЕ мърда, барът НЕ мърда.
бар2 = (БАР_H-ИСТИНА, БАР_L-ИСТИНА)
print("рън2: барът вече се чете", tuple(round(x,2) for x in бар2), "вместо", tuple(round(x,2) for x in бар1))
m2 = lb._мозък_следене(файл, дн, СПОТ, "2026-08-21T10:05", нов=None, бар=бар2)
print("   карти:", [t for t,_ in m2] or "НЯМА")
if дн.exists():
    for ln in дн.read_text(encoding="utf-8").strip().split("\n"):
        d = json.loads(ln)
        print("   ЗАПИСАН ИЗХОД:", d.get("изход"), "цена", d.get("цена_изход"), "пари", d.get("пари"))
print("   файлът стои ли още:", файл.exists())
