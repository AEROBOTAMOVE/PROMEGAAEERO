# -*- coding: utf-8 -*-
import sys, os, json, io, datetime as dt
sys.argv=["x"]
import live_bot as lb

print("REOFFER_MAX_AGE_H =", lb.REOFFER_MAX_AGE_H, " СТОЯЩ_МАКС_Ч =", lb.СТОЯЩ_МАКС_Ч)
now = dt.datetime(2026,8,17,17,2,22, tzinfo=dt.timezone.utc).isoformat()
board=[("1час","long",6,"strong","СИЛЕН"),("4часа","long",6,"strong","СИЛЕН")]
best=("1час","long",6,"strong","СИЛЕН")
def card(macro, age):
    return lb._standing_msg("long", best, age, {"mid":4425.07}, 4425.0, 4425.07,
                            board, macro, {}, now)
print("\n=== A · МАКРОТО Е СМЕСЕНО (както в живия дневник) ===")
print(card({"миньори":True,"долар":True,"лихви":False}, 276.0))
print("\n=== B · МАКРОТО Е НАПЪЛНО ПОДРЕДЕНО (за лонг) ===")
print(card({"миньори":True,"долар":True,"лихви":True}, 276.0))
print("\n=== C · МАКРОТО Е ИЗЦЯЛО СРЕЩУ ===")
print(card({"миньори":False,"долар":False,"лихви":False}, 276.0))
