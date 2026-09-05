# -*- coding: utf-8 -*-
"""k6_gejt_epohi.py — единствената доказана находка, разгледана отблизо.

ГЕЙТЪТ е ЕДИНСТВЕНОТО звено, чиито ПУСНАТИ бият СПРЕНИТЕ (Т2). Но клетките му
са измерени на СЪЩАТА лента (backtest_stats.json._meta: «114813 сделки, XAUUSD
1-мин bid/ask 2006-2026») — тоест находката е ВЪТРЕ В ИЗВАДКАТА по устройство.

Тук се пита само едно: държи ли се числото, като се разреже. По ЕПОХА и по
ПОСОКА. Разпадне ли се, «доказано» значи «напаснато».
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
sys.path.insert(0, str(TUK))
sys.path.insert(0, str(IZM / "mer_mnozhitelite"))
import konv                                                          # noqa: E402

REPS = 4000
T0 = time.time()


def зв(lo, hi):
    return "ДОКАЗАНО+" if lo > 0 else ("ДОКАЗАНО−" if hi < 0 else "недоказано")


def main():
    G, D, B = konv.данни()
    stats = json.load(open(konv.REPO / "backtest_stats.json", encoding="utf-8"))
    гейт = konv.Гейт(stats)
    Z = np.load(TUK / "baza_po_den.npz")
    BL, BS = Z["long"], Z["short"]
    nd = len(BL)
    n = len(D["dir"])
    day = np.where(D["dord_entry"] >= 0, D["dord_entry"], 0).astype(np.int64)
    посока = D["dir"]
    base = np.where(посока == 1, BL[day], np.where(посока == -1, BS[day], np.nan))
    base = np.where(D["dord_entry"] >= 0, base, np.nan)
    прев = D["net"] - base

    сд, ф, карти, убит = konv.бягай(D, konv.ЖИВА, гейт, B, записвай=True)
    ki = np.array([c[0] for c in карти])
    ok = np.array([c[3] for c in карти])
    v = прев[ki]; dd = day[ki]; pp = посока[ki]
    добри = np.isfinite(v)
    ki, ok, v, dd, pp = ki[добри], ok[добри], v[добри], dd[добри], pp[добри]
    ts = D["tsmin"][ki]
    среда = int(np.median(dd))
    rng = np.random.default_rng(31337)
    iz = rng.integers(0, nd, size=(REPS, nd), dtype=np.int32)

    def мери(m):
        if m.sum() == 0 or (ok & m).sum() == 0 or ((~ok) & m).sum() == 0:
            return None
        out = []
        for sel in (ok & m, (~ok) & m):
            S = np.bincount(dd[sel], weights=v[sel], minlength=nd)
            C = np.bincount(dd[sel], minlength=nd).astype(float)
            out.append((S, C, S.sum() / C.sum(), int(C.sum())))
        b = (out[0][0][iz].sum(1) / np.maximum(out[0][1][iz].sum(1), 1e-12)
             - out[1][0][iz].sum(1) / np.maximum(out[1][1][iz].sum(1), 1e-12))
        return (out[0][3], out[0][2], out[1][3], out[1][2], out[0][2] - out[1][2],
                np.nanpercentile(b, 2.5), np.nanpercentile(b, 97.5))

    print()
    print("Т7 · ГЕЙТЪТ, РАЗРЯЗАН · нето минус базата, блоков бутстрап по ден (%d)" % REPS)
    print("     ⚠ клетките на гейта са мерени на СЪЩАТА лента → всичко тук е "
          "ВЪТРЕ в извадката")
    print("%-26s %8s %9s %8s %9s %9s %-22s %s"
          % ("срез", "пуснати", "пуснати$", "спрени", "спрени$", "П−С", "95% интервал",
             "присъда"))
    срезове = [("ВСИЧКИ карти", np.ones(len(v), bool)),
               ("епоха 1 (по-старата половина)", dd <= среда),
               ("епоха 2 (по-новата половина)", dd > среда),
               ("само ЛОНГ карти", pp == 1),
               ("само ШОРТ карти", pp == -1)]
    for име, m in срезове:
        r = мери(m)
        if r is None:
            print("%-26s %8s  —" % (име, "0"))
            continue
        np_, mp, ns, ms, d, lo, hi = r
        print("%-26s %8s %+9.3f %8s %+9.3f %+9.3f [%+9.3f .. %+9.3f]  %s"
              % (име, format(np_, ","), mp, format(ns, ","), ms, d, lo, hi, зв(lo, hi)))
    print("     епоха 1 свършва на ден %d от %d (около средата на 22.6-те години)"
          % (среда, nd))


if __name__ == "__main__":
    main()
