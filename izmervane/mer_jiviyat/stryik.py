# -*- coding: utf-8 -*-
"""stryik.py — КОЙ КАЛЕНДАР МЕРИ СТРИЙКА.

НАМЕРЕНО в тази сесия. Генераторът на живите клетки
(`scratchpad/mer_chestni_kletki.py`, чийто изход стои в
`backtest_stats.json → fresh`) смята стрийка върху индекс от
`sorted(E["day"].unique())` — тоест САМО дните, в които има вход (~2055),
а не всички търговски дни (5703). Следствия, ако е вярно:

  · `dxy.pct_change(20)` е «20 ВХОДНИ дни назад» ≈ 55 търговски дни
  · «стрийк N» брои поредни ВХОДНИ дни, не поредни календарни

Живият бот смята същото върху ПЪЛНАТА дневна история (`_hist`), и точно
това прави `k0_reshetka.py`.

ТУК ДВЕТЕ СЕ ПУСКАТ ЕДНА СРЕЩУ ДРУГА върху ЕДНИТЕ И СЪЩИ 6846 входа и
ЕДНАТА И СЪЩА жива геометрия. Ако версията «само входните дни» възпроизведе
записаните числа, диагнозата е доказана, а не предположена.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import jiv                                                        # noqa: E402
import mer                                                        # noqa: E402

F_DXY = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\dxy_yahoo_full.csv")
F_RR = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\DFII10.csv")


def кл(n):
    return "day1" if n == 1 else ("fresh" if 2 <= n <= 3 else
                                  ("mixed" if n == 0 else "stale"))


def стрийкове(индекс):
    dxy = pd.read_csv(F_DXY, parse_dates=["Date"]).set_index("Date")["Close"]
    rr = pd.read_csv(F_RR)
    rr["observation_date"] = pd.to_datetime(rr["observation_date"])
    rr["DFII10"] = pd.to_numeric(rr["DFII10"], errors="coerce")
    rr = rr.dropna().set_index("observation_date")["DFII10"]
    dx = dxy.reindex(индекс).ffill(); r = rr.reindex(индекс).ffill()
    d_ = (-(dx.pct_change(20))).shift(1)
    r_ = (-(r - r.shift(20))).shift(1)
    m_l = ((d_ > 0) & (r_ > 0)).fillna(False)
    m_s = ((d_ < 0) & (r_ < 0)).fillna(False)
    бяг = lambda s: s.groupby((~s).cumsum()).cumsum()          # noqa: E731
    return бяг(m_l), бяг(m_s)


def кофа_числа(net, дни_вс, маска, seed=20260902, nb=6000):
    v = net[маска]; d = дни_вс[маска]
    ок = np.isfinite(v); v, d = v[ок], d[ок]
    if len(v) < 20:
        return None
    у, inv = np.unique(d, return_inverse=True)
    S = np.bincount(inv, weights=v); C = np.bincount(inv).astype(float)
    rng = np.random.default_rng(seed)
    iz = rng.integers(0, len(у), size=(nb, len(у)))
    bm = S[iz].sum(1) / np.maximum(C[iz].sum(1), 1)
    return dict(n=int(len(v)), дни=int(len(у)), net=round(float(v.mean()), 3),
                lo=round(float(np.percentile(bm, 2.5)), 3),
                hi=round(float(np.percentile(bm, 97.5)), 3))


def main():
    B = jiv.лента()
    E = jiv.доставени_входове()
    n = len(E["bar_index"])

    sig = pd.to_datetime(E["signal_utc"], unit="us", utc=True)
    ден = (sig.tz_convert("America/New_York") + pd.Timedelta(hours=7)).normalize().tz_localize(None)
    ден = pd.DatetimeIndex(ден)

    # ── нетата при ЖИВАТА геометрия, 21 търговски дни (един път) ──────────
    net = np.full(n, np.nan)
    for p in range(n):
        d = str(E["direction"][p])
        r = jiv.бързо(int(E["bar_index"][p]), d, float(E["entry_px"][p]),
                      jiv.жива_геом(d, 21), B)
        if r is not None:
            net[p] = r["net"]
    jiv.лог("6846 сделки при живата геометрия · 21 търг. дни — готови")

    # ── ПЪЛЕН дневен календар (както прави живият бот и k0_reshetka) ──────
    # пълният набор дневни барове идва от ЛЕНТАТА: един ред на търговски ден
    dord = B["dord"]
    първи = np.searchsorted(dord, np.arange(int(dord[-1]) + 1), "left")
    tsmin = B["tsmin"][първи]
    дни_лента = pd.DatetimeIndex(
        pd.to_datetime(tsmin * 60_000_000_000).tz_localize("UTC")
        .tz_convert("America/New_York") + pd.Timedelta(hours=7)).normalize().tz_localize(None)
    пълен = pd.DatetimeIndex(sorted(set(дни_лента)))

    само_входни = pd.DatetimeIndex(sorted(set(ден)))
    jiv.лог("календар ПЪЛЕН %d дни · САМО ВХОДНИ %d дни (%.2f×)"
            % (len(пълен), len(само_входни), len(пълен) / len(само_входни)))

    записано = json.loads((jiv.REPO / "backtest_stats.json").read_text(
        encoding="utf-8"))["fresh"]

    for етикет, индекс in (("САМО ВХОДНИ дни (както е смятан живият файл)", само_входни),
                           ("ПЪЛЕН дневен календар (както смята живият бот)", пълен)):
        st_l, st_s = стрийкове(индекс)
        клетки = np.array([кл(int((st_l if dr == "long" else st_s).get(d, 0)))
                           for d, dr in zip(ден, E["direction"])])
        print("\n  " + етикет)
        print("    %-6s %-6s %6s %5s %9s %9s %9s   %s"
              % ("посока", "кофа", "n", "дни", "$/сделка", "lo", "hi", "ЗАПИСАНО в bs.json"))
        for пос in ("long", "short"):
            for c in ("day1", "fresh", "mixed", "stale"):
                a = кофа_числа(net, ден.values,
                               (E["direction"] == пос) & (клетки == c))
                з = записано[пос].get(c) or {}
                if a is None:
                    continue
                съвп = ("СЪВПАДА" if (a["n"] == з.get("n")
                                      and abs(a["net"] - (з.get("net") or 0)) < 0.002)
                        else "различно")
                print("    %-6s %-6s %6d %5d %+9.3f %+9.3f %+9.3f   n=%-5s net=%+7.3f  → %s"
                      % (пос, c, a["n"], a["дни"], a["net"], a["lo"], a["hi"],
                         з.get("n"), з.get("net") or 0, съвп))


if __name__ == "__main__":
    main()
