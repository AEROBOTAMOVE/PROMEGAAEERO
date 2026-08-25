# -*- coding: utf-8 -*-
import sys, io, json, re
sys.argv = ["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
st = json.load(io.open("backtest_stats.json", encoding="utf-8"))
for k in ("време_изход_проверено", "геометрия_проверена", "произход_на_числата", "важно"):
    print(f"--- _meta[{k}] ---")
    print(json.dumps(st["_meta"].get(k), ensure_ascii=False)[:1200])
    print()

s = io.open("live_bot.py", encoding="utf-8").read()
print("=== има ли помощниците от patch_trabi ===")
for им in ("def _бр(", "def _ппз(", "def _зона_текст(", "ДНИ_МАКС", "_zc, _zt", "_zc, _ =",
           "мерено=None, now_utc=None", '"дни": seg.get("дни")'):
    print(f"  {им!r:35s} → {s.count(им)}")
print()
print("=== F19-Т3 / обръщане в кода ===")
for m in re.finditer(r".{140}F19.{200}", s, re.S):
    print(m.group(0).replace("\n", " | ")[:360]); print("  ~~~")
print("=== ред 3141-3145 ===")
ред = s.split("\n")
for i, r in enumerate(ред, 1):
    if "САМО ПРЕМИУМ насрещен" in r or "exit:flip" in r:
        print(i, r)
