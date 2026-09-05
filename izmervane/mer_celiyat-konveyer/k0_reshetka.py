# -*- coding: utf-8 -*-
"""k0_reshetka.py — ЦЯЛАТА решетка от 15-минутни чекпойнти, БЕЗ нито едно звено.

Всичко останало в тази папка стои върху този файл. Тук НЕ се филтрира нищо:
записва се какво е ВИЖДАЛ ботът на всеки чекпойнт (посока, степен, точки,
стрийк, клетка, dd20, режим, превес) и КЪДЕ би влязъл (бар в 1-мин лента).

Огледало на gh.build_entries (тя изхвърля всичко освен избраните) +
допълнителните колони от pribor.решетка.

СВЕРКА С1 (условие преди което и да е число оттук):
    прилагам анти-спама на gh (COOL_MIN=45 / COOL_FLIP=15) върху МОЯТА
    решетка → трябва да дам ТОЧНО gh.OUT_ENTRIES (6846 реда, същите
    bar_index / direction / tier / score / entry_px).
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
sys.path.insert(0, str(IZM))
sys.path.insert(0, str(REPO))
import geom_harness as gh                                            # noqa: E402
import live_bot as lb                                                # noqa: E402

OUT = TUK / "reshetka.parquet"
T0 = time.time()


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


def строй():
    cols = ["timestamp_utc", "open_bid", "high_bid", "low_bid", "close_bid",
            "open_ask", "high_ask", "low_ask", "close_ask"]
    d = pq.read_table(gh.P15MIN, columns=cols).to_pandas()
    d = d.sort_values("timestamp_utc").reset_index(drop=True)
    d["o"] = (d.open_bid + d.open_ask) / 2
    d["h"] = (d.high_bid + d.high_ask) / 2
    d["l"] = (d.low_bid + d.low_ask) / 2
    d["c"] = (d.close_bid + d.close_ask) / 2
    ny = d.timestamp_utc.dt.tz_convert("America/New_York")
    d["day"] = (ny + pd.Timedelta(hours=7)).dt.normalize().dt.tz_localize(None)
    лог("15-мин барове %s  %s .. %s" % (format(len(d), ","),
                                        d.timestamp_utc.iloc[0], d.timestamp_utc.iloc[-1]))

    daily = d.groupby("day").agg(Open=("o", "first"), High=("h", "max"),
                                 Low=("l", "min"), Close=("c", "last"))
    idx = daily.index
    лог("дневни барове %d  %s .. %s" % (len(daily), idx[0].date(), idx[-1].date()))

    gdx = pd.read_csv(gh.F_GDX, parse_dates=["Date"]).set_index("Date")["Close"]
    dxy = pd.read_csv(gh.F_DXY, parse_dates=["Date"]).set_index("Date")["Close"]
    rr = pd.read_csv(gh.F_RR)
    rr["observation_date"] = pd.to_datetime(rr["observation_date"])
    rr["DFII10"] = pd.to_numeric(rr["DFII10"], errors="coerce")
    rr = rr.dropna().set_index("observation_date")["DFII10"]

    g = daily["Close"]
    gd = gdx.reindex(idx).ffill()
    dx = dxy.reindex(idx).ffill()
    r = rr.reindex(idx).ffill()

    raw_min = (gd.pct_change(50) - g.pct_change(50)).shift(1)
    raw_dol = (-(dx.pct_change(20))).shift(1)
    raw_rat = (-(r - r.shift(20))).shift(1)
    m_min = (raw_min > 0).fillna(False)
    m_dol = (raw_dol > 0).fillna(False)
    m_rat = (raw_rat > 0).fillna(False)
    mac_ok = raw_min.notna() & raw_dol.notna() & raw_rat.notna()

    R = pd.DataFrame(index=idx)
    R["sma50"] = g.rolling(50).mean().shift(1)
    R["sma20"] = g.rolling(20).mean().shift(1)
    R["ago5"] = g.shift(6)
    R["ago20"] = g.shift(21)
    R["low20"] = daily["Low"].rolling(20).min().shift(1)
    R["high20"] = daily["High"].rolling(20).max().shift(1)
    R["n_hist"] = np.arange(len(idx))
    R["mac_ok"] = mac_ok.values
    R["m_min"] = m_min.values
    R["m_dol"] = m_dol.values
    R["m_rat"] = m_rat.values
    R["sma200"] = g.rolling(200).mean().shift(1)
    vol20 = g.pct_change().rolling(20).std()
    R["vol20"] = vol20.shift(1)
    R["volmed"] = vol20.rolling(252).median().shift(1)

    m_l = ((-(dx.pct_change(20))) > 0) & ((-(r - r.shift(20))) > 0)
    m_s = ((dx.pct_change(20)) > 0) & ((r - r.shift(20)) > 0)

    def стрийк(m):
        s = m.shift(1).fillna(False).astype(bool)
        return s.groupby((~s).cumsum()).cumsum().astype(int)

    R["streak_long"] = стрийк(m_l).values
    R["streak_short"] = стрийк(m_s).values
    R["dd20"] = (((g.rolling(20).max() - g) / g).shift(1)).values

    d["run_h"] = d.groupby("day")["h"].cummax()
    d["run_l"] = d.groupby("day")["l"].cummin()
    X = d.join(R, on="day")

    cN, hN, lN = X.c.values, X.run_h.values, X.run_l.values
    s50, s20, a5, a20, l20, h20 = (X.sma50.values, X.sma20.values, X.ago5.values,
                                   X.ago20.values, X.low20.values, X.high20.values)
    nn = lambda a: ~np.isnan(a)                                       # noqa: E731
    with np.errstate(invalid="ignore", divide="ignore"):
        lp = ((nn(s50) & (cN > s50)).astype(np.int8)
              + (nn(s20) & (cN > s20)).astype(np.int8)
              + (nn(a20) & (cN > a20)).astype(np.int8)
              + (nn(a5) & nn(a20) & (cN / a5 - 1 < 0) & (cN / a20 - 1 > 0)).astype(np.int8)
              + (nn(l20) & (lN <= l20 * 1.015)).astype(np.int8))
        sp = ((nn(s50) & (cN < s50)).astype(np.int8)
              + (nn(s20) & (cN < s20)).astype(np.int8)
              + (nn(a20) & (cN < a20)).astype(np.int8)
              + (nn(a5) & nn(a20) & (cN / a5 - 1 > 0) & (cN / a20 - 1 < 0)).astype(np.int8)
              + (nn(h20) & (hN >= h20 * 0.985)).astype(np.int8))
    ml = (X.m_min.values.astype(np.int8) + X.m_dol.values.astype(np.int8)
          + X.m_rat.values.astype(np.int8))
    ls = (ml + lp).astype(np.int16)
    ss = ((3 - ml) + sp).astype(np.int16)

    def tier(score, m3):
        return np.where(m3, 3, np.where(score >= 6, 2, np.where(score >= 4, 1, 0)))

    tl, tsh = tier(ls, ml == 3), tier(ss, ml == 0)
    direction = np.where(ls > ss, 1, np.where(ss > ls, -1, 0)).astype(np.int8)
    score = np.where(ls > ss, ls, np.where(ss > ls, ss, np.maximum(ls, ss))).astype(np.int16)
    tk = np.where(ls > ss, tl, np.where(ss > ls, tsh, 0)).astype(np.int8)
    ok_hist = ((X.n_hist.values >= gh.MIN_HISTORY) & X.mac_ok.values)

    # ---- къде би влязъл: първият 1-мин бар на/след чекпойнт+15м -------------
    B = gh.load_tape()
    tsmin15 = X.timestamp_utc.values.astype("datetime64[m]").astype(np.int64)
    want = tsmin15 + 15
    j = np.searchsorted(B["tsmin"], want, side="left")
    fill_ok = j < len(B["tsmin"])
    jc = np.clip(j, 0, len(B["tsmin"]) - 1)
    gapmin = np.where(fill_ok, B["tsmin"][jc] - want, 10 ** 9)
    fill_ok &= gapmin <= 120

    px_long = np.where(fill_ok, B["oa"][jc], np.nan)
    px_short = np.where(fill_ok, B["ob"][jc], np.nan)
    ny_entry = pd.DatetimeIndex(B["ts"][jc]).tz_localize("UTC").tz_convert("America/New_York")
    et_min = (ny_entry.hour * 60 + ny_entry.minute).values
    us_shield = ((et_min >= lb.SHIELD_ET[0]) & (et_min <= lb.SHIELD_ET[1])) & fill_ok
    sof_h = (pd.DatetimeIndex(X.timestamp_utc.values).tz_localize("UTC")
             .tz_convert("Europe/Sofia").hour).values

    G = pd.DataFrame({
        "ts": X.timestamp_utc.values,
        "ден": X["day"].values,
        "dord_entry": np.where(fill_ok, B["dord"][jc], -1).astype(np.int32),
        "bar_index": np.where(fill_ok, jc, -1).astype(np.int64),
        "fill_ok": fill_ok,
        "ok_hist": ok_hist,
        "dir": direction,
        "tier": tk,
        "score": score,
        "ls": ls, "ss": ss,
        "px_long": px_long, "px_short": px_short,
        "us_shield": us_shield,
        "sofia_h": sof_h.astype(np.int8),
        "streak_long": X["streak_long"].values.astype(np.int16),
        "streak_short": X["streak_short"].values.astype(np.int16),
        "dd20": X["dd20"].values,
        "cN": cN, "sma200": X["sma200"].values,
        "vol20": X["vol20"].values, "volmed": X["volmed"].values,
    })
    лог("чекпойнти %s · ok_hist %s · с посока %s · actionable %s"
        % (format(len(G), ","), format(int(ok_hist.sum()), ","),
           format(int((ok_hist & (direction != 0)).sum()), ","),
           format(int((ok_hist & (direction != 0) & (tk > 0)).sum()), ",")))
    return G, B


# --------------------------------------------------------------- С1
def сверка_с1(G, B):
    """Анти-спамът на gh (45/15, състояние се мени при ИЗБОР) → gh.OUT_ENTRIES."""
    act = (G.ok_hist.values & (G["dir"].values != 0) & (G.tier.values > 0))
    tsmin = G.ts.values.astype("datetime64[m]").astype(np.int64)
    dname = np.array(["short", "wait", "long"])[G["dir"].values + 1]
    tname = np.array(["weak", "medium", "strong", "premium"])[G.tier.values]
    keys = np.where(act, np.char.add(np.char.add(dname, ":"), tname), "")
    last_key = ""; last_dir = ""; last_tier = 0; last_ts = None
    picked = []
    for i in range(len(G)):
        if not act[i]:
            last_key = ""
            continue
        dr = dname[i]; tr = int(G.tier.values[i])
        mins = None if last_ts is None else (tsmin[i] - last_ts)
        tier_up = (tr > last_tier) and (dr == last_dir)
        cool_ok = (mins is None or mins >= 45 or (dr != last_dir and mins >= 15) or tier_up)
        if (keys[i] != last_key or tier_up) and cool_ok:
            picked.append(i)
            last_key, last_dir, last_tier, last_ts = keys[i], dr, tr, tsmin[i]
    picked = np.array(picked)
    picked = picked[G.fill_ok.values[picked]]
    лог("С1 · моите карти след анти-спам 45/15 и изпълнимост: %d" % len(picked))

    E = pd.read_parquet(gh.OUT_ENTRIES)
    лог("С1 · gh.OUT_ENTRIES n=%d" % len(E))
    assert len(E) == len(picked), "различен брой входове"
    my_dir = dname[picked]
    my_tier = tname[picked]
    my_px = np.where(my_dir == "long", G.px_long.values[picked], G.px_short.values[picked])
    for име, мое, тяхно in (("bar_index", G.bar_index.values[picked], E.bar_index.values),
                            ("direction", my_dir, E.direction.values),
                            ("tier", my_tier, E.tier.values),
                            ("score", G.score.values[picked], E.score.values)):
        нес = int((мое != тяхно).sum())
        лог("   С1 %-10s разминавания: %d" % (име, нес))
        assert нес == 0, име
    нес = int((np.abs(my_px - E.entry_px.values) > 1e-12).sum())
    лог("   С1 %-10s разминавания: %d" % ("entry_px", нес))
    assert нес == 0
    нес = int((G.us_shield.values[picked] & (my_dir == "short")
               != E.us_shield_short_block.values).sum())
    лог("   С1 %-10s разминавания: %d" % ("us_shield", нес))
    assert нес == 0
    лог("С1 ✅ решетката възпроизвежда доставените 6846 входа точно")


def main():
    G, B = строй()
    сверка_с1(G, B)
    G.to_parquet(OUT, index=False)
    лог("записано %s  редове=%s" % (OUT, format(len(G), ",")))


if __name__ == "__main__":
    main()
