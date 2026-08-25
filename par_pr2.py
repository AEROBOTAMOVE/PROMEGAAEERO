# -*- coding: utf-8 -*-
import sys, json, io, copy
sys.argv=["x"]
import live_bot as lb

raw = json.load(io.open("backtest_stats.json", encoding="utf-8"))
lb.СРЕБРО_ВХОД = True
print("=== колко СРЕБЪРНИ клетки пускат вход при различен спред ===")
for spr in (0.03, 0.02, 0.01, 0.0):
    lb.СРЕБРО_СПРЕД = spr
    st = copy.deepcopy(raw)
    lb._сребро_разход(st, None)
    да = []
    for d in ("long","short"):
        for sn in (0,1,2,4,7):
            txt, ok = lb._advice_entry(d, sn, st, 0, False, 0, sym="XAGUSD")
            if ok:
                кофа = {0:"mixed",1:"day1"}.get(sn, "fresh" if sn<=3 else "stale")
                да.append(f"{d}/{кофа}")
    print("  спред %.2f$ → пускат: %d  %s" % (spr, len(да), sorted(set(да))))
    if spr==0.0:
        sv=st["silver"]
        for d in ("long","short"):
            for k in ("day1","fresh","stale","mixed"):
                c=sv[d].get(k) or {}
                print("      %-6s %-6s n=%-5s net=%-9s lo=%-9s hi=%-9s шум=%s" %
                      (d,k,c.get("n"),c.get("net"),c.get("lo"),c.get("hi"), lb._noise(c)))
lb.СРЕБРО_СПРЕД=0.03; lb.СРЕБРО_ВХОД=False

print("\n=== README срещу кода: ранг за «ГЛЕДАЙ» ===")
import importlib.util as ilu
from pathlib import Path
p=Path("brain/chart_brain.py")
s=ilu.spec_from_file_location("cb",p); cb=ilu.module_from_spec(s); s.loader.exec_module(cb)
СТ = cb.SL.СТЕПЕНИ
print("  СТЕПЕНИ:", list(enumerate(СТ)))
print("  МОЗЪК_РАНГ_ВХОД =", lb.МОЗЪК_РАНГ_ВХОД, "→ степен:", СТ[lb.МОЗЪК_РАНГ_ВХОД])
print("  README ред 77 казва: «прагът за «👁 ГЛЕДАЙ» е вдигнат на 🔥 СИЛЕН» =", СТ.index("🔥 СИЛЕН"))
print("  ПРАГОВЕ:", cb.SL.ПРАГОВЕ, " МОЗЪК_ПРАГ =", lb.МОЗЪК_ПРАГ, "→ степен:", cb.SL.f_степен(lb.МОЗЪК_ПРАГ))
print("  МАКС_ТОЧКИ:", cb.SL.МАКС_ТОЧКИ, " сбор на тавани:", sum(cb.SL.ТАВАН_ГРУПА.values()),
      " НАБЛЮДАВАН_МАКС:", cb.SL.НАБЛЮДАВАН_МАКС)
print("  брой условия в ТАБЛИЦА:", len(cb.SL.ТАБЛИЦА), "(докстрингът на b_сливане казва «20 условия»)")
