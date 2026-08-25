# -*- coding: utf-8 -*-
"""ЛОВ 1 · РАТЧЕТЪТ НА ДАТАТА:  date = max(date_raw, meta['date'])  — само напред.
Един бъдещ дневен бар от Yahoo -> meta['date'] заяжда в бъдещето ЗАВИНАГИ,
а всеки дневен пазач (пулс, равносметка, cq, guard) е окован за него."""
import sys, json
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/_chernovi")
import harness as H

H.patch()

def show(out, tag):
    m = json.load(open(out/"meta.json", encoding="utf-8"))
    g = json.load(open(out/"guard.json", encoding="utf-8")) if (out/"guard.json").exists() else {}
    print(f"  [{tag}] meta.date={m.get('date')!r} pulse_14={m.get('pulse_14')!r} "
          f"digest={m.get('digest')!r} guard.date={g.get('date')!r}")
    return m

# ---------- КОНТРОЛА: чист бот, без отрова ----------
print("=== КОНТРОЛА (никаква отрова) ===")
ctl = H.fresh("_chernovi/sand_ctl")
for now, gend in (("2026-08-20T11:00", "2026-08-20"), ("2026-08-21T11:00", "2026-08-21")):
    H.set_now(now)
    H.CFG.update(gold_end=gend, intra_end=gend+" 10:55", gold_px=4600.0, spot_mid=4600.0)
    H.run(ctl, ["--send"])
    r = H.last_journal(ctl)
    _p = [s for s in r["status"] if "pulse" in s]
    print(f"  {now}: date={r['date']}  пулс-статус={_p or 'НЯМА пулс карта'}")
    show(ctl, now)

# ---------- ОТРОВА: ЕДИН рън с бъдещ дневен бар ----------
print()
print("=== ОТРОВА: ЕДИН рън, в който Yahoo дава дневен бар с дата 2026-12-31 ===")
sb = H.fresh("_chernovi/sand_date")
H.set_now("2026-08-20T11:00")
H.CFG.update(gold_end="2026-12-31", intra_end="2026-08-20 10:55", gold_px=4600.0, spot_mid=4600.0)
H.run(sb, ["--send"])
r = H.last_journal(sb)
print(f"  рън 1 (отровен): date={r['date']}  статус={[s for s in r['status'] if 'pulse' in s]}")
show(sb, "след отровата")

print()
print("=== СЛЕД ОТРОВАТА: Yahoo Е ЗДРАВ, датите са НОРМАЛНИ ===")
for now, gend in (("2026-08-21T11:00", "2026-08-21"),
                  ("2026-08-24T11:00", "2026-08-24"),
                  ("2026-08-25T11:00", "2026-08-25")):
    H.set_now(now)
    H.CFG.update(gold_end=gend, intra_end=gend+" 10:55", gold_px=4600.0, spot_mid=4600.0)
    H.run(sb, ["--send"])
    r = H.last_journal(sb)
    _p = [s for s in r["status"] if "pulse" in s]
    print(f"  {now}: Yahoo дава {gend} -> ботът работи с date={r['date']}  "
          f"пулс={_p or 'НЯМА пулс карта'}")
    show(sb, now)

print()
print("=== ИМА ЛИ ПЪТ НАЗАД В КОДА? ===")
import subprocess, re
src = open(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live_bot.py", encoding="utf-8").read().splitlines()
for i, l in enumerate(src, 1):
    if 'meta["date"]' in l or "meta.get(\"date\"" in l or "date_raw" in l:
        print(f"  ред {i}: {l.strip()}")
