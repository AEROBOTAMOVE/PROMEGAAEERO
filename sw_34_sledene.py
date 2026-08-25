# -*- coding: utf-8 -*-
import sys, json, pathlib, tempfile
sys.argv=["x"]; import live_bot as lb
sys.stdout.reconfigure(encoding='utf-8')
out=pathlib.Path(tempfile.mkdtemp())
трак=out/"brain_track.json"; днев=out/"brain_result.jsonl"
# вече ИМА отворено следене (15м лонг), още далеч от стоп/цел
отворено={"посока":"long","рамка":"15м","степен":"✅","точки":15,"отворен":"2026-08-19T08:00",
          "вход":3300.0,"стоп":3290.0,"цел1":3310.0,"цел2":None,"цел1_взета":False}
трак.write_text(json.dumps(отворено,ensure_ascii=False),encoding="utf-8")
# идва ВТОРА пратена карта (друга рамка, друга посока)
нов={"рамка":"5м","посока":"short","лонг":False,"степен":"⚡","точки":20,
     "залог":{"вход":3305.0,"стоп":3315.0,"цел":3285.0}}
msgs=lb._мозък_следене(трак,днев,3301.0,"2026-08-19T10:00",нов=нов)
print("върнати карти:",msgs)
print("brain_track.json СЛЕД:",трак.read_text(encoding="utf-8"))
print("новата карта записана ли е някъде:",
      "5м" in трак.read_text(encoding="utf-8"),
      "· дневник съществува:",днев.exists())
print()
# и вторият случай: ДВЕ пратени карти в един рън — `_за_следене = _за_следене or _s`
src=open("live_bot.py",encoding="utf-8").read().splitlines()
print("live_bot.py:3767 →",src[3766].strip())
_за_следене=None
for _s in [{"име":"A"},{"име":"B"}]:
    _за_следене=_за_следене or _s
print("две пратени карти → следи се само:",_за_следене)
print("бележка за пропуснатата в кода:",
      [l.strip() for l in src[3768:3792] if "notes.append" in l])
