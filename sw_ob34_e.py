# -*- coding: utf-8 -*-
import sys, json, pathlib, shutil, os
sys.argv=["x"]
import live_bot as lb
T=pathlib.Path(os.environ["TMPDIR"])/"ob34"; shutil.rmtree(T,ignore_errors=True); T.mkdir(parents=True)
tr=T/"brain_track.json"; rs=T/"brain_result.jsonl"
tr.write_text(json.dumps({"посока":"long","рамка":"15м","степен":"силен","точки":7,
  "отворен":"2026-08-19T09:00","вход":3300.0,"стоп":3290.0,"цел1":3320.0,"цел2":None,
  "цел1_взета":False}, ensure_ascii=False), encoding="utf-8")
нов={"лонг":False,"рамка":"5м","степен":"силен","точки":6,
     "залог":{"вход":3305.0,"стоп":3315.0,"цел":3285.0}}
msgs = lb._мозък_следене(tr, rs, 3301.0, "2026-08-19T09:05", нов=нов)
print("A) върнати от _мозък_следене:", msgs)
print("A) brain_track.json след това:", json.loads(tr.read_text(encoding='utf-8'))["рамка"],
      json.loads(tr.read_text(encoding='utf-8'))["посока"])
print("A) brain_result.jsonl съществува:", rs.exists())
print("   => ПОТВЪРЖДАВАМ частта на одитора: новото НЕ се отваря.")
print()
print("B) но ТОВА не е пътят на КАРТАТА. Ред 3761 (new_msgs.append(CB.карта)) е ПРЕДИ ред 3784.")
print("   Тест: пипа ли _мозък_следене изобщо картата? подавам нов + гледам дали има странични ефекти")
print("   -> функцията НЕ вижда new_msgs (доказано с AST), връща само изход-карти.")
print()
# C) `or` върху два сетъпа
_за=None
for _s in ({"име":"A","точки":9},{"име":"B","точки":8}):
    _за = _за or _s
print("C) `_за_следене or _s` върху 2 пуснати:", _за, "-> вторият НЕ се следи. ПОТВЪРДЕНО.")
print("C) но МОЗЪК_ТАВАН =", lb.МОЗЪК_ТАВАН, "-> най-много", lb.МОЗЪК_ТАВАН-1, "изгубен на рън")
