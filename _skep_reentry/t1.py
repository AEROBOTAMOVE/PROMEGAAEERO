# -*- coding: utf-8 -*-
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import live_bot as LB
import hashlib
print("sha live_bot.py:", hashlib.sha256(open("live_bot.py","rb").read()).hexdigest()[:8])

f = LB._reentry_ban
print("\n=== A · слагане на ден 1, проверка ден 1 и ден 2 ===")
meta = {}
print(" set ден1:", f(meta,"long",2,why="2 стопа днес в тази посока — спирам до утре",set_it=True,ден="2026-08-20"))
print(" запис:", json.dumps(meta.get("reentry_ban"), ensure_ascii=False))
print(" ден1 проверка:", f(meta,"long",2,ден="2026-08-20"))
print(" ден2 проверка (същият стрийк):", f(meta,"long",2,ден="2026-08-21"))
print(" запис след ден2:", json.dumps(meta.get("reentry_ban"), ensure_ascii=False))

print("\n=== B · СТАР запис БЕЗ дата (мигриран от v13.7) ===")
meta2 = {"reentry_ban":{"dir":"long","streak":2,"why":"2 стопа днес в тази посока — спирам до утре"}}
print(" ден2 проверка:", f(meta2,"long",2,ден="2026-08-21"))
print(" запис след:", json.dumps(meta2.get("reentry_ban"), ensure_ascii=False))

print("\n=== C · запис с date=None (ден=None при слагането) ===")
meta3 = {}
print(" set с ден=None:", f(meta3,"long",2,why="w",set_it=True,ден=None))
print(" запис:", json.dumps(meta3.get("reentry_ban"), ensure_ascii=False))
print(" проверка ден 2026-08-21:", f(meta3,"long",2,ден="2026-08-21"))
print(" запис след:", json.dumps(meta3.get("reentry_ban"), ensure_ascii=False))
