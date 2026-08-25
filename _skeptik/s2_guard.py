# -*- coding: utf-8 -*-
"""СКЕПТИК ТЕСТ 2 — «козметично ли е?»
А) КОЛКО СТРУВА реалистичната отрова (+1 ден часова зона) срещу абсурдната.
Б) СТОП-ПАЗАЧЪТ: guard се нулира само при `guard["date"] != date` (ред 3597).
   Ако date е замразен → «2 стопа → спирам до утре» става ЗАВИНАГИ, а ред 3832
   реже сигнала: `guard.get(new_dir,0) >= 2` → сделка НЕ се отваря. Това е ПАРИ.
Аргументи: път_до_бот  етикет  отрова"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import rig, hashlib

BOT, TAG, POISON = sys.argv[1], sys.argv[2], sys.argv[3]
rig.load(BOT, name="lb2_" + TAG)
rig.patch()
print(f"### {TAG} sha1={hashlib.sha1(Path(BOT).read_bytes()).hexdigest()[:16]} отрова={POISON}")
OUT = Path(__file__).parent / ("g_" + TAG)


def ден(now_iso, bar_end):
    rig.CFG.clear()
    rig.CFG.update(gold_end=bar_end, intra_end=now_iso[:10] + " 12:00", gold_px=4600.0)
    rig.set_now(now_iso)
    rig.run(OUT, argv_extra=["--send"])
    j = rig.last_journal(OUT)
    g = json.loads((OUT / "guard.json").read_text(encoding="utf-8"))
    пулс = any("pulse" in str(s) for s in j.get("status") or [])
    блок = g.get("long", 0) >= 2
    print(f"  {now_iso[:10]} bar={bar_end}  date={j['date']:10s} "
          f"guard={{date:{g.get('date')}, long:{g.get('long')}}}  "
          f"пулс={'ДА' if пулс else 'НЯМА'}  "
          f"ЛОНГ вход={'🔴 БЛОКИРАН (ред 3832)' if блок else 'зелен'}")


rig.fresh(OUT)
ден("2026-08-19T11:00:00", "2026-08-19")
print(f"--- ОТРОВЕН рън: Yahoo дава бар {POISON} ---")
ден("2026-08-20T11:00:00", POISON)
# Ботът САМ пише този запис на ред 3648 след 2 стопа в лонг.
# Форматът е точно този от ред 3598.
g = json.loads((OUT / "guard.json").read_text(encoding="utf-8"))
g["long"] = 2
(OUT / "guard.json").write_text(json.dumps(g), encoding="utf-8")
print(f"--- слагам 2 УДАРЕНИ СТОПА в лонг (както ги пише ред 3648): {g} ---")
print("--- Yahoo Е ЗДРАВ всеки следващ ден ---")
for d in ("2026-08-21", "2026-08-24", "2026-08-25", "2026-08-26", "2026-08-27"):
    ден(d + "T11:00:00", d)
