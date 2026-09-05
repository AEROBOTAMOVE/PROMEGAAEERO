# -*- coding: utf-8 -*-
"""tegla.py — четирите множителя като вектори, и гейтът като маска.

ВСИЧКО СЕ ВЗИМА ОТ ЖИВИЯ БОТ (импортиран, не преписан):
  _zw  ← live_bot.ZONE_W[зона]              (днес ПЛОСКО 1/1/1)
  _мw  ← live_bot.МАЛЪК_РАЗМЕР_W = 0.5, когато клетката е mixed/stale,
         тоест когато `_advice_entry` връща «ДА (малък размер)»
  _рw  ← live_bot._режим_тегло(посока, {'below_sma200': cN < sma200})
  _пw  ← live_bot._превес_тегло(ls - ss)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
sys.path.insert(0, str(REPO))
import live_bot as lb                                                # noqa: E402

MIN_N = 100                    # live_bot.py:1764
NEAR_HIGH_DD20 = 0.015         # live_bot.py:1838

ZONE_ВАРИАНТИ = {
    "плоска (жива днес)": {"A": 1.00, "B": 1.00, "C": 1.00},
    "мерена (до 01.09)": {"A": 1.00, "B": 0.85, "C": 0.50},
    "стара (до 26.08)": {"A": 1.00, "B": 0.67, "C": 0.33},
}


def данни():
    return pd.read_parquet(TUK / "mnozh_6846.parquet")


# ------------------------------------------------------------------ множители
def множители(E, zone_w=None):
    """Връща DataFrame с четирите множителя + произведението."""
    zw_map = lb.ZONE_W if zone_w is None else zone_w
    zw = np.array([zw_map.get(z, 1.0) for z in E["зона"].values])
    мw = np.where(np.isin(E["клетка"].values, ("mixed", "stale")), lb.МАЛЪК_РАЗМЕР_W, 1.0)
    под = E["cN"].values < E["sma200"].values
    рw = np.array([lb._режим_тегло(d, {"below_sma200": bool(b), "low_vol": None})[0]
                   for d, b in zip(E["direction"].values, под)])
    пw = np.array([lb._превес_тегло(int(a) - int(b))[0]
                   for a, b in zip(E["ls"].values, E["ss"].values)])
    W = pd.DataFrame({"zw": zw, "мw": мw, "рw": рw, "пw": пw})
    W["W"] = W.zw * W.мw * W.рw * W.пw
    return W


# ------------------------------------------------------------------ гейтът
def _noise(seg):
    lo, hi = seg.get("lo"), seg.get("hi")
    return lo is not None and hi is not None and lo <= 0 <= hi


def гейт_маска(E, stats_path=None):
    """ДОСЛОВНО пластът «клетка» на live_bot._advice_entry (само злато).
    Другите пластове (стоп-пазач, US-щит, стара цена) НЕ се моделират —
    те не зависят от тези числа и режат допълнително."""
    p = stats_path or (REPO / "backtest_stats.json")
    S = json.load(open(p, encoding="utf-8"))["fresh"]
    ok = np.zeros(len(E), dtype=bool)
    защо = []
    for i in range(len(E)):
        d = E["direction"].values[i]
        sn = int(E["streak"].values[i])
        fr = S.get(d, {})
        dd20 = E["dd20"].values[i]
        if 1 <= sn <= 3:
            seg_near = fr.get("near_high") or {}
            if (d == "short" and 2 <= sn <= 3 and np.isfinite(dd20)
                    and dd20 < NEAR_HIGH_DD20 and seg_near.get("n", 0) >= MIN_N
                    and seg_near.get("net", 0) > 0 and not _noise(seg_near)):
                ok[i] = True; защо.append("near_high"); continue
            seg = fr.get("day1" if sn == 1 else "fresh", {})
            лошо = (seg.get("n", 0) >= MIN_N
                    and (seg.get("net", 0) <= 0 or _noise(seg)))
            ok[i] = not лошо
            защо.append("day1/fresh")
        else:
            seg = (fr.get("mixed") or fr.get("stale", {})) if sn == 0 else fr.get("stale", {})
            лошо = (seg.get("n", 0) >= MIN_N
                    and (seg.get("net", 0) < 0 or _noise(seg)))
            ok[i] = not лошо
            защо.append("mixed" if sn == 0 else "stale")
    return ok, np.array(защо)


# ------------------------------------------------------------------ помощни
def ден_ид(E):
    return pd.factorize(pd.to_datetime(E["ден"].values))[0]


def фмт(m, lo, hi, w=8):
    return "%+*.3f [%+.3f, %+.3f]" % (w, m, lo, hi)
