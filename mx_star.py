# -*- coding: utf-8 -*-
"""РЕНДИРА СТАРИТЕ карти: ЦЕЛ 2, ЦЕЛ 3, изход по време, обръщане, сянка-изход."""
import sys, io, json
sys.argv = ["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import live_bot as lb

E = 4358.00
LV = {"sl": 4358.00, "tp1": 4365.50, "tp2": 4370.00, "tp3": 4378.00}
LV0 = {"sl": 4338.00, "tp1": 4365.50, "tp2": 4370.00, "tp3": 4378.00}

def tr(hit, lv=None, opened="2026-07-22T09:39:00Z"):
    return {"sym": "XAUUSD", "direction": "long", "entry": E,
            "levels": dict(lv or LV), "hit": dict(hit), "opened": opened,
            "hit_px": {}}

WHEN = "2026-08-21T10:00:00Z"
SPOT = {"mid": 4370.00, "bid": 4369.8, "ask": 4370.2}

print("### КОНСТАНТИ")
print("PIP", lb.PIP, "| SL_PIPS", lb.SL_PIPS, "| TPS", lb.TPS, "| ДНИ_МАКС", lb.ДНИ_МАКС)
print("S_TPS", lb.S_TPS)
print()

cases = [
 ("ЦЕЛ 2", "tp2", tr({"tp1": True}), 4370.00, False, ""),
 ("ЦЕЛ 3 (ВСИЧКО ПРИБРАНО)", "tp3", tr({"tp1": True, "tp2": True}), 4378.00, False, "ДА — нова карта идва."),
 ("ИЗХОД ПО ВРЕМЕ · с взети ТП1+ТП2", "time", tr({"tp1": True, "tp2": True}), 4366.40, False, "НЕ — няма активен сигнал."),
 ("ИЗХОД ПО ВРЕМЕ · без нито една цел", "time", tr({}, LV0), 4341.20, False, "НЕ — няма активен сигнал."),
 ("ОБРЪЩАНЕ · с взета ТП1", "flip", tr({"tp1": True}), 4361.10, False,
  "обърна се на силен SHORT — новата карта идва след паузата (до 45 мин)"),
 ("ОБРЪЩАНЕ · без нито една цел", "flip", tr({}, LV0), 4352.30, False, "ДА — нова карта идва."),
]
for име, kind, t, px, gap, nl in cases:
    txt = lb._exit_msg(kind, t, px, WHEN, "спот", gap, spot=SPOT, next_line=nl)
    print(f"===== СТАР · {име} =====")
    print(txt)
    print(f"--- {len(txt.splitlines())} реда · {len(txt)} знака\n")

sh = [
 ("СЯНКА · ЦЕЛ 2", "tp2", tr({"tp1": True}), 4370.00, False),
 ("СЯНКА · ЦЕЛ 3", "tp3", tr({"tp1": True, "tp2": True}), 4378.00, False),
 ("СЯНКА · по време", "time", tr({"tp1": True}), 4362.00, False),
 ("СЯНКА · обръщане", "flip", tr({}, LV0), 4352.30, False),
 ("СЯНКА · стоп на нула", "sl", tr({"tp1": True}), 4358.00, False),
 ("СЯНКА · истински стоп с гап", "sl", tr({}, LV0), 4335.62, True),
]
for име, kind, t, px, gap in sh:
    txt = lb._shadow_exit_msg(kind, t, px, WHEN, "спот", gap, spot=SPOT)
    print(f"===== СТАР · {име} =====")
    print(txt)
    print(f"--- {len(txt.splitlines())} реда · {len(txt)} знака\n")

# сметките на ръка
for kind, hit, px in (("tp2", {"tp1": True}, 4370.00),
                      ("tp3", {"tp1": True, "tp2": True}, 4378.00),
                      ("time", {"tp1": True, "tp2": True}, 4366.40),
                      ("time", {}, 4341.20),
                      ("flip", {"tp1": True}, 4361.10),
                      ("flip", {}, 4352.30)):
    дол = (px - E) * 1
    ст, вз = lb._ladder_pnl(kind, hit, LV, E, 1, дол, {})
    print(f"ladder {kind:5s} hit={list(hit)} px={px} → дол={дол:+.2f} стълба={ст:+.2f} взети={вз}")
