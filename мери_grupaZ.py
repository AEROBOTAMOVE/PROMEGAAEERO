# -*- coding: utf-8 -*-
"""
ИЗМЕРВАНЕ · ГРУПА «З» — ЧЕТИРИ УСЛОВИЯ ИЛИ ЕДНО, ПРЕБРОЕНО ЧЕТИРИ ПЪТИ?

Армията твърди: три от четирите условия в група «З» са една и съща дума.
Не му вярвам на дума — меря на ИСТИНСКИ XAUUSD барове.

Това има значение точно сега, защото вчера вдигнах прага за «👁 ГЛЕДАЙ» от
✅ ГОТОВ на 🔥 СИЛЕН — тоест реших по СТЕПЕНТА. Ако група «З» надува степента
с 2-3 точки от едно и също наблюдение, прагът не значи каквото мисля.
"""
import sys, warnings, itertools, collections
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
import pandas as pd, numpy as np

ПЪТ = "C:/Users/User/Downloads/ЛОЦО/f6_data/parquet/xauusd_1min_bid_ask.parquet"
df = pd.read_parquet(ПЪТ)
print(f"барове: {len(df):,} · колони: {list(df.columns)[:8]}")
print(f"период: {df.index[0]} → {df.index[-1]}")

# нормализираме до OHLC по mid
кол = {c.lower(): c for c in df.columns}
def взем(*имена):
    for н in имена:
        if н in кол:
            return df[кол[н]]
    return None

o = взем("open", "bid_open", "open_bid"); h = взем("high", "bid_high", "high_bid")
l = взем("low", "bid_low", "low_bid"); c = взем("close", "bid_close", "close_bid")
if o is None:
    print("НЕ разпознавам колоните:", list(df.columns)); sys.exit(2)
ao = взем("ask_open", "open_ask"); ah = взем("ask_high", "high_ask")
al = взем("ask_low", "low_ask"); ac = взем("ask_close", "close_ask")
if ac is not None:
    O, H, L, C = (o + ao) / 2, (h + ah) / 2, (l + al) / 2, (c + ac) / 2
else:
    O, H, L, C = o, h, l, c
барове = pd.DataFrame({"Open": O, "High": H, "Low": L, "Close": C}).dropna()
print(f"готови барове: {len(барове):,}")

import brain.b_сливане as SL
import brain.chart_brain as CB

# ── взимаме ПОСЛЕДНИТЕ N прозореца и гледаме четирите Z условия ──────────
N = 400
СТЪПКА = max(1, len(барове) // (N * 3))
прозорци = []
край = len(барове)
i = край
while len(прозорци) < N and i > 800:
    прозорци.append(барове.iloc[i - 800:i])
    i -= СТЪПКА * 3
print(f"прозорци за оценка: {len(прозорци)} (по 800 бара)")

Z = ["Z1_дискаунт_премиум", "Z2_хоризонти", "Z2b_единодушно", "Z3_извън_стойността"]
резултати = []
грешки = 0
for w in прозорци:
    for лонг in (True, False):
        try:
            с = CB.сканирай({"1мин": w}, праг=0, състояние=None)
        except Exception:
            грешки += 1
            break
        if not с:
            continue
        for сет in (с if isinstance(с, list) else [с]):
            у = (сет or {}).get("условия") or {}
            if any(k in у for k in Z):
                резултати.append(tuple(bool(у.get(k)) for k in Z))
    if грешки > 5:
        break

if not резултати:
    print("\nСканирането не върна условия в тази форма — пробвам директно сливането")
    sys.exit(3)

print(f"\nоценки с група «З»: {len(резултати)}")
print("=" * 70)
print("КОЛКО ПЪТИ ВСЯКО УСЛОВИЕ Е ВЯРНО")
print("=" * 70)
for j, к in enumerate(Z):
    n = sum(1 for r in резултати if r[j])
    print(f"  {к:24s} {n:5d} / {len(резултати)} = {n/len(резултати)*100:5.1f}%")

print("\n" + "=" * 70)
print("СЪВПАДАТ ЛИ ДВЕ ПО ДВЕ (100% = едно и също нещо)")
print("=" * 70)
for a, b in itertools.combinations(range(4), 2):
    еднакви = sum(1 for r in резултати if r[a] == r[b])
    п = еднакви / len(резултати) * 100
    знак = "🔴 ЕДНО И СЪЩО" if п >= 99 else ("🟡 почти" if п >= 90 else "различни ✅")
    print(f"  {Z[a][:18]:18s} ↔ {Z[b][:18]:18s} {п:5.1f}%  {знак}")

print("\n" + "=" * 70)
print("КОЛКО РАЗЛИЧНИ ОТПЕЧАТЪКА ДАВАТ ЧЕТИРИТЕ (макс 16)")
print("=" * 70)
c2 = collections.Counter(резултати)
print(f"  различни: {len(c2)} от 16 възможни")
for k, v in c2.most_common(8):
    print(f"    {v:5d} · {['✓' if x else '·' for x in k]}")
print(f"\n  средно точки от група «З»: {sum(sum(r) for r in резултати)/len(резултати):.2f} от 4")
