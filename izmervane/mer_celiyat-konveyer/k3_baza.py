# -*- coding: utf-8 -*-
"""k3_baza.py — БАЗАТА: случаен вход в СЪЩИЯ ден, в СЪЩАТА посока.

Без нея «спрените са по-лоши» не значи нищо: денят може да е бил лош за всички.
За всеки търговски ден и всяка посока се играят NDRAW случайни минути от деня с
ДОСТАВЕНАТА геометрия. Всеки чекпойнт после се сдвоява с базата на СВОЯ ден и
СВОЯТА посока — точно както иска правилото.

Защо по ДЕН, а не по вход: базата за 461 291 хипотетични входа × 15 тегления е
6.9 млн. сделки. Базата е функция само на (ден, посока) — 5 549 × 2 × 15 =
166 470 сделки дават СЪЩОТО сдвояване за 40× по-малко работа.

Сверка С4: базата на 6846-те доставени входа, смятана по ДЕН, срещу базата,
смятана ВХОД ПО ВХОД (dvig.слепи_нета) — трябва да дадат едно и също средно
в рамките на тегленето.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
sys.path.insert(0, str(TUK))
sys.path.insert(0, str(IZM / "mer_mnozhitelite"))
import dvig                                                          # noqa: E402

NDRAW = 15
SEED = 20260902
OUT = TUK / "baza_po_den.npz"
T0 = time.time()


def лог(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)


def main():
    B = dvig.лента()
    st, en = dvig.дни_индекс(B)
    nd = len(st)
    лог("търговски дни: %s" % format(nd, ","))
    rng = np.random.default_rng(SEED)
    L = np.full((NDRAW, nd), np.nan)
    S = np.full((NDRAW, nd), np.nan)
    for d in range(nd):
        lo, hi = int(st[d]), int(en[d])
        if hi - lo < 2:
            continue
        u = rng.integers(lo, hi, size=NDRAW)
        for q in range(NDRAW):
            i0 = int(u[q])
            r = dvig.една(i0, "long", float(B["oa"][i0]), dvig.GEOM, B)
            if r is not None:
                L[q, d] = r["net"]
            r = dvig.една(i0, "short", float(B["ob"][i0]), dvig.GEOM, B)
            if r is not None:
                S[q, d] = r["net"]
        if d % 500 == 0 and d:
            лог("   ден %s / %s" % (format(d, ","), format(nd, ",")))
    bl = np.nanmean(L, axis=0)
    bs = np.nanmean(S, axis=0)
    лог("база ЛОНГ  средно %+.3f$  (дни с число %s)"
        % (np.nanmean(bl), format(int(np.isfinite(bl).sum()), ",")))
    лог("база ШОРТ  средно %+.3f$  (дни с число %s)"
        % (np.nanmean(bs), format(int(np.isfinite(bs).sum()), ",")))
    лог("база ВСИЧКО средно %+.3f$" % np.nanmean(np.concatenate([bl, bs])))
    np.savez_compressed(OUT, long=bl, short=bs, long_all=L, short_all=S)
    лог("записано %s" % OUT)


if __name__ == "__main__":
    main()
