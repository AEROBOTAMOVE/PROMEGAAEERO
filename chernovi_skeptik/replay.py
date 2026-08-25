# -*- coding: utf-8 -*-
"""СКЕПТИК: възпроизвеждам ли твърдението? Пускам РЕАЛНИЯ код върху РЕАЛНИЯ дневник."""
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
import pandas as pd
import live_bot as LB

print("ВЕРСИЯ на живия файл :", LB.VERSION)
print("СПАЛ_МИН            :", LB.СПАЛ_МИН)
print("СУХИ_МАКС           :", getattr(LB, 'СУХИ_МАКС', '<< НЯМА ГО >>'))
print("СУХИ_ПОВТОР_Ч       :", getattr(LB, 'СУХИ_ПОВТОР_Ч', '<< НЯМА ГО >>'))
print("има ли _сухо_msg    :", hasattr(LB, '_сухо_msg'))
print()

recs = []
for line in open('live/live_journal.jsonl', encoding='utf-8'):
    line = line.strip()
    if not line: continue
    try: d = json.loads(line)
    except Exception: continue
    if d.get('weekend'): continue
    if not d.get('run_utc'): continue
    recs.append(d)
recs.sort(key=lambda d: d['run_utc'])
print(f"делнични записа общо: {len(recs)}  ({recs[0]['run_utc']} .. {recs[-1]['run_utc']})")
print()

# ── 1) ПЪРВИЯТ БУДИЛНИК (твърдението: никога не стига 45 мин) ──
print("=== 1) ПЪРВИЯТ БУДИЛНИК (СПАЛ_МИН=%d) — с ИСТИНСКАТА _търговски_минути ===" % LB.СПАЛ_МИН)
from collections import defaultdict
maxgap = defaultdict(float); pali = defaultdict(int); brоy = defaultdict(int)
for i, d in enumerate(recs):
    brоy[d['run_utc'][:10]] += 1
    if i == 0: continue
    g = LB._търговски_минути(recs[i-1]['run_utc'], d['run_utc'])
    ден = d['run_utc'][:10]
    if g > maxgap[ден]: maxgap[ден] = g
    if g >= LB.СПАЛ_МИН: pali[ден] += 1
for ден in sorted(brоy)[-8:]:
    print(f"  {ден}  ръна={brоy[ден]:4d}  най-дълга дупка={maxgap[ден]:7.1f} търг.мин  палил={pali[ден]}")
print(f"  ОБЩО палвания на първия будилник за целия дневник: {sum(pali.values())}")
print()

# ── 2) СУХИ РЪНА: колко ръна без жива цена ──
print("=== 2) ЖИВА ЦЕНА (spot) по дни ===")
suh = defaultdict(int); tot = defaultdict(int)
for d in recs:
    ден = d['run_utc'][:10]; tot[ден] += 1
    if d.get('spot') is None: suh[ден] += 1
for ден in sorted(tot)[-8:]:
    print(f"  {ден}  {suh[ден]:4d} от {tot[ден]:4d} ръна БЕЗ жива цена")
print()

# най-дългата поредица
best = cur = 0; bs = be = cs = None
for d in recs:
    if d.get('spot') is None:
        if cur == 0: cs = d['run_utc']
        cur += 1
        if cur > best: best, bs, be = cur, cs, d['run_utc']
    else:
        cur = 0
print(f"най-дълга непрекъсната поредица без жива цена: {best} ръна  ({bs} → {be})")
print()

# ── 3) РЕПЛЕЙ на ВТОРИЯ будилник върху същите данни ──
print("=== 3) РЕПЛЕЙ на ВТОРИЯ БУДИЛНИК (СУХИ_МАКС=%s) ===" % getattr(LB,'СУХИ_МАКС','-'))
meta = {}
karti = []
for d in recs:
    now_utc = d['run_utc']
    spot_g = d.get('spot')
    spot_rejected_g = d.get('spot_rejected')
    if LB.СУХИ_МАКС > 0:
        if spot_g is not None:
            meta["сухи_ръна"] = 0; meta.pop("сухи_от", None)
        else:
            meta["сухи_ръна"] = int(meta.get("сухи_ръна", 0)) + 1
            meta.setdefault("сухи_от", meta.get("сухи_последно_жив") or now_utc)
            if meta["сухи_ръна"] >= LB.СУХИ_МАКС:
                _посл = meta.get("сухи_казано"); _мин = 999.0
                if _посл:
                    try: _мин = (pd.Timestamp(now_utc)-pd.Timestamp(_посл)).total_seconds()/60.0
                    except Exception: _мин = 999.0
                if _мин >= LB.СУХИ_ПОВТОР_Ч*60:
                    _пр = "живата цена се реже от санитито" if spot_rejected_g else "фийдът мълчи"
                    karti.append((now_utc, meta["сухи_ръна"], _пр))
                    meta["сухи_казано"] = now_utc
        if spot_g is not None:
            meta["сухи_последно_жив"] = now_utc
print(f"ПАЛВАНИЯ на втория будилник за целия дневник: {len(karti)}")
for t, br, pr in karti[:40]:
    print(f"   🔴 {t}  след {br:4d} сухи ръна  · {pr}")
if len(karti) > 40: print(f"   ... още {len(karti)-40}")
print()
print("=== 4) от тях в аварията 19-21.08 ===")
av = [k for k in karti if '2026-08-19' <= k[0][:10] <= '2026-08-21']
print(f"палвания в аварийния прозорец: {len(av)}")
for t, br, pr in av: print(f"   🔴 {t}  след {br} сухи ръна · {pr}")
