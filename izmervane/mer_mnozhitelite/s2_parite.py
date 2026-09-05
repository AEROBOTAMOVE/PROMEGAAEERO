# -*- coding: utf-8 -*-
"""s2 · ПАРИТЕ: с тегла срещу без тегла, СДВОЕНО, върху ЕДНИ И СЪЩИ входове.

Теглата НЕ менят коя сделка се отваря — те менят само РАЗМЕРА. Затова нетото
на всеки вход се играе ВЕДНЪЖ, а сравнението е чисто аритметично и напълно
сдвоено: същият вход, същият изход, различен размер.

ДВЕ РАЗЛИЧНИ ВЪПРОСА, две различни числа (смесването им е измама):
  А · «на карта, при същия базов риск»  Δ = средно(W·нето) − средно(нето)
      Това е парите, които собственикът вижда, ако не пипа базовия риск.
      Печели се и само от това, че по-малко пари стоят в губещи сделки.
  Б · «на единица риск»                 Δ = Σ(W·нето)/Σ(W) − средно(нето)
      Това пита ДРУГО: по-добър ли е доларът, СЛОЖЕН в риск, когато го
      разпределяш по теглата. Ако Б е нула, теглата не РАЗЛИЧАВАТ нищо —
      просто търгуват по-малко.

БАЗАТА (задължителна): същите тегла, положени върху СЛЕПИ входове — случаен
момент в СЪЩИЯ ден, същата посока, същата геометрия, 15 тегления. Ако теглата
работят еднакво добре върху случаен момент от деня, те съдят ДЕНЯ, не сигнала.

ПЛАЦЕБО: 2000 кръгови измествания на вектора W (пази струпването по дни).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

TUK = Path(__file__).resolve().parent
sys.path.insert(0, str(TUK))
import dvig                                                          # noqa: E402
import tegla                                                         # noqa: E402

T0 = time.time()
REPS = 4000


def лог(*a):
    print("[%6.1fs]" % (time.time() - T0), *a, flush=True)


def дв(m, lo, hi):
    зв = "✅" if lo > 0 else ("🔴" if hi < 0 else "⚪")
    return "%+7.3f$ [%+.3f, %+.3f] %s" % (m, lo, hi, зв)


class Б2:
    """Блоков бутстрап по търговски ден, СПОДЕЛЕН между всички сравнения."""

    def __init__(self, dayid, reps=REPS, seed=424242):
        self.u, self.inv = np.unique(dayid, return_inverse=True)
        self.k = len(self.u)
        rng = np.random.default_rng(seed)
        self.iz = rng.integers(0, self.k, size=(reps, self.k))

    def _S(self, v, ok):
        return np.bincount(self.inv[ok], weights=v[ok], minlength=self.k)

    def средно(self, v):
        ok = np.isfinite(v)
        S = self._S(v, ok); C = np.bincount(self.inv[ok], minlength=self.k).astype(float)
        bm = S[self.iz].sum(1) / np.maximum(C[self.iz].sum(1), 1)
        return float(v[ok].mean()), float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))

    def на_риск(self, num, den):
        ok = np.isfinite(num) & np.isfinite(den)
        S = self._S(num, ok); D = self._S(den, ok)
        bm = S[self.iz].sum(1) / np.maximum(D[self.iz].sum(1), 1e-12)
        return (float(num[ok].sum() / den[ok].sum()),
                float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5)))

    def разлика_на_риск(self, net, W):
        """Δ Б = Σ(W·нето)/Σ(W) − Σ(нето)/n, преизчислено ВЪВ ВСЯКО повторение."""
        ok = np.isfinite(net)
        Swn = self._S(W * net, ok); Sw = self._S(W, ok)
        Sn = self._S(net, ok); C = np.bincount(self.inv[ok], minlength=self.k).astype(float)
        a = Swn[self.iz].sum(1) / np.maximum(Sw[self.iz].sum(1), 1e-12)
        b = Sn[self.iz].sum(1) / np.maximum(C[self.iz].sum(1), 1)
        d = a - b
        точка = float((W * net)[ok].sum() / W[ok].sum() - net[ok].mean())
        return точка, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main():
    E = tegla.данни()
    B = dvig.лента()
    net = np.load(TUK / "net_6846.npy")
    гейт, _ = tegla.гейт_маска(E)
    dayid = tegla.ден_ид(E)

    # ---- базата: слепи входове, същия ден ------------------------------
    p_bl = TUK / "slepi_15.npy"
    if p_bl.exists():
        BL = np.load(p_bl)
        лог("слепи нета от кеш: %s" % (BL.shape,))
    else:
        лог("играя слепите (15 тегления × 6846) ...")
        BL, _ = dvig.слепи_нета(E.bar_index.values.astype(np.int64),
                                E.direction.values, B, ndraw=15)
        np.save(p_bl, BL)
        лог("готово")
    net_b = np.nanmean(BL, axis=0)

    print("=" * 78)
    print("s2 · ПАРИТЕ С ТЕГЛА СРЕЩУ БЕЗ ТЕГЛА  ·  сдвоено, едни и същи входове")
    print("=" * 78)
    print("геометрия: %s" % dvig.GEOM["name"])
    print("нето БЕЗ тегла: всички %.3f$ · слепи (база) %.3f$"
          % (np.nanmean(net), np.nanmean(net_b)))

    for име_поп, m in (("ВСИЧКИ 6846 входа", np.ones(len(E), bool)),
                       ("ГЕЙТ-ПУСНАТИТЕ", гейт)):
        b = Б2(dayid[m])
        nt = net[m]; nb = net_b[m]
        print("\n" + "=" * 78)
        print("%s   n=%d   дни=%d" % (име_поп, int(m.sum()), b.k))
        print("=" * 78)
        m0, l0, h0 = b.средно(nt)
        print("  БЕЗ тегла (пълен размер):        %s" % дв(m0, l0, h0))
        mb, lb_, hb = b.средно(nb)
        print("  БАЗА · сляп момент, без тегла:   %s" % дв(mb, lb_, hb))

        for име_z, zmap in tegla.ZONE_ВАРИАНТИ.items():
            W = tegla.множители(E, zone_w=zmap)["W"].values[m]
            print("\n  ── ZONE_W: %s ────────────────────────────" % име_z)
            print("     среден размер %.1f%% от пълния · пари в риск: %.1f%% от досегашните"
                  % (100 * W.mean(), 100 * W.mean()))
            # А · на карта
            dA = (W - 1.0) * nt
            mA, lA, hA = b.средно(dA)
            mw, lw, hw = b.средно(W * nt)
            print("     А · с тегла, на карта:        %s" % дв(mw, lw, hw))
            print("     А · Δ срещу без тегла:        %s" % дв(mA, lA, hA))
            # А върху БАЗАТА
            dAb = (W - 1.0) * nb
            mAb, lAb, hAb = b.средно(dAb)
            print("     А · Δ върху СЛЕПИ (база):     %s" % дв(mAb, lAb, hAb))
            mAd, lAd, hAd = b.средно(dA - dAb)
            print("     А · Δ НАД базата (сдвоено):   %s" % дв(mAd, lAd, hAd))
            # Б · на единица риск
            mB, lB, hB = b.разлика_на_риск(nt, W)
            print("     Б · Δ на единица риск:        %s" % дв(mB, lB, hB))
            mBb, lBb, hBb = b.разлика_на_риск(nb, W)
            print("     Б · същото върху СЛЕПИ:       %s" % дв(mBb, lBb, hBb))

            # плацебо: кръгово изместване на W
            rng = np.random.default_rng(20260902)
            n = len(W)
            бие_A = 0; бие_B = 0
            цA = np.nanmean(dA)
            цB = mB
            for _ in range(2000):
                sh = int(rng.integers(1, n))
                Wp = np.roll(W, sh)
                бие_A += float(np.nanmean((Wp - 1.0) * nt) >= цA)
                ok = np.isfinite(nt)
                бие_B += float((Wp * nt)[ok].sum() / Wp[ok].sum() - nt[ok].mean() >= цB)
            print("     ПЛАЦЕБО (2000 измествания): бият А в %d/2000 · Б в %d/2000"
                  % (бие_A, бие_B))


if __name__ == "__main__":
    main()
