import sys, importlib
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import live_bot as lb
print("VERSION:", getattr(lb, "VERSION", "?"), "| файл:", lb.__file__)
print("SPOT_TOL_PCT =", lb.SPOT_TOL_PCT, " SPOT_TOL_MIN =", lb.SPOT_TOL_MIN)
print()
print("=== _spot_tol по цена (ПУСНАТО) ===")
for p in (1500, 2000, 2500, 3000, 4000, 4471, 4639, None, "хх"):
    print(f"  цена={p!r:>8} -> tol={lb._spot_tol(p):.3f}")
print()
# ТОЧНО сценарият на другия агент: 12.08.2026 16:02 UTC, bar=4471.5 basis=61.78 diff=13.7 rng=2.14 jump=3.755
bar, basis, diff, rng, jump = 4471.5, 61.78, 13.7, 2.14, 3.755
ref = bar - basis
mid = ref - diff                     # спот на 13.7$ ПОД очакваното
spot = {"bid": mid-0.2, "ask": mid+0.2, "mid": mid}
sl = {}
res = lb._spot_sane(spot, ref, lb._spot_tol(bar), bar_rng=rng, spot_jump=jump, следа=sl)
print("=== СЦЕНАРИЯТ НА АГЕНТА, пуснат през ТЕКУЩИЯ код ===")
print(f"  bar={bar} basis={basis} ref={ref:.2f} spot.mid={mid:.2f} diff={diff}")
print(f"  -> {'CUT' if res is None else 'PASS'} | следа={sl}")
print()
# и през СТАРАТА фиксирана база 8.0 за сравнение
sl2 = {}
res2 = lb._spot_sane(spot, ref, 8.0, bar_rng=rng, spot_jump=jump, следа=sl2)
print(f"  същото със СТАРАТА база 8.0 -> {'CUT' if res2 is None else 'PASS'} | допуск={sl2['допуск']}")
