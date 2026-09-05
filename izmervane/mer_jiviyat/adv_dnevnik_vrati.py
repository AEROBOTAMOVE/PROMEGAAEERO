# -*- coding: utf-8 -*-
"""ЖИВИЯТ ДНЕВНИК сам казва през коя врата минава всяка карта.

`karta` в live_journal.jsonl носи ТОЧНО решението на живия бот:
   key · key_age_h · tier_up · reoffer · cool_ok · should · actionable
Тоест вратата не се МОДЕЛИРА — тя се ЧЕТЕ. Това е единствената пряка
проверка на «80.5% РЕ-ОФЕР» срещу самия бот.
"""
import json, collections
from pathlib import Path

П = Path(__file__).resolve().parent.parent.parent / "live" / "live_journal.jsonl"
r = [json.loads(l) for l in open(П, encoding="utf-8") if l.strip()]
r.sort(key=lambda d: d.get("run_utc", ""))
print("дневник %s → %s · %d ръна" % (r[0]["run_utc"], r[-1]["run_utc"], len(r)))

предх = None
бр = collections.Counter(); пратени = 0
for d in r:
    ka = d.get("karta")
    if not isinstance(ka, dict):
        continue
    if not ka.get("should"):
        предх = ka.get("key") if ka.get("actionable") else None
        continue
    пратени += 1
    нов = (ka.get("key") != предх)
    if ka.get("reoffer") and not нов:
        бр["РЕ-ОФЕР"] += 1
    elif ka.get("tier_up") and not нов:
        бр["TIER_UP"] += 1
    elif нов:
        бр["нов ключ"] += 1
    else:
        бр["друго"] += 1
    предх = ka.get("key")

print("ПРАТЕНИ КАРТИ (should=True): %d" % пратени)
for k, v in бр.most_common():
    print("   %-10s %4d = %5.1f%%" % (k, v, 100.0 * v / max(пратени, 1)))

# и второ броене, което НЕ зависи от моята реконструкция на «нов»:
r2 = collections.Counter()
for d in r:
    ka = d.get("karta")
    if isinstance(ka, dict) and ka.get("should"):
        r2["reoffer=%s" % bool(ka.get("reoffer"))] += 1
print("   --- голото поле на бота:", dict(r2))
