# -*- coding: utf-8 -*-
"""ПРОСЛЕДЯВАНЕ НА ВЕРИГАТА НА РАЗМЕРА — само четене, само изпълнение."""
import sys, json, itertools
sys.argv = ["x"]
import live_bot as lb

print("=== КОНСТАНТИ (прочетени от живия модул) ===")
print("ZONE_W          =", lb.ZONE_W)
print("МАЛЪК_РАЗМЕР_W  =", lb.МАЛЪК_РАЗМЕР_W)
print("PIP             =", lb.PIP)
print("SL_D (злато)    =", lb.SL_D)
print("S_SL (сребро)   =", lb.S_SL)
print("MIN_N           =", lb.MIN_N)

stats = json.load(open("backtest_stats.json", encoding="utf-8"))

lv = {"sl": 4400.00, "tp1": 4430.00, "tp2": 4448.00, "tp3": 4475.00}
entry = 4420.00
spot = {"mid": 4420.5, "src": "gold"}

ZONE_TXT = {"A": "🟩 <b>СИЛНА ЗОНА</b> — празнина под цената, чисто отгоре",
            "B": "🟨 зона отдолу, но има насрещна отгоре",
            "C": "🟧 без опора отдолу и с насрещна зона отгоре"}

ADVICES = [
    ("ДА",       "ДА — доларът и лихвите падат от днес, това вдига златото", True),
    ("ДА-малък", "ДА (малък размер) — макрото мълчи, само по цена", True),
    ("ИЗЧАКАЙ",  "ИЗЧАКАЙ — прясно е, но такива случаи не носят нищо", False),
    ("НЕ",       "НЕ — доларът и лихвите се карат днес", False),
]

def лот_и_риск(zc, малък, balance, risk_pct, sym="XAUUSD"):
    zw = lb.ZONE_W.get(zc, 1.0) if zc else 1.0
    риск = balance * risk_pct / 100.0 * zw * (lb.МАЛЪК_РАЗМЕР_W if малък else 1.0)
    ед = lb.SL_D if sym == "XAUUSD" else lb.S_SL
    дел = 100.0 if sym == "XAUUSD" else 5000.0
    лот = риск / ед / дел
    return zw, риск, лот

for balance, risk_pct in ((1000.0, 2.0), (10000.0, 2.0), (50000.0, 2.0)):
    print("\n" + "#" * 78)
    print(f"# БАЛАНС {balance:g}$ · РИСК {risk_pct:g}%   (по подразбиране в кода: 1000 / 2)")
    print("#" * 78)
    for zc in ("A", "B", "C"):
        for ключ, adv, ok in ADVICES:
            малък = "малък размер" in adv
            zw, риск, лот = лот_и_риск(zc, малък, balance, risk_pct)
            txt = lb._sig_msg("long", 7.0, 6, "силен", spot, 4420.3, "2026-08-18T09:00:00Z",
                              lv, entry, adv, {}, 1, "тренд", stats, balance, risk_pct,
                              adv_ok=ok, zone=(zc, ZONE_TXT[zc]))
            print("\n" + "─" * 78)
            print(f"ЗОНА {zc} · присъда {ключ}  →  ZONE_W={zw}  множител={zw*(0.5 if малък else 1.0):.4f}"
                  f"  риск={риск:.2f}$  лот={лот:.4f}  (окр {round(лот,2)})")
            print("─" * 78)
            print(txt)
