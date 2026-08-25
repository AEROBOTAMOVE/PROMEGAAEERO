# -*- coding: utf-8 -*-
"""ЛЪЖА-ТЕСТ · рендира ПРЕДЛОЖЕНИТЕ карти в сценарии, които кодът РЕАЛНО поражда."""
import sys, io, os, re, copy
sys.argv = ["x"]

_dev = open(os.devnull, "w"); _saved = sys.stdout; sys.stdout = _dev
import live_bot as lb
import mx_z9_final as z9
_keep = sys.stdout
sys.stdout = io.TextIOWrapper(_saved.buffer, encoding="utf-8", errors="replace")

def чист(t): return re.sub(r"<[^>]+>", "", t)

E = 4358.00
LV_ОРИГ = {"sl": 4338.00, "tp1": 4365.50, "tp2": 4370.00, "tp3": 4378.00}

def tr(hit, lv, hit_px=None, opened="2026-08-19T09:39:00"):
    return {"sym":"XAUUSD","direction":"long","entry":E,"levels":dict(lv),
            "hit":dict(hit),"opened":opened,"hit_px":dict(hit_px or {})}

print("="*78)
print("A · CATCH-UP BURST: ТП1 и ТП2 в ЕДИН рън.")
print("   live_bot.py 3389: trade_obj = copy.deepcopy(trade)  ← снимка ПРЕДИ track_trade")
print("   live_bot.py 3407: obj = dict(trade_obj); obj['hit']=cum_hit  ← levels СА СТАРИТЕ")
print("   значи lv['sl'] в картата за ТП2 е ОРИГИНАЛНИЯТ стоп, не входът")
print("="*78)
# точно каквото прави кодът: снимка преди, кумулативен hit след
снимка = tr({}, LV_ОРИГ)
обj = dict(снимка); обj["hit"] = {"tp1": True}; обj["hit_px"] = {"tp1": 4365.50}
print("СТАРА карта ТП1:"); print(чист(lb._exit_msg("tp1", dict(снимка, hit={}), 4365.50, "2026-08-21T10:00:00","спот",False)))
print()
print("НОВА карта 8 (ТП2) в СЪЩИЯ рън:")
print(чист(z9.нов_изход("tp2", обj, 4370.00, "2026-08-21T10:00:00", "спот", False, "")))
print("\n   entry =", E, " levels['sl'] =", обj["levels"]["sl"])

print("\n"+"="*78)
print("Б · ГАПНАТ СТОП НА ВХОДА (спот-път, фил по BID — live_bot.py 2691-2700)")
print("="*78)
o = tr({"tp1":True,"tp2":True}, {"sl":E,"tp1":4365.50,"tp2":4370.00,"tp3":4378.00},
       {"tp1":4365.50,"tp2":4370.00})
for фил in (4358.00, 4357.60, 4356.10):
    print(f"--- фил {фил} ---")
    print(чист(z9.нов_сянка("sl", o, фил, "2026-08-21T10:00:00", "спот", фил < 4357.9)))
    print()

print("="*78)
print("В · ГАП ПРЕЗ ЦЕЛТА (gap=True) — старите карти пишат «· с гап», новите?")
print("="*78)
o2 = tr({"tp1":True}, {"sl":E,"tp1":4365.50,"tp2":4370.00,"tp3":4378.00}, {"tp1":4366.90})
print("СТАРА сянка:"); print(чист(lb._shadow_exit_msg("tp2", o2, 4372.30, "2026-08-21T10:00:00","бар",True)))
print("\nНОВА сянка:"); print(чист(z9.нов_сянка("tp2", o2, 4372.30, "2026-08-21T10:00:00","бар",True)))
print("\nСТАРА изходна:"); print(чист(lb._exit_msg("tp2", o2, 4372.30, "2026-08-21T10:00:00","бар",True)))
print("\nНОВА изходна:"); print(чист(z9.нов_изход("tp2", o2, 4372.30, "2026-08-21T10:00:00","бар",True,"")))
