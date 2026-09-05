# -*- coding: utf-8 -*-
"""r4b_stryk.py - КОЙ стрийк дава кофите, записани в backtest_stats.json.fresh?

Кофите в доставения блок НЕ се възпроизвеждат от стрийка в reshetka.parquet
(shift(1)). Тук се пробват вариантите ЕДИН ПО ЕДИН върху СЪЩИТЕ 6846 входа и
се сравнява САМО броят по кофа (n) - число, което не зависи от геометрия,
хоризонт или бутстрап. Съвпадне ли n за осемте кофи, вариантът е намерен.
"""
from __future__ import annotations
import io
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
KONV = IZM / "mer_celiyat-konveyer"
for p in (str(KONV), str(IZM / "mer_mnozhitelite"), str(IZM), str(REPO)):
    sys.path.insert(0, p)
import pq_lite as pl                                                 # noqa: E402
import dvig                                                          # noqa: E402
import live_bot as lb                                                # noqa: E402
import r2_vhodove as r2                                              # noqa: E402

T0 = time.time()
F_DXY = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\dxy_yahoo_full.csv")
F_RR = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\DFII10.csv")
F_GDX = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\gdx_us_d.csv")
КОФИ = ("day1", "fresh", "mixed", "stale")


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


def дълж(s):
    s = s.fillna(False).astype(bool)
    return s.groupby((~s).cumsum()).cumsum().astype(int)


def main():
    Z = dict(np.load(TUK / "r1_ramki.npz"))
    G = pl.read_columns(KONV / "reshetka.parquet")
    G.pop("__meta__", None)
    B = dvig.лента()
    tsmin = G["ts"] // 60_000_000
    ml = Z["ml"].astype(np.int16)
    d0, sc0, t0 = r2.resolve_tier(Z["1ден_ls"].astype(np.int16),
                                  Z["1ден_ss"].astype(np.int16), ml, живо=False)
    act = np.asarray(G["ok_hist"]) & (d0 != 0) & (t0 > 0)
    key = ((d0 + 1) * 4 + t0).astype(np.int32)
    picked = r2.antispam(act, key, np.where(d0 == 1, "long", "short"), t0, tsmin)
    picked = picked[np.asarray(G["fill_ok"])[picked]]
    assert len(picked) == 6846
    dirs = d0[picked]
    dcp = Z["ден_чекпойнт"][picked]

    st, en = dvig.дни_индекс(B)
    дати = (pd.DatetimeIndex(pd.to_datetime(B["tsmin"][st] * 60, unit="s", utc=True))
            .tz_convert("America/New_York") + pd.Timedelta(hours=7))
    idx = pd.DatetimeIndex(дати.normalize().tz_localize(None))
    dxy = pd.read_csv(F_DXY, parse_dates=["Date"]).set_index("Date")["Close"]
    rr = pd.read_csv(F_RR)
    rr["observation_date"] = pd.to_datetime(rr["observation_date"])
    rr["DFII10"] = pd.to_numeric(rr["DFII10"], errors="coerce")
    rr = rr.dropna().set_index("observation_date")["DFII10"]
    gdx = pd.read_csv(F_GDX, parse_dates=["Date"]).set_index("Date")["Close"]
    dx = dxy.reindex(idx).ffill()
    r = rr.reindex(idx).ffill()
    gd = gdx.reindex(idx).ffill()
    # дневното злато, за да може вариант с миньорите
    g15 = B["tsmin"] // 15
    _, s15 = np.unique(g15, return_index=True)
    s15 = np.sort(s15)
    e15 = np.append(s15[1:], len(B["tsmin"])) - 1
    c15 = ((B["cb"] + B["ca"]) / 2.0)[e15]
    d15 = B["dord"][e15]
    nd = int(B["dord"][-1]) + 1
    ds = np.searchsorted(d15, np.arange(nd), "left")
    de = np.searchsorted(d15, np.arange(nd), "right")
    dc = np.full(nd, np.nan)
    има = de > ds
    dc[има] = c15[de[има] - 1]
    g = pd.Series(dc, index=idx)

    m_l = ((-(dx.pct_change(20))) > 0) & ((-(r - r.shift(20))) > 0)
    m_s = ((dx.pct_change(20)) > 0) & ((r - r.shift(20)) > 0)
    mi_l = (gd.pct_change(50) - g.pct_change(50)) > 0
    m3_l = m_l & mi_l
    m3_s = m_s & (~mi_l)

    ВАРИАНТИ = {
        "V1 shift(1) долар+лихви": (дълж(m_l.shift(1)), дълж(m_s.shift(1))),
        "V2 без shift долар+лихви": (дълж(m_l), дълж(m_s)),
        "V3 shift(2)": (дълж(m_l.shift(2)), дълж(m_s.shift(2))),
        "V4 shift(1) + миньори": (дълж(m3_l.shift(1)), дълж(m3_s.shift(1))),
        "V5 без shift + миньори": (дълж(m3_l), дълж(m3_s)),
    }
    # V6-V8 · други мрежи от дни
    кал = pd.date_range(idx[0], idx[-1], freq="D")
    dxk = dxy.reindex(кал).ffill()
    rrk = rr.reindex(кал).ffill()
    mk_l = ((-(dxk.pct_change(20))) > 0) & ((-(rrk - rrk.shift(20))) > 0)
    mk_s = ((dxk.pct_change(20)) > 0) & ((rrk - rrk.shift(20)) > 0)
    kl = дълж(mk_l.shift(1)).reindex(idx).fillna(0).astype(int)
    ks = дълж(mk_s.shift(1)).reindex(idx).fillna(0).astype(int)
    ВАРИАНТИ["V6 календарни дни shift(1)"] = (kl, ks)
    kl2 = дълж(mk_l).reindex(idx).fillna(0).astype(int)
    ks2 = дълж(mk_s).reindex(idx).fillna(0).astype(int)
    ВАРИАНТИ["V7 календарни дни без shift"] = (kl2, ks2)
    съюз = dxy.index.union(rr.index)
    dxu = dxy.reindex(съюз).ffill()
    rru = rr.reindex(съюз).ffill()
    mu_l = ((-(dxu.pct_change(20))) > 0) & ((-(rru - rru.shift(20))) > 0)
    mu_s = ((dxu.pct_change(20)) > 0) & ((rru - rru.shift(20)) > 0)
    ВАРИАНТИ["V8 собствената мрежа на DXY"] = (
        дълж(mu_l.shift(1)).reindex(idx).ffill().fillna(0).astype(int),
        дълж(mu_s.shift(1)).reindex(idx).ffill().fillna(0).astype(int))
    st_json = json.load(io.open(REPO / "backtest_stats.json", encoding="utf-8"))["fresh"]
    цел = {(dn, c): st_json[dn][c]["n"] for dn in ("long", "short") for c in КОФИ}
    лог("ЦЕЛ (backtest_stats.json.fresh): " + " · ".join(
        "%s/%s=%d" % (dn, c, цел[(dn, c)]) for dn in ("long", "short") for c in КОФИ))
    for име, (sl, ss) in ВАРИАНТИ.items():
        SL = sl.to_numpy()[dcp]
        SS = ss.to_numpy()[dcp]
        s = np.where(dirs == 1, SL, SS)
        cell = np.array([lb._cell_name(int(x)) for x in s], dtype=object)
        мое = {(dn, c): int(((dirs == (1 if dn == "long" else -1)) & (cell == c)).sum())
               for dn in ("long", "short") for c in КОФИ}
        разлика = sum(abs(мое[k] - цел[k]) for k in цел)
        print("   %-26s Σ|Δn| = %5d   %s" % (име, разлика,
              " ".join("%s/%s %d" % (dn, c, мое[(dn, c)])
                       for dn in ("long", "short") for c in КОФИ)), flush=True)


if __name__ == "__main__":
    main()
