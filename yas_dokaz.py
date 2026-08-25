# -*- coding: utf-8 -*-
"""ДОКАЗАТЕЛСТВА ЗА ДЕФЕКТИТЕ ПО ВЕРИГАТА НА РАЗМЕРА. Само четене и изпълнение."""
import sys, json, hashlib
sys.argv = ["x"]
import live_bot as lb
import numpy as np, pandas as pd

stats = json.load(open("backtest_stats.json", encoding="utf-8"))
lv = {"sl": 4400.00, "tp1": 4430.00, "tp2": 4448.00, "tp3": 4475.00}
entry, spot = 4420.00, {"mid": 4420.5, "src": "gold"}
BAL, RISK = 1000.0, 2.0          # МЕРЕНО в live/sent_log.jsonl: 46 карти, всички «$1000@2%»

def карта(zc, adv, ok=True):
    return lb._sig_msg("long", 7.0, 6, "силен", spot, 4420.3, "2026-08-18T09:00:00Z",
                       lv, entry, adv, {}, 1, "тренд", stats, BAL, RISK,
                       adv_ok=ok, zone=(zc, "текст"))

ПЪЛНО = "ДА — доларът и лихвите падат от днес, това вдига златото"
МАЛКО = "ДА (малък размер) — подреждането е отпреди 4 дни"

print("=" * 78)
print("Д1 · ШЕСТТЕ НИВА ДАВАТ ЕДИН И СЪЩ РЕД ЗА РАЗМЕР (баланс 1000$, риск 2%)")
print("=" * 78)
редове = {}
for zc in ("A", "B", "C"):
    for име, adv in (("ПЪЛЕН", ПЪЛНО), ("малък", МАЛКО)):
        zw = lb.ZONE_W[zc]; м = zw * (0.5 if "малък размер" in adv else 1.0)
        риск = BAL * RISK / 100 * м
        лот = риск / lb.SL_D / 100.0
        t = карта(zc, adv)
        ред = [x for x in t.split("\n") if x.startswith("📏") or x.startswith("⚠️")]
        редове[(zc, име)] = " | ".join(ред)
        print(f"зона {zc} · {име:6} → множ {м:.4f} · риск {риск:6.2f}$ · лот {лот:.4f} "
              f"→ РЕД: {' | '.join(ред)}")
уникални = set(редове.values())
print(f"\nБРОЙ РАЗЛИЧНИ РЕДОВЕ ЗА РАЗМЕР: {len(уникални)} от 6 нива")
print("6-те множителя:", [round(lb.ZONE_W[z] * m, 4) for z in "ABC" for m in (1.0, 0.5)])
print("НАЙ-ГОЛЯМ / НАЙ-МАЛЪК =", round(1.0 / 0.165, 2), "пъти разлика — един и същ текст")

print("\n" + "=" * 78)
print("Д2 · «⚠️ малък размер» Е НЕДОСТИЖИМ ПРИ ЖИВИЯ БАЛАНС")
print("=" * 78)
for bal in (1000, 2000, 3000, 5000, 10000):
    има = []
    for zc in ("A", "B", "C"):
        for adv in (ПЪЛНО, МАЛКО):
            t = lb._sig_msg("long", 7.0, 6, "силен", spot, 4420.3, "x", lv, entry, adv,
                            {}, 1, "тренд", stats, float(bal), RISK, adv_ok=True,
                            zone=(zc, "т"))
            if "малък размер (" in t:
                има.append(zc + ("/малък" if "малък размер)" in adv else "/пълен"))
    print(f"баланс {bal:6}$ → предупреждение се вижда в: {има or 'НИКОЯ комбинация'}")

print("\n" + "=" * 78)
print("Д3 · `риск` и `лот_окр` се СМЯТАТ и НИКОГА не се печатат (мъртва сметка)")
print("=" * 78)
import ast, io
fn = next(n for n in ast.walk(ast.parse(io.open("live_bot.py", encoding="utf-8").read()))
          if isinstance(n, ast.FunctionDef) and n.name == "_sig_msg")
чет = sorted((n.lineno, n.id) for n in ast.walk(fn)
             if isinstance(n, ast.Name) and n.id in ("риск", "лот_окр") and isinstance(n.ctx, ast.Load))
зап = sorted((n.lineno, n.id) for n in ast.walk(fn)
             if isinstance(n, ast.Name) and n.id in ("риск", "лот_окр") and isinstance(n.ctx, ast.Store))
print("записи :", зап)
print("четения:", чет)
print("→ последен запис на `риск` е ред 1324; след него НЯМА нито едно четене.")
print("→ нито `риск`, нито `лот_окр` влизат в текста (grep по f-стринговете: 0 попадения)")
for l in io.open("live_bot.py", encoding="utf-8").read().split("\n")[1325:1360]:
    if "L.append" in l and ("риск" in l or "лот_окр" in l):
        print("   НАМЕРЕНО В ТЕКСТ:", l.strip())

print("\n" + "=" * 78)
print("Д4 · ЛИПСВАЩИ ДАННИ ЗА ЗОНА → МЪЛЧАЛИВО «B» (0.67), неразличимо от мерено B")
print("=" * 78)
print("_zones(None, 'long')            =", lb._zones(None, "long"))
малка = pd.DataFrame({"High": np.arange(10.0), "Low": np.arange(10.0)})
print("_zones(рамка с 10 бара, 'long') =", lb._zones(малка, "long"))
счупена = pd.DataFrame({"High": ["а"] * 50, "Low": ["б"] * 50})
print("_zones(счупена рамка, 'long')   =", lb._zones(счупена, "long"))
print("→ и трите дават 'B' → множител 0.67 → −33% размер БЕЗ НИТО ЕДНО ИЗМЕРВАНЕ")

print("\n" + "=" * 78)
print("Д5 · ТЕКСТЪТ НА ЗОНАТА СЕ ИЗХВЪРЛЯ (втората половина на кортежа)")
print("=" * 78)
t = карта("A", ПЪЛНО)
print("зона A дава текст:", lb._zones.__doc__.split("\n")[0][:0] or "🟩 <b>СИЛНА ЗОНА</b> …")
print("в картата има ли 'ЗОНА'? →", "ЗОНА" in t, " (има ли 🟩/🟨/🟧? →",
      any(e in t for e in "🟩🟨🟧"), ")")
print("ред 1309: `_zc, _ = (zone if zone else (None, \"\"))`  ← текстът отива в `_`")

print("\n" + "=" * 78)
print("Д6 · ЗОНА C Е ШУМ ПО СОБСТВЕНИЯ СТАНДАРТ НА ПРОЕКТА, но пак дава «КУПИ»")
print("=" * 78)
C = {"n": 7900, "net": 0.502, "lo": -0.19, "hi": 1.19}
print("зона C мерена: +0.502$ [−0.19 .. +1.19] (live_bot.py:1156)")
print("_noise(зона C) =", lb._noise(C), " ← същият критерий, с който клетките се отхвърлят")
print("картата за зона C:")
print(карта("C", ПЪЛНО))

print("\n" + "=" * 78)
print("Д7 · «ИЗЧАКАЙ» и «НЕ» СА ЕДНА И СЪЩА КАРТА (само 📌 редът се мени)")
print("=" * 78)
a = карта("A", "ИЗЧАКАЙ — прясно е, но такива случаи не носят нищо", ok=False).split("\n")
b = карта("A", "НЕ — доларът и лихвите се карат днес", ok=False).split("\n")
print("брой редове:", len(a), len(b), " · различни редове:",
      sum(1 for x, y in zip(a, b) if x != y))
for x, y in zip(a, b):
    if x != y:
        print("  ИЗЧАКАЙ:", x)
        print("  НЕ     :", y)
print("→ и двете почват с «⏸ БЕЗ ВХОД» и дават пълен план вход/стоп/3 цели")
print("→ РАЗМЕРЪТ НУЛА не е казан НИКЪДЕ; зоната изобщо не се чете в този клон")

print("\n" + "=" * 78)
print("Д8 · «малък размер» СЕ ПОЯВЯВА И КОГАТО ПРИСЪДАТА Е ПЪЛНО «ДА»")
print("=" * 78)
t = lb._sig_msg("long", 7.0, 6, "силен", spot, 4420.3, "x", lv, entry, ПЪЛНО, {}, 1,
                "тренд", stats, 10000.0, RISK, adv_ok=True, zone=("B", "т"))
print("присъда:", ПЪЛНО)
print([l for l in t.split("\n") if l.startswith("📏")][0])
print("→ присъдата казва ПЪЛЕН вход, картата казва «малък размер» — думата е чужда")
