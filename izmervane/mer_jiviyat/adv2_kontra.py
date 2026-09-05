# -*- coding: utf-8 -*-
"""adv2_kontra.py — АДВЕРСАРНА ПРОВЕРКА на mer.py.
Т-A: слипидж НА ПЪЛНЕЖ (net_per_fill) вместо плосък 0.02 на СДЕЛКА
Т-B: блоков бутстрап с блок 21 ТЪРГОВСКИ ДНИ (припокриващи се държания)
Т-C: разлагане на стъпало 6 по ВРАТА (нов ключ / TIER_UP / РЕ-ОФЕР)
Т-D: едновременни сделки — колко капитал иска всяко стъпало
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import jiv, potok, mer                                            # noqa: E402

REPS = 5000
SEED = 20260905


def блок_бутстрап(dayvals, dayids, блок, reps=REPS, seed=SEED):
    """Блоков бутстрап с блок от `блок` ПОСЛЕДОВАТЕЛНИ търговски дни."""
    u = np.unique(dayids)
    S = np.zeros(len(u)); C = np.zeros(len(u))
    pos = {d: j for j, d in enumerate(u)}
    for v, d in zip(dayvals, dayids):
        j = pos[d]; S[j] += v; C[j] += 1
    k = len(u)
    nb = int(np.ceil(k / блок))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, max(k - блок + 1, 1), size=(reps, nb))
    off = np.arange(блок)
    idx = (starts[:, :, None] + off[None, None, :]).reshape(reps, -1)
    idx = np.minimum(idx, k - 1)[:, :k]
    bs = S[idx].sum(1); bc = np.maximum(C[idx].sum(1), 1)
    bm = bs / bc
    return (float(S.sum() / max(C.sum(), 1)),
            float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5)), k)


def main():
    B = jiv.лента(); G = jiv.решетка(); D = potok.подготви(G)
    брой_дни = int(B["dord"][-1]) + 1
    години = (B["tsmin"][-1] - B["tsmin"][0]) / (60 * 24 * 365.25)
    ЖИВ = potok.жива_настройка()
    print("ЖИВА НАСТРОЙКА, прочетена СЕГА:", {k: v for k, v in ЖИВ.items() if k != "име"})

    С0 = dict(potok.СТАР)
    С6 = dict(С0, cap=ЖИВ["cap"], guard=True, guard_h=ЖИВ["guard_h"],
              guard_stops=ЖИВ["guard_stops"], cool_min=ЖИВ["cool_min"],
              cool_flip=ЖИВ["cool_flip"], reoffer=True,
              reoffer_h=ЖИВ["reoffer_h"], reoffer_h_fresh=ЖИВ["reoffer_h_fresh"],
              max_age=ЖИВ["max_age"], max_age_fresh=ЖИВ["max_age_fresh"],
              reoffer_lo=ЖИВ["reoffer_lo"], reoffer_hi=ЖИВ["reoffer_hi"],
              reoffer_tier=ЖИВ["reoffer_tier"])

    r0 = potok.пробег(D, B, С0, mer.геом_доставена)
    jiv.лог("стъпало 0 готово %d сделки" % len(r0["сделки"]))
    r6 = potok.пробег(D, B, С6, mer.геом_жива)
    jiv.лог("стъпало 6 готово %d сделки" % len(r6["сделки"]))

    print("\n" + "=" * 110)
    print("Т-A · СЛИПИДЖЪТ Е НА ПЪЛНЕЖ, НЕ НА СДЕЛКА (полето net_per_fill вече е в кода, НЕ СЕ ПОЛЗВА)")
    print("=" * 110)
    for име, r in (("0 · СТАР", r0), ("6 · ЖИВ", r6)):
        net = np.array([x[4] for x in r["сделки"]])
        npf = np.array([x[8] for x in r["сделки"]])
        nf = np.array([x[7] for x in r["сделки"]])
        print("  %-10s n=%6d  ср. пълнежи/сделка %.3f | по СДЕЛКА %+8.1f$ (/год %+7.2f$)"
              " | по ПЪЛНЕЖ %+8.1f$ (/год %+7.2f$)  разлика %+7.2f$/год"
              % (име, len(net), nf.mean(), net.sum(), net.sum() / години,
                 npf.sum(), npf.sum() / години, (npf.sum() - net.sum()) / години))

    v0 = mer.по_дни([(0, 0, 0, 0, x[8], 0, x[6]) for x in r0["сделки"]], брой_дни)
    v6 = mer.по_дни([(0, 0, 0, 0, x[8], 0, x[6]) for x in r6["сделки"]], брой_дни)
    d = v6 - v0
    жив = np.nonzero(np.abs(v0) + np.abs(v6) > 0)[0]
    m, lo, hi, дни = jiv.бутстрап_по_ден(d[жив], жив, REPS, SEED)
    print("  СТАР → ЖИВ при слипидж НА ПЪЛНЕЖ: Δ$/ден %+.4f [%+.4f..%+.4f] %s  Δ$/год %+.2f"
          % (m, lo, hi, jiv.присъда(lo, hi, дни), d.sum() / години))

    print("\n" + "=" * 110)
    print("Т-B · БЛОКЪТ. Държането е до 21 ТЪРГОВСКИ ДНИ → дните НЕ СА независими.")
    print("=" * 110)
    n0 = np.array([x[4] for x in r0["сделки"]]); d0 = np.array([x[6] for x in r0["сделки"]])
    n6 = np.array([x[4] for x in r6["сделки"]]); d6 = np.array([x[6] for x in r6["сделки"]])
    v0f = mer.по_дни(r0["сделки"], брой_дни); v6f = mer.по_дни(r6["сделки"], брой_дни)
    df = v6f - v0f; жив2 = np.nonzero(np.abs(v0f) + np.abs(v6f) > 0)[0]
    for блок in (1, 5, 21, 42):
        a = блок_бутстрап(n0, d0, блок); b = блок_бутстрап(n6, d6, блок)
        c = блок_бутстрап(df[жив2], жив2, блок)
        print("  блок %2dд | СТАР %+.3f [%+.3f..%+.3f] %-14s | ЖИВ %+.3f [%+.3f..%+.3f] %-14s | Δ/ден %+.3f [%+.3f..%+.3f] %s"
              % (блок, a[0], a[1], a[2], jiv.присъда(a[1], a[2], a[3]),
                 b[0], b[1], b[2], jiv.присъда(b[1], b[2], b[3]),
                 c[0], c[1], c[2], jiv.присъда(c[1], c[2], c[3])))

    print("\n" + "=" * 110)
    print("Т-C · СТЪПАЛО 6 ПО ВРАТА · откъде идват парите")
    print("=" * 110)
    вр = np.array([x[9] for x in r6["сделки"]])
    for v in ("нов ключ", "TIER_UP", "РЕ-ОФЕР"):
        м = вр == v
        if м.sum() == 0:
            continue
        nn = n6[м]; dd = d6[м]
        mm, lo, hi, дни = jiv.бутстрап_по_ден(nn, dd, REPS, SEED)
        print("  %-9s n=%6d  $/сделка %+.3f [%+.3f..%+.3f] %-14s общо %+8.1f$  /год %+7.2f$  дни=%d"
              % (v, м.sum(), mm, lo, hi, jiv.присъда(lo, hi, дни),
                 nn.sum(), nn.sum() / години, дни))

    print("\n" + "=" * 110)
    print("Т-D · ЕДНОВРЕМЕННИ СДЕЛКИ · колко капитал иска всяко стъпало")
    print("=" * 110)
    for име, r, cfg, gf in (("0 · СТАР (∞ таван, 5д)", r0, С0, mer.геом_доставена),
                            ("6 · ЖИВ (таван 12, 21д)", r6, С6, mer.геом_жива)):
        соб = []
        for x in r["сделки"]:
            i0 = x[1]; dr = x[2]
            g = gf(dr)
            a, b = jiv.прозорец(i0, g, B)
            соб.append((B["tsmin"][i0], 0))
        # брой отворени във всеки момент, по входните/изходните времена
        отв = []
        for x in r["сделки"]:
            i0 = x[1]
            отв.append(int(B["tsmin"][i0]))
        отв = np.array(отв)
        print("  %-24s сделки %6d · %5.2f сделки/търговски ден" % (име, len(r["сделки"]),
                                                                   len(r["сделки"]) / 5703.0))


if __name__ == "__main__":
    main()
