# -*- coding: utf-8 -*-
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))
os.environ.setdefault("TELEGRAM_TOKEN","x"); os.environ.setdefault("TELEGRAM_CHAT_ID","1")
import live_bot as LB, hashlib
print("sha:", hashlib.sha256(open("live_bot.py","rb").read()).hexdigest()[:8])

f, v = LB._reentry_ban, LB._reentry_verdict

def run(meta, guard, ден_карти, date, new_dir, streak):
    """копие 1:1 на живия ред: guard се нулира по ден_карти, банът се съди по date"""
    if guard.get("date") != ден_карти:
        guard = {"date": ден_карти, "long": 0, "short": 0}
    # външното чистене (ред ~3896) — сравнява с `date`
    if meta.get("reentry_ban"):
        ст = meta.get("reentry_ban") or {}
        if str(ст.get("date","")) != str(date):
            meta.pop("reentry_ban", None)
    забранен, защо = f(meta, new_dir, streak, ден=date)
    if забранен:
        return guard, (False, защо, "БАН")
    ok, why = v(new_dir, streak, False, guard.get(new_dir, 0))
    if not ok:
        f(meta, new_dir, streak, why=why, set_it=True, ден=date)
    return guard, (ok, why, "verdict")

print("\n=== ЗАСТОЯЛ ДНЕВЕН БАР: Yahoo стои на 19.08, календарът върви ===")
meta, guard = {}, {}
g, r = run(meta, {"date":"2026-08-19","long":2,"short":0}, "2026-08-19", "2026-08-19", "long", 2)
print(" 19.08 (2 стопа):", r, "| запис:", json.dumps(meta.get("reentry_ban"), ensure_ascii=False))
g, r = run(meta, g, "2026-08-20", "2026-08-19", "long", 2)   # НОВ календарен ден, СЪЩИЯТ бар
print(" 20.08 guard нулиран =", g, "→", r)
g, r = run(meta, g, "2026-08-21", "2026-08-19", "long", 2)   # ВТОРИ нов ден, същият бар
print(" 21.08 guard нулиран =", g, "→", r)
print(" запис след 3 дни:", json.dumps(meta.get("reentry_ban"), ensure_ascii=False))

print("\n=== КОНТРОЛА: барът върви заедно с календара ===")
meta2, guard2 = {}, {}
g, r = run(meta2, {"date":"2026-08-19","long":2}, "2026-08-19", "2026-08-19", "long", 2)
print(" 19.08:", r)
g, r = run(meta2, g, "2026-08-20", "2026-08-20", "long", 2)
print(" 20.08:", r, "| запис:", json.dumps(meta2.get("reentry_ban"), ensure_ascii=False))
