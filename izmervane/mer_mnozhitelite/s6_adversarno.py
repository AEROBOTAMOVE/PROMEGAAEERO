# -*- coding: utf-8 -*-
"""s6 · АДВЕРСАРНАТА ФАЗА ВЪРХУ ОЦЕЛЕЛИТЕ.

Досега пробвах МНОГО сравнения. Преброени точно:
  s2 · 2 популации × 3 варианта ZONE_W × 6 твърдения + 4 = 40 интервала
  s3 · 4 множителя × 2 въпроса × 2 (сурово / над базата) × 2 популации
       × 3 варианта, минус плоските празни клетки                = 88 интервала
  s4 · 12 кофи-теста × средно 4.3 интервала                      ≈ 52 интервала
  общо ≈ 180 интервала, върху ~24 РАЗЛИЧНИ хипотези
       (4 множителя × {принос, подредба} × 2 популации × 3 варианта).

Затова оцелелите се проверяват тук с:
  1) Бонферони: 95% → 99.79% интервал (α = 0.05/24)
  2) плацебо: 2000 кръгови измествания на СЪЩИЯ етикет (пази струпването по дни)
  3) ДВЕТЕ ЕПОХИ поотделно (2004-2014 · 2015-2026) — в този проект правило,
     което живее само в едната епоха, вече е падало три пъти
  4) ДВЕТЕ ПОСОКИ
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

TUK = Path(__file__).resolve().parent
sys.path.insert(0, str(TUK))
import tegla                                                         # noqa: E402
from s2_parite import Б2                                             # noqa: E402

АЛФА = 0.05 / 24.0        # Бонферони върху 24 различни хипотези
P_LO, P_HI = 100 * АЛФА / 2, 100 * (1 - АЛФА / 2)


def дв2(m, l95, h95, l99, h99):
    зв = "✅" if l95 > 0 else ("🔴" if h95 < 0 else "⚪")
    зв99 = "✅" if l99 > 0 else ("🔴" if h99 < 0 else "⚪")
    return "%+7.3f$  95%%[%+.3f,%+.3f]%s  99.79%%[%+.3f,%+.3f]%s" % (m, l95, h95, зв, l99, h99, зв99)


class Б3(Б2):
    def средно2(self, v):
        ok = np.isfinite(v)
        S = self._S(v, ok); C = np.bincount(self.inv[ok], minlength=self.k).astype(float)
        bm = S[self.iz].sum(1) / np.maximum(C[self.iz].sum(1), 1)
        return (float(v[ok].mean()),
                float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5)),
                float(np.percentile(bm, P_LO)), float(np.percentile(bm, P_HI)))


def двойка(име, vals, dayid, hi_m, lo_m, reps=8000):
    """Разлика между две кофи, с 95% и 99.79% интервал."""
    m = hi_m | lo_m
    b = Б3(dayid[m], reps=reps)
    v = vals[m]
    v_hi = np.where(hi_m[m], v, np.nan); v_lo = np.where(lo_m[m], v, np.nan)
    okh = np.isfinite(v_hi); okl = np.isfinite(v_lo)
    if okh.sum() < 30 or okl.sum() < 30:
        print("  %-46s n=%d/%d — под 30, не се съди" % (име, okh.sum(), okl.sum()))
        return
    Sh = np.bincount(b.inv[okh], weights=v_hi[okh], minlength=b.k)
    Ch = np.bincount(b.inv[okh], minlength=b.k).astype(float)
    Sl = np.bincount(b.inv[okl], weights=v_lo[okl], minlength=b.k)
    Cl = np.bincount(b.inv[okl], minlength=b.k).astype(float)
    d = (Sh[b.iz].sum(1) / np.maximum(Ch[b.iz].sum(1), 1e-9)
         - Sl[b.iz].sum(1) / np.maximum(Cl[b.iz].sum(1), 1e-9))
    т = float(np.nanmean(v_hi) - np.nanmean(v_lo))
    print("  %-46s n=%4d/%4d  %s"
          % (име, okh.sum(), okl.sum(),
             дв2(т, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)),
                 float(np.percentile(d, P_LO)), float(np.percentile(d, P_HI)))))


def плацебо(име, vals, етикет, reps=2000, seed=20260903):
    """Кръгово изместване на етикета — пази струпването по дни, чупи връзката."""
    ok = np.isfinite(vals)
    v = vals[ok]; lab = етикет[ok]
    цел = v[lab].mean() - v[~lab].mean()
    rng = np.random.default_rng(seed)
    n = len(v)
    бие = 0
    for _ in range(reps):
        sh = int(rng.integers(1, n))
        L = np.roll(lab, sh)
        if L.sum() == 0 or (~L).sum() == 0:
            continue
        бие += int((v[L].mean() - v[~L].mean()) >= цел)
    print("  ПЛАЦЕБО %-38s цел %+.3f$ · бият я %d от %d" % (име, цел, бие, reps))


def main():
    E = tegla.данни()
    net = np.load(TUK / "net_6846.npy")
    BL = np.load(TUK / "slepi_15.npy")
    net_b = np.nanmean(BL, axis=0)
    изл = net - net_b                      # нето МИНУС слепия ден
    dayid = tegla.ден_ид(E)
    d = E.direction.values
    под = (E.cN.values < E.sma200.values)
    прев = np.abs(E.ls.values.astype(int) - E.ss.values.astype(int))
    зона = E["зона"].values
    кл = E["клетка"].values
    гейт, _ = tegla.гейт_маска(E)
    год = pd.to_datetime(E["ден"]).dt.year.values
    епоха1 = год <= 2014
    епоха2 = год >= 2015
    L = d == "long"; S = d == "short"

    print("=" * 96)
    print("s6 · АДВЕРСАРНО · Бонферони 99.79%% (α=0.05/24) · плацебо · епохи · посоки")
    print("=" * 96)
    print("вертикалът «МИНУС слепия ден» = нето на входа минус средното на 15 случайни")
    print("момента в СЪЩИЯ ден, същата посока, същата геометрия.\n")

    print("── 1 · РЕЖИМ (_рw): «над SMA200» минус «под SMA200», ЛОНГ ─────────────")
    двойка("всички · сурово", net, dayid, L & ~под, L & под)
    двойка("всички · МИНУС слепия ден", изл, dayid, L & ~под, L & под)
    двойка("епоха 2004-2014 · МИНУС слепия ден", изл, dayid, L & ~под & епоха1, L & под & епоха1)
    двойка("епоха 2015-2026 · МИНУС слепия ден", изл, dayid, L & ~под & епоха2, L & под & епоха2)
    двойка("ГЕЙТ-пуснатите · МИНУС слепия ден", изл, dayid, гейт & L & ~под, гейт & L & под)
    двойка("ШОРТ (теглото не се прилага) · МИНУС базата", изл, dayid, S & ~под, S & под)
    плацебо("режим · ЛОНГ · минус базата", np.where(L, изл, np.nan), (~под))

    print("\n── 2 · ПРЕВЕС (_пw): «широк ≥3» минус «тесен ≤2» ──────────────────────")
    двойка("всички · сурово", net, dayid, прев >= 3, прев <= 2)
    двойка("всички · МИНУС слепия ден", изл, dayid, прев >= 3, прев <= 2)
    двойка("епоха 2004-2014 · МИНУС слепия ден", изл, dayid, (прев >= 3) & епоха1, (прев <= 2) & епоха1)
    двойка("епоха 2015-2026 · МИНУС слепия ден", изл, dayid, (прев >= 3) & епоха2, (прев <= 2) & епоха2)
    двойка("ЛОНГ · МИНУС слепия ден", изл, dayid, L & (прев >= 3), L & (прев <= 2))
    двойка("ШОРТ · МИНУС слепия ден", изл, dayid, S & (прев >= 3), S & (прев <= 2))
    двойка("ГЕЙТ-пуснатите · МИНУС слепия ден", изл, dayid, гейт & (прев >= 3), гейт & (прев <= 2))
    плацебо("превес · минус базата", изл, (прев >= 3))

    print("\n── 3 · МАЛЪК (_мw): «day1/fresh» минус «mixed/stale» ──────────────────")
    пресен = np.isin(кл, ("day1", "fresh"))
    двойка("всички · сурово", net, dayid, пресен, ~пресен)
    двойка("всички · МИНУС слепия ден", изл, dayid, пресен, ~пресен)
    двойка("ЛОНГ · МИНУС слепия ден", изл, dayid, L & пресен, L & ~пресен)
    двойка("ШОРТ · МИНУС слепия ден", изл, dayid, S & пресен, S & ~пресен)
    двойка("ГЕЙТ-пуснатите · МИНУС слепия ден", изл, dayid, гейт & пресен, гейт & ~пресен)
    плацебо("малък · минус базата", изл, пресен)

    print("\n── 4 · ЗОНА (_zw): «A» минус «C» (теглото твърди A > C) ───────────────")
    двойка("всички · сурово", net, dayid, зона == "A", зона == "C")
    двойка("всички · МИНУС слепия ден", изл, dayid, зона == "A", зона == "C")
    двойка("епоха 2004-2014 · МИНУС слепия ден", изл, dayid, (зона == "A") & епоха1, (зона == "C") & епоха1)
    двойка("епоха 2015-2026 · МИНУС слепия ден", изл, dayid, (зона == "A") & епоха2, (зона == "C") & епоха2)
    двойка("ГЕЙТ-пуснатите · МИНУС слепия ден", изл, dayid, гейт & (зона == "A"), гейт & (зона == "C"))
    плацебо("зона A−C · минус базата", np.where(зона != "B", изл, np.nan), (зона == "A"))

    print("\n── 5 · ПРОИЗВЕДЕНИЕТО КАТО ЦЯЛО, над базата, с Бонферони ──────────────")
    for име_поп, m in (("ВСИЧКИ 6846", np.ones(len(E), bool)), ("ГЕЙТ-ПУСНАТИТЕ", гейт)):
        for име_z, zmap in tegla.ZONE_ВАРИАНТИ.items():
            W = tegla.множители(E, zone_w=zmap)["W"].values[m]
            b = Б3(dayid[m], reps=8000)
            dA = (W - 1.0) * net[m]
            dAb = (W - 1.0) * net_b[m]
            r = b.средно2(dA - dAb)
            print("  %-16s %-20s Δ над базата: %s" % (име_поп, име_z, дв2(*r)))


if __name__ == "__main__":
    main()
