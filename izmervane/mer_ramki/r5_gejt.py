# -*- coding: utf-8 -*-
"""r5_gejt.py - ПАРИТЕ през ЖИВИЯ гейт: старите входове срещу новите.

Гейтът е САМАТА функция lb._advice_entry (не преписана логика), с памет по
(посока, стрийк, връх, щит, пазач). Около нея стоят звената, които решават
дали сделката се ОТВАРЯ:
    · US-щит (вътре в гейта)
    · стоп-пазач: ПАЗАЧ_СТОПОВЕ стопа в прозорец ПАЗАЧ_ПРОЗОРЕЦ_Ч (живо 1 / 4ч)
    · ТАВАН_СДЕЛКИ едновременно отворени (живо 12)
Мерят се ТРИ свята:
    A · старите входове (ОБЩИ) през ДОСТАВЕНИТЕ клетки  = ботът ПРЕДИ ръчката
    B · новите входове (СВОИ) през ДОСТАВЕНИТЕ клетки    = ботът ДНЕС (ръчката е
        включена на 05.09, а клетките са от старото поведение)
    C · новите входове (СВОИ) през ПРЕИЗМЕРЕНИТЕ клетки   = след вграждането
Интервалите са блоков бутстрап ПО ДЕН, 5000 реплики, seed 20260905.
"""
from __future__ import annotations
import copy
import io
import json
import sys
import time
from pathlib import Path
import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
for p in (str(IZM / "mer_mnozhitelite"), str(IZM), str(REPO)):
    sys.path.insert(0, p)
import live_bot as lb                                                # noqa: E402

T0 = time.time()
REPS = 5000
SEED = 20260905


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


class Гейт:
    def __init__(self, stats):
        self.stats = stats
        self._m = {}

    def __call__(self, посока, streak_n, dd20, shield, guard_n):
        k = (посока, int(streak_n),
             bool(np.isfinite(dd20) and dd20 < lb.NEAR_HIGH_DD20),
             bool(shield), int(guard_n))
        r = self._m.get(k)
        if r is None:
            _, ok = lb._advice_entry(посока, int(streak_n), self.stats, None,
                                     bool(shield), int(guard_n), sym="XAUUSD",
                                     stale_price=False,
                                     dd20=(float(dd20) if np.isfinite(dd20) else None))
            r = bool(ok)
            self._m[k] = r
        return r


def конвейер(E, N, етикет, гейт, пазач=True, cap=None):
    cap = lb.ТАВАН_СДЕЛКИ if cap is None else cap
    ts = E[етикет + "_ts"]
    d = E[етикет + "_dir"]
    stl = E[етикет + "_stl"]
    sts = E[етикет + "_sts"]
    dd20 = E[етикет + "_dd20"]
    ush = E[етикет + "_ush"]
    dord = E[етикет + "_dord"]
    net = N[етикет + "_net"]
    exts = N[етикет + "_exts"]
    kind = N[етикет + "_kind"]
    отворени = []
    g_n = {"long": 0, "short": 0}
    g_t = {"long": None, "short": None}
    взети = []
    for i in range(len(ts)):
        сега = int(ts[i])
        жив = []
        for t in отворени:
            if t[0] <= сега:
                if t[2] == 1:                      # истински стоп без взета цел
                    g_n[t[1]] += 1
                    g_t[t[1]] = t[0]
            else:
                жив.append(t)
        отворени = жив
        dn = "long" if d[i] == 1 else "short"
        gn = 0
        if пазач and g_t[dn] is not None and g_n[dn] > 0:
            ч = (сега - g_t[dn]) / 60.0
            gn = g_n[dn] if (0 <= ч < lb.ПАЗАЧ_ПРОЗОРЕЦ_Ч) else 0
        s = int(stl[i] if dn == "long" else sts[i])
        if not гейт(dn, s, dd20[i], bool(ush[i]), gn):
            continue
        if len(отворени) >= cap:
            continue
        if not np.isfinite(net[i]):
            continue
        взети.append(i)
        отворени.append((int(exts[i]), dn, int(kind[i])))
    return np.array(взети, np.int64)


class Boot:
    def __init__(self, dayid, reps=REPS, seed=SEED):
        self.u = np.unique(dayid)
        self.k = len(self.u)
        rng = np.random.default_rng(seed)
        self.W = rng.multinomial(self.k, np.full(self.k, 1.0 / self.k),
                                 size=reps).astype(np.float64).T


def ci(day, v, u=None, W=None):
    uu, inv = np.unique(day, return_inverse=True)
    if W is None:
        rng = np.random.default_rng(SEED)
        W = rng.multinomial(len(uu), np.full(len(uu), 1.0 / len(uu)),
                            size=REPS).astype(np.float64).T
    S = np.bincount(inv, weights=v, minlength=len(uu))
    C = np.bincount(inv, minlength=len(uu)).astype(float)
    bm = (S @ W) / np.maximum(C @ W, 1e-12)
    return S.sum() / C.sum(), np.percentile(bm, 2.5), np.percentile(bm, 97.5), len(uu), S.sum()


def знак(lo, hi):
    return "ДОКАЗАН+" if lo > 0 else ("ДОКАЗАН-" if hi < 0 else "недоказана")


def main():
    E = np.load(TUK / "r2_vhodove.npz")
    N = np.load(TUK / "r3_neta.npz")
    st_ship = json.load(io.open(REPO / "backtest_stats.json", encoding="utf-8"))
    нови = json.load(io.open(TUK / "r4_kletki.json", encoding="utf-8"))
    st_new = copy.deepcopy(st_ship)
    st_new["fresh"] = {"long": нови["СВОИ"]["long"], "short": нови["СВОИ"]["short"]}
    лог("живи ръчки: ТАВАН_СДЕЛКИ=%d · ПАЗАЧ_ВКЛ=%s · ПАЗАЧ_СТОПОВЕ=%d · ПАЗАЧ_ПРОЗОРЕЦ_Ч=%.0f"
        " · МИН_ДНИ=%d · ГЕЙТ_ЛОНГ_НЕДОКАЗАНО=%s · ГЕЙТ_ШОРТ_НЕДОКАЗАНО=%s"
        % (lb.ТАВАН_СДЕЛКИ, lb.ПАЗАЧ_ВКЛ, lb.ПАЗАЧ_СТОПОВЕ, lb.ПАЗАЧ_ПРОЗОРЕЦ_Ч,
           lb.МИН_ДНИ, lb.ГЕЙТ_ЛОНГ_НЕДОКАЗАНО, lb.ГЕЙТ_ШОРТ_НЕДОКАЗАНО))
    st_mix = copy.deepcopy(st_ship)
    st_mix["fresh"] = {"long": нови["СМЕС"]["long"], "short": нови["СМЕС"]["short"]}
    светове = (("A · ОБЩИ линии · доставени клетки", "ОБЩИ", st_ship),
               ("B · СВОИ линии · доставени клетки", "СВОИ", st_ship),
               ("C · СВОИ линии · преизмерени клетки", "СВОИ", st_new),
               ("D · СМЕС (лекът) · доставени клетки", "СМЕС", st_ship),
               ("E · СМЕС (лекът) · преизмерени клетки", "СМЕС", st_mix))
    рез = {}
    for име, ет, stats in светове:
        for пазач in (True, False):
            г = Гейт(stats)
            взети = конвейер(E, N, ет, г, пазач=пазач)
            d = E[ет + "_dir"][взети]
            day = E[ет + "_dord"][взети]
            v = N[ет + "_net"][взети]
            m, lo, hi, дни, общо = ci(day, v)
            лог("%-42s пазач=%-5s сделки %6d (лонг %5d шорт %5d) дни %4d  "
                "%+7.3f$ [%+7.3f, %+7.3f] %s  общо %+9.0f$"
                % (име, "да" if пазач else "не", len(взети), int((d == 1).sum()),
                   int((d == -1).sum()), дни, m, lo, hi, знак(lo, hi), общо))
            if пазач:
                рез[име] = (взети, day, v, ет)
    # ---- сдвоено ПО ДЕН, върху ОБЕДИНЕНИЕТО на дните (ден без сделка = 0$) ----
    # Пресичането би излъгало: единият свят търгува в 2 464 дни, другият в 4 668.
    def суми(day, v, дни):
        m = {}
        for d_, x in zip(day, v):
            m[int(d_)] = m.get(int(d_), 0.0) + float(x)
        return np.array([m.get(int(x), 0.0) for x in дни])

    двойки = (("B − A · само ръчката РАМКИ_СВОИ_ЛИНИИ", светове[1][0], светове[0][0]),
              ("C − B · вграждането на новите клетки", светове[2][0], светове[1][0]),
              ("D − B · лекът върху ръчката", светове[3][0], светове[1][0]),
              ("E − B · лекът + новите клетки", светове[4][0], светове[1][0]),
              ("E − A · целият ход, край до край", светове[4][0], светове[0][0]))
    for име, к1, к2 in двойки:
        _, d1, v1, _ = рез[к1]
        _, d2, v2, _ = рез[к2]
        дни = np.union1d(np.unique(d1), np.unique(d2))
        δ = суми(d1, v1, дни) - суми(d2, v2, дни)
        rng = np.random.default_rng(SEED)
        W = rng.multinomial(len(дни), np.full(len(дни), 1.0 / len(дни)),
                            size=REPS).astype(np.float64).T
        bm = (δ @ W) / len(дни)
        лог("СДВОЕНО ПО ДЕН · %-38s %+8.3f$/ден [%+8.3f, %+8.3f] %s  (дни %d)"
            % (име, δ.mean(), np.percentile(bm, 2.5), np.percentile(bm, 97.5),
               знак(np.percentile(bm, 2.5), np.percentile(bm, 97.5)), len(дни)))


if __name__ == "__main__":
    main()
