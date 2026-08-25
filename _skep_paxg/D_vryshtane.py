# -*- coding: utf-8 -*-
"""D · КЛЮЧОВИЯТ въпрос: «ЗАВИНАГИ» ли е? Замразявам базиса 200 руна на резерва
(както твърди находката), после ЗЛАТНИЯТ ФИЙД СЕ ВРЪЩА. Колко руна му трябват
на СТАРИЯ (непоправен) код да се възстанови?"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import _skep_lb_pre as lb

ИСТИНА = 47.0
state = {"basis_g": 25.515, "basis_g_bar": 4400.0}
notes = []; bar = 4400.0
for i in range(200):
    bar += 1.3
    lb._basis_update(state, "basis_g", {"mid": bar - ИСТИНА, "src": "paxg-cb"}, bar,
                     notes, cap=lb._basis_cap(bar), now_utc=None)
print("след 200 руна резерва: базис = %.3f (истина %.1f), бележки %d" %
      (state["basis_g"], ИСТИНА, len(notes)))

print("\n--- swq се връща ---")
for i in range(1, 16):
    n2 = []
    bar += 1.3
    lb._basis_update(state, "basis_g", {"mid": bar - ИСТИНА, "src": "swq"}, bar,
                     n2, cap=lb._basis_cap(bar), now_utc="2026-08-21T12:00")
    следа = {}
    ok = lb._spot_sane({"mid": bar - ИСТИНА, "bid": 0, "ask": 0}, bar - state["basis_g"],
                       8.0, bar_rng=3.3, spot_jump=0.5, следа=следа)
    print("swq рун %d: базис=%.3f  разлика в санитито=%.2f$  спотът мина=%s  бележки=%s"
          % (i, state["basis_g"], следа["разлика"], следа["мина"], n2))
