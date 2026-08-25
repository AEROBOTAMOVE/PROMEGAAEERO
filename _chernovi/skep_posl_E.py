# -*- coding: utf-8 -*-
"""СКЕПТИК·ПОСЛЕДИЦА — стъпка 5: КОЛКО СДЕЛКИ/КАРТИ мести замразеният базис.
Един и същ свят, две стойности: ИСТИНСКАТА и ЗАМРАЗЕНАТА отпреди 19 дни (-3.851)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H
import live_bot as lb

H.patch()
lb._spot = lambda instr="XAU/USD", **k: {"bid": H.CFG.get("spot_mid",4600.0)-0.2,
                                         "ask": H.CFG.get("spot_mid",4600.0)+0.2,
                                         "mid": H.CFG.get("spot_mid",4600.0),
                                         "src": "swq", "age_sec": 1.0}
_ист = lb._tf_basis

def пусни(тег, X, cfg, час):
    if X is None:
        lb._tf_basis = _ист
    else:
        def подмени(state, key, intra, daily, notes, days=20, cap=None, _v=X):
            if key == "tf_basis_g":
                state[key] = _v; return _v
            return _ист(state, key, intra, daily, notes, days=days, cap=cap)
        lb._tf_basis = подмени
    H.CFG.clear(); H.CFG.update(cfg)
    H.set_now(час)
    d = H.fresh("_skep_posl5/sw_" + тег)
    H.run(d)
    j = H.last_journal(d)
    return j.get("board"), len(H.SENT), bool(j.get("trade")), j.get("tf_basis")

сценарии = []
for i, (px, step) in enumerate([(4600, 0.5), (4600, -0.5), (3300, 0.2), (3300, -0.2),
                                (2100, 0.05), (2100, -0.05), (4600, 0.0), (3300, 0.0)]):
    for ден, час in (("2026-08-21", "2026-08-21T12:05:00+00:00"),  # само 1 час
                     ):
        сценарии.append((f"{i}_{ден}", dict(gold_end=ден, gold_px=px, gold_step=step,
                                            spot_mid=px, intra_end=ден + " 12:00"), час))

разл_борд = разл_карти = разл_сделка = 0
for тег, cfg, час in сценарии:
    b1, c1, t1, v1 = пусни(тег + "_ist", None, cfg, час)
    b2, c2, t2, v2 = пусни(тег + "_zamr", -3.851, cfg, час)
    d_b = (b1 != b2); d_c = (c1 != c2); d_t = (t1 != t2)
    разл_борд += d_b; разл_карти += d_c; разл_сделка += d_t
    if d_b or d_c or d_t:
        print(f"{тег}: истински={v1} замразен={v2} | борд различен={d_b} карти {c1}->{c2} сделка {t1}->{t2}")
        if d_b:
            for k in b1:
                if b1[k] != b2.get(k): print(f"      {k}: {b1[k]} -> {b2.get(k)}")
print()
print(f"СБОР по {len(сценарии)} сценария: борд различен {разл_борд}, "
      f"карти различни {разл_карти}, сделка различна {разл_сделка}")
