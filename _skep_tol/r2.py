import sys
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import live_bot as lb
print("СУХИ_МАКС =", lb.СУХИ_МАКС, "| СУХИ_ПОВТОР_Ч =", lb.СУХИ_ПОВТОР_Ч)
print()
print("=== ПУСНАТА картата, която агентът предлага да се ДОБАВИ ===")
print(lb._сухо_msg(12, "живата цена се реже от санитито",
                   "2026-08-19T18:00:00", "2026-08-19T19:00:00"))
print()
print("=== jump_cap може ли да СВАЛИ допуска под базата? ===")
# base=17.886, но bar_rng мъничък → jump_cap = 2.5*0.5 = 1.25 << base
for rng, jump in ((0.5, 40.0), (0.5, 3.0), (2.14, 3.755), (None, 40.0)):
    sl = {}
    ref = 4409.72
    spot = {"bid": ref-0.2, "ask": ref+0.2, "mid": ref}   # разлика 0 → винаги минава
    lb._spot_sane(spot, ref, 17.886, bar_rng=rng, spot_jump=jump, следа=sl)
    print(f"  rng={rng!r:>6} jump={jump:>6} -> допуск={sl['допуск']:.3f} (база 17.886) "
          f"{'⚠️ ПОД базата!' if sl['допуск'] < 17.886 else 'OK, не пада под базата'}")
