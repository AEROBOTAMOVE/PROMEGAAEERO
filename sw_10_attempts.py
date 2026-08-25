# -*- coding: utf-8 -*-
"""Находка 10: attempts «за журнал», но не влиза в никой журнал."""
import sys, json, tempfile, ast
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.argv = ["x"]
import live_bot as lb

# 1 · КОЙ ЧЕТЕ attempts? (AST — файлът е на кирилица, \w не хваща)
src = Path("live_bot.py").read_text(encoding="utf-8")
дърво = ast.parse(src)
чете, пише = [], []
for в in ast.walk(дърво):
    if isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) \
       and в.slice.value == "attempts":
        (пише if isinstance(в.ctx, ast.Store) else чете).append(в.lineno)
    if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) \
       and в.func.attr in ("get", "setdefault"):
        for a in в.args:
            if isinstance(a, ast.Constant) and a.value == "attempts":
                чете.append(в.lineno)
print("ПИШЕ attempts на редове:", sorted(set(пише)))
print("ЧЕТЕ attempts на редове:", sorted(set(чете)), "(само .get() вътре в самото увеличаване)")

# 2 · ИЗПЪЛНЕНИЕ: 3 провалени + 1 успешен рън, къде свършва attempts?
d = Path(tempfile.mkdtemp())
lb._send_raw = lambda text: "SOFT_FAIL: тест"
st = []
for i in range(3):
    lb._outbox_flush(d, [("signal", "карта %d" % i)] if i == 0 else [], st)
кола = [json.loads(l) for l in (d / "outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
print("\nслед 3 провала · outbox.jsonl:", кола)

lb._send_raw = lambda text: "SENT ok"
lb._outbox_flush(d, [], st)
print("\nsent_log.jsonl (журналът на ПРАТЕНИТЕ):")
for l in (d / "sent_log.jsonl").read_text(encoding="utf-8").splitlines():
    j = json.loads(l)
    print("  ключове:", sorted(j.keys()), "· има ли attempts:", "attempts" in j)
print("остатък в outbox.jsonl:", repr((d / "outbox.jsonl").read_text(encoding="utf-8")))
print("файлове в изхода:", sorted(p.name for p in d.iterdir()))
print("\nима ли 'attempts' в живия live/sent_log.jsonl:",
      "attempts" in Path("live/sent_log.jsonl").read_text(encoding="utf-8"))
print("има ли 'attempts' в живия live/live_journal.jsonl:",
      "attempts" in Path("live/live_journal.jsonl").read_text(encoding="utf-8"))
print("има ли 'attempts' в живия live/outbox.jsonl:",
      "attempts" in Path("live/outbox.jsonl").read_text(encoding="utf-8"))
