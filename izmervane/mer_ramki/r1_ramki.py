# -*- coding: utf-8 -*-
"""r1_ramki.py - СЕДЕМТЕ РАМКИ на всеки от 530 659 чекпойнта.

Строи за всяка рамка (1мин/5м/15м/30м/1час/4час/1ден):
    cN,hN,lN на ТЕКУЩИЯ (частичен) бар на рамката, както `_scores` ги чете,
    и СВОИТЕ линии `_refs(df)` - sma50/sma20/ago5/ago20/low20/high20,
    смятани от баровете НА РАМКАТА, с текущия бар ВКЛЮЧЕН (както в живия бот:
    `_refs` се вика върху същия df, чийто последен бар е частичният).

СВЕРКА С0 (условие, преди което и да е число оттук):
    рамката «1ден», смятана ТУК от лентата, трябва да върне същите ls/ss като
    reshetka.parquet (която е сверена с доставените 6846 входа).
"""
from __future__ import annotations
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

OUT = TUK / "r1_ramki.npz"
T0 = time.time()
F_GDX = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\gdx_us_d.csv")
F_DXY = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\dxy_yahoo_full.csv")
F_RR = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\DFII10.csv")
РАМКИ = (("1мин", 1), ("5м", 5), ("15м", 15), ("30м", 30), ("1час", 60), ("4час", 240))


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


def сегментни(vals, gid, op):
    _, st = np.unique(gid, return_index=True)
    st = np.sort(st)
    if op == "max":
        return np.maximum.reduceat(vals, st), st
    return np.minimum.reduceat(vals, st), st


def refs_ot(fc, fh, fl, k, c_run, h_run, l_run):
    """_refs(df) при последен (частичен) бар на позиция k, история fc/fh/fl[<k]."""
    n = len(fc)
    CS = np.concatenate(([0.0], np.cumsum(fc)))
    RL = pd.Series(fl).rolling(19).min().shift(1).to_numpy()
    RH = pd.Series(fh).rolling(19).max().shift(1).to_numpy()
    nan = np.nan
    ok50 = k >= 49
    ok20 = k >= 20
    ok19 = k >= 19
    ok5 = k >= 5
    k49 = np.where(ok50, k - 49, 0)
    k19 = np.where(ok19, k - 19, 0)
    kc = np.clip(k, 0, n - 1)
    sma50 = np.where(ok50, (CS[k] - CS[k49] + c_run) / 50.0, nan)
    sma20 = np.where(ok19, (CS[k] - CS[k19] + c_run) / 20.0, nan)
    ago5 = np.where(ok5, fc[np.where(ok5, k - 5, 0)], nan)
    ago20 = np.where(ok20, fc[np.where(ok20, k - 20, 0)], nan)
    low20 = np.where(ok19, np.minimum(RL[kc], l_run), nan)
    high20 = np.where(ok19, np.maximum(RH[kc], h_run), nan)
    return dict(sma50=sma50, sma20=sma20, ago5=ago5, ago20=ago20,
                low20=low20, high20=high20)


def tochki(cN, hN, lN, R):
    """ДОСЛОВНО lp/sp от live_bot._scores при price_adj=0."""
    def nn(a):
        return ~np.isnan(a)
    s50, s20, a5, a20, l20, h20 = (R["sma50"], R["sma20"], R["ago5"],
                                   R["ago20"], R["low20"], R["high20"])
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
    return lp, sp


def main():
    G = pl.read_columns(KONV / "reshetka.parquet")
    G.pop("__meta__", None)
    cp = G["ts"] // 60_000_000
    B = dvig.лента()
    ts = B["tsmin"]
    N = len(ts)
    лог("лента %s · чекпойнти %s" % (format(N, ","), format(len(cp), ",")))

    j = np.searchsorted(ts, cp + 15, "left") - 1
    assert (j >= 0).all()
    assert (ts[j] >= cp).all(), "чекпойнт без свой минутен бар"
    assert (ts[j] <= cp + 14).all()
    лог("j намерен - всеки чекпойнт има свой минутен бар")

    mid_c = (B["cb"] + B["ca"]) / 2.0
    OUT_D = {}

    g15 = ts // 15
    hb15, st15 = сегментни(B["hb"], g15, "max")
    ha15, _ = сегментни(B["ha"], g15, "max")
    lb15, _ = сегментни(B["lb"], g15, "min")
    la15, _ = сегментни(B["la"], g15, "min")
    en15 = np.append(st15[1:], N) - 1
    h15 = (hb15 + ha15) / 2.0
    l15 = (lb15 + la15) / 2.0
    c15 = mid_c[en15]
    d15 = B["dord"][en15]
    лог("15-мин барове %s (решетката има %s)" % (format(len(c15), ","), format(len(cp), ",")))

    nd = int(B["dord"][-1]) + 1
    dstart = np.searchsorted(d15, np.arange(nd), "left")
    dend = np.searchsorted(d15, np.arange(nd), "right")
    dc = np.full(nd, np.nan)
    dh = np.full(nd, np.nan)
    dl = np.full(nd, np.nan)
    има = dend > dstart
    dc[има] = c15[dend[има] - 1]
    dh[има] = np.maximum.reduceat(h15, dstart[има])
    dl[има] = np.minimum.reduceat(l15, dstart[има])
    run_h15 = pd.Series(h15).groupby(d15).cummax().to_numpy()
    run_l15 = pd.Series(l15).groupby(d15).cummin().to_numpy()

    i15 = np.searchsorted(g15[en15], cp // 15, "left")
    assert (g15[en15][i15] == cp // 15).all(), "чекпойнт без 15-мин бар"

    S = pd.Series(dc)
    Rd = dict(sma50=S.rolling(50).mean().shift(1).to_numpy(),
              sma20=S.rolling(20).mean().shift(1).to_numpy(),
              ago5=S.shift(6).to_numpy(),
              ago20=S.shift(21).to_numpy(),
              low20=pd.Series(dl).rolling(20).min().shift(1).to_numpy(),
              high20=pd.Series(dh).rolling(20).max().shift(1).to_numpy())
    dcp = d15[i15]
    Rdcp = {k2: v[dcp] for k2, v in Rd.items()}
    cNd = c15[i15]
    hNd = run_h15[i15]
    lNd = run_l15[i15]
    lp_d, sp_d = tochki(cNd, hNd, lNd, Rdcp)

    st, en = dvig.дни_индекс(B)
    дати = (pd.DatetimeIndex(pd.to_datetime(ts[st] * 60, unit="s", utc=True))
            .tz_convert("America/New_York") + pd.Timedelta(hours=7))
    idx = pd.DatetimeIndex(дати.normalize().tz_localize(None))
    gdx = pd.read_csv(F_GDX, parse_dates=["Date"]).set_index("Date")["Close"]
    dxy = pd.read_csv(F_DXY, parse_dates=["Date"]).set_index("Date")["Close"]
    rr = pd.read_csv(F_RR)
    rr["observation_date"] = pd.to_datetime(rr["observation_date"])
    rr["DFII10"] = pd.to_numeric(rr["DFII10"], errors="coerce")
    rr = rr.dropna().set_index("observation_date")["DFII10"]
    g = pd.Series(dc, index=idx)
    gd = gdx.reindex(idx).ffill()
    dx = dxy.reindex(idx).ffill()
    r = rr.reindex(idx).ffill()
    raw_min = (gd.pct_change(50) - g.pct_change(50)).shift(1)
    raw_dol = (-(dx.pct_change(20))).shift(1)
    raw_rat = (-(r - r.shift(20))).shift(1)
    ml_d = ((raw_min > 0).fillna(False).to_numpy().astype(np.int8)
            + (raw_dol > 0).fillna(False).to_numpy().astype(np.int8)
            + (raw_rat > 0).fillna(False).to_numpy().astype(np.int8))
    ml = ml_d[dcp]
    ls_моя = (ml + lp_d).astype(np.int16)
    ss_моя = ((3 - ml) + sp_d).astype(np.int16)
    нес_ls = int((ls_моя != G["ls"]).sum())
    нес_ss = int((ss_моя != G["ss"]).sum())
    лог("С0 - «1ден» ls разминавания %d / %s - ss %d"
        % (нес_ls, format(len(cp), ","), нес_ss))
    if нес_ls or нес_ss:
        m = (ls_моя != G["ls"]) | (ss_моя != G["ss"])
        лог("   първите 5 индекса:", np.flatnonzero(m)[:5].tolist())

    OUT_D["ml"] = ml.astype(np.int8)
    OUT_D["ден_чекпойнт"] = dcp.astype(np.int32)
    for k2, v in Rdcp.items():
        OUT_D["дневна_" + k2] = v
    OUT_D["1ден_ls"] = np.asarray(G["ls"]).astype(np.int16)
    OUT_D["1ден_ss"] = np.asarray(G["ss"]).astype(np.int16)
    OUT_D["1ден_cN"] = cNd
    OUT_D["1ден_hN"] = hNd
    OUT_D["1ден_lN"] = lNd

    for име, m in РАМКИ:
        t1 = time.time()
        if m == 1:
            fc = mid_c
            fh = (B["hb"] + B["ha"]) / 2.0
            fl = (B["lb"] + B["la"]) / 2.0
            k = j.copy()
            c_run = fc[j]
            h_run = fh[j]
            l_run = fl[j]
        elif m < 15:
            gid = ts // m
            hbm, stm = сегментни(B["hb"], gid, "max")
            ham, _ = сегментни(B["ha"], gid, "max")
            lbm, _ = сегментни(B["lb"], gid, "min")
            lam, _ = сегментни(B["la"], gid, "min")
            enm = np.append(stm[1:], N) - 1
            fc = mid_c[enm]
            fh = (hbm + ham) / 2.0
            fl = (lbm + lam) / 2.0
            k = np.searchsorted(gid[enm], ts[j] // m, "left")
            assert (gid[enm][k] == ts[j] // m).all()
            c_run = fc[k]
            h_run = fh[k]
            l_run = fl[k]
        else:
            gid15 = ts[en15] // m
            _, stm = np.unique(gid15, return_index=True)
            stm = np.sort(stm)
            enm = np.append(stm[1:], len(gid15)) - 1
            fc = c15[enm]
            fh = np.maximum.reduceat(h15, stm)
            fl = np.minimum.reduceat(l15, stm)
            k = np.searchsorted(gid15[enm], gid15[i15], "left")
            assert (gid15[enm][k] == gid15[i15]).all()
            c_run = c15[i15]
            if m == 15:
                h_run = h15[i15]
                l_run = l15[i15]
            else:
                h_run = pd.Series(h15).groupby(gid15).cummax().to_numpy()[i15]
                l_run = pd.Series(l15).groupby(gid15).cummin().to_numpy()[i15]
        R = refs_ot(fc, fh, fl, k, c_run, h_run, l_run)
        добри = np.ones(len(cp), bool)
        for v in R.values():
            добри &= np.isfinite(v)
        добри &= (k >= 60)
        OUT_D[име + "_cN"] = c_run
        OUT_D[име + "_hN"] = h_run
        OUT_D[име + "_lN"] = l_run
        for k2, v in R.items():
            OUT_D[име + "_" + k2] = v
        OUT_D[име + "_свои_ок"] = добри
        лог("   %-5s барове %s - свои линии валидни %.2f%% (%.0fs)"
            % (име, format(len(fc), ","), 100.0 * добри.mean(), time.time() - t1))
        del fc, fh, fl, R
    np.savez_compressed(OUT, **OUT_D)
    лог("записано %s" % OUT)


if __name__ == "__main__":
    main()
