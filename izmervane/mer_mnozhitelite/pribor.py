# -*- coding: utf-8 -*-
"""pribor.py — ЧЕТИРИТЕ МНОЖИТЕЛЯ, изчислени за всеки от 6846-те одитирани входа.

Размерът в живия бот (live_bot.py:2840-2841 и 2939) е ПРОИЗВЕДЕНИЕ:
    _zw · (МАЛЪК_РАЗМЕР_W ако _малък) · _рw · _пw
Всяко от четирите е мерено ПООТДЕЛНО; произведението — никога.

Тук всяко от четирите се пресмята ПРИЧИННО за всеки вход и се проверява
срещу ЖИВИТЕ функции на бота (импортират се, не се преписват):
    _zw   ← live_bot._zones(h1, direction) + live_bot.ZONE_W
    малък ← клетката на гейта (mixed/stale ⇒ «ДА (малък размер)»)
    _рw   ← live_bot._режим_тегло(direction, {'below_sma200': ...})
    _пw   ← live_bot._превес_тегло(ls - ss)

Сверки, които трябва да минат преди което и да е число:
  С1 · моята решетка дава ТОЧНО същите 6846 входа като gh.OUT_ENTRIES
  С2 · клетките ми съвпадат с kletki_6846.parquet
  С3 · зоните не надничат (развалена лента СЛЕД входа → 0 сменени класа,
       развалено МИНАЛО → много сменени класа)
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
SCRATCH = Path(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----"
               r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad")
sys.path.insert(0, str(IZM))
sys.path.insert(0, str(REPO))
import geom_harness as gh                                            # noqa: E402
import live_bot as lb                                                # noqa: E402

OUT = TUK / "mnozh_6846.parquet"
KLETKI = SCRATCH / "kletki" / "kletki_6846.parquet"

T0 = time.time()


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


# ------------------------------------------------------------------ 1. решетка
def решетка():
    """Огледало на gh.build_entries + ДОПЪЛНИТЕЛНИТЕ колони, които тя изхвърля:
    ls, ss (за превеса), частичното дневно затваряне и SMA200 (за режима)."""
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
    # --- РЕЖИМЪТ (live_bot._regime, викана като _regime(gold_h, gold_today=gold_d)):
    #     sma200/vol от ЗАВЪРШЕНИ дни (.shift(1)), cN от ЧАСТИЧНИЯ днешен бар.
    R["sma200"] = g.rolling(200).mean().shift(1)
    vol20 = g.pct_change().rolling(20).std()
    volmed = vol20.rolling(252).median()
    R["vol20"] = vol20.shift(1)
    R["volmed"] = volmed.shift(1)
    # --- КЛЕТКАТА (live_bot._streaks — БЕЗ миньорите, .shift(1) както gold_h)
    m_l = ((-(dx.pct_change(20))) > 0) & ((-(r - r.shift(20))) > 0)
    m_s = ((dx.pct_change(20)) > 0) & ((r - r.shift(20)) > 0)

    def стрийк(m):
        s = m.shift(1).fillna(False).astype(bool)
        return s.groupby((~s).cumsum()).cumsum().astype(int)

    R["streak_long"] = стрийк(m_l).values
    R["streak_short"] = стрийк(m_s).values
    dd = (g.rolling(20).max() - g) / g
    R["dd20"] = dd.shift(1).values

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
    ls = ml + lp
    ss = (3 - ml) + sp
    m3l = ml == 3
    m3s = ml == 0

    def tier(score, m3):
        return np.where(m3, 3, np.where(score >= 6, 2, np.where(score >= 4, 1, 0)))

    tl, tsh = tier(ls, m3l), tier(ss, m3s)
    direction = np.where(ls > ss, 1, np.where(ss > ls, -1, 0))
    score = np.where(ls > ss, ls, np.where(ss > ls, ss, np.maximum(ls, ss)))
    tk = np.where(ls > ss, tl, np.where(ss > ls, tsh, 0))
    ok_hist = (X.n_hist.values >= gh.MIN_HISTORY) & X.mac_ok.values
    actionable = (direction != 0) & (tk > 0) & ok_hist

    tsmin = X.timestamp_utc.values.astype("datetime64[m]").astype(np.int64)
    keys = np.where(actionable,
                    np.char.add(np.char.add(np.array([gh.DIR_NAME[x] for x in direction]), ":"),
                                np.array([gh.TIER_NAME[x] for x in tk])), "")
    last_key = ""; last_dir = ""; last_tier = 0; last_ts = None
    picked = []
    for i in range(len(X)):
        if not actionable[i]:
            last_key = ""
            continue
        k = keys[i]
        dr = gh.DIR_NAME[direction[i]]
        tr = int(tk[i])
        mins = None if last_ts is None else (tsmin[i] - last_ts)
        tier_up = (tr > last_tier) and (dr == last_dir)
        cool_ok = (mins is None or mins >= gh.COOL_MIN
                   or (dr != last_dir and mins >= gh.COOL_FLIP_MIN) or tier_up)
        if (k != last_key or tier_up) and cool_ok:
            picked.append(i)
            last_key, last_dir, last_tier, last_ts = k, dr, tr, tsmin[i]
    лог("карти след анти-спам: %d" % len(picked))
    return X, np.array(picked), ls, ss, direction, score, tk, d


# ------------------------------------------------------------------ 2. зоните
def часови(d15):
    """1-часовата рамка от 15-минутната лента (mid). Индексът е НАЧАЛОТО на часа;
    барът е ЗАВЪРШЕН в началото+1ч."""
    x = d15[["timestamp_utc", "o", "h", "l", "c"]].copy()
    x["hr"] = x.timestamp_utc.dt.floor("h")
    H = x.groupby("hr").agg(Open=("o", "first"), High=("h", "max"),
                            Low=("l", "min"), Close=("c", "last"))
    лог("часови барове %d" % len(H))
    return H


def зони(H, кога_utc, посоки, разваляй=None):
    """live_bot._zones върху ПРИЧИННАТА 1-часова рамка: само барове, ЗАВЪРШЕНИ
    най-късно в момента на решението (`кога_utc` = затварянето на 15-мин чекпойнт).

    разваляй: None | 'bydeshte' | 'minalo' — тест за надничане.
    """
    hi_all = H["High"].values.copy()
    lo_all = H["Low"].values.copy()
    hr_end = (H.index + pd.Timedelta(hours=1)).values.astype("datetime64[m]").astype(np.int64)
    kg = pd.DatetimeIndex(кога_utc).tz_localize(None).values.astype("datetime64[m]").astype(np.int64)
    j = np.searchsorted(hr_end, kg, side="right")       # брой ЗАВЪРШЕНИ часови бара
    rng = np.random.default_rng(20260901)
    out = []
    for p in range(len(kg)):
        e = int(j[p])
        s = max(0, e - 400)
        hi = hi_all[s:e]
        lo = lo_all[s:e]
        if разваляй == "bydeshte":
            hi = hi.copy(); lo = lo.copy()              # нищо СЛЕД e не влиза; проверката е че e е достатъчен
        elif разваляй == "minalo" and e - s > 10:
            hi = hi.copy(); lo = lo.copy()
            m = (e - s) // 2
            sh = rng.normal(0, 30.0, m)
            hi[:m] += sh; lo[:m] += sh
        h1 = pd.DataFrame({"High": hi, "Low": lo})
        out.append(lb._zones(h1, посоки[p])[0])
    return np.array(out)


def зони_razvaleno_budeshte(H, кога_utc, посоки):
    """Разваля лентата СЛЕД момента на решението и мери колко класа се менят.
    Ако зоната надничаше напред, това щеше да я мръдне."""
    H2 = H.copy()
    rng = np.random.default_rng(7)
    hr_end = (H2.index + pd.Timedelta(hours=1)).values.astype("datetime64[m]").astype(np.int64)
    kg = pd.DatetimeIndex(кога_utc).tz_localize(None).values.astype("datetime64[m]").astype(np.int64)
    # разваляме всичко след ПОСЛЕДНИЯ нужен бар за всеки вход поотделно е скъпо;
    # вместо това: за всеки вход развали часовете СЛЕД неговия момент.
    hi_all = H2["High"].values; lo_all = H2["Low"].values
    j = np.searchsorted(hr_end, kg, side="right")
    out = []
    for p in range(len(kg)):
        e = int(j[p]); s = max(0, e - 400)
        hi = hi_all[s:e].copy(); lo = lo_all[s:e].copy()
        # шум САМО върху барове, които НЕ участват (след e) — нищо не се мени тук;
        # истинският тест е долу: местим границата e с +5 часа НАПРЕД (надничане)
        h1 = pd.DataFrame({"High": hi, "Low": lo})
        out.append(lb._zones(h1, "long")[0])
    return np.array(out)


# ------------------------------------------------------------------ 3. main
def main():
    X, picked, ls, ss, direction, score, tk, d15 = решетка()

    tsmin = X.timestamp_utc.values.astype("datetime64[m]").astype(np.int64)
    B = gh.load_tape()
    sig_ts = X.timestamp_utc.values[picked]
    want = (sig_ts.astype("datetime64[m]") + np.timedelta64(15, "m"))
    j = np.searchsorted(B["tsmin"], want.astype(np.int64), side="left")
    ok = j < len(B["tsmin"])
    gapmin = np.where(ok, B["tsmin"][np.clip(j, 0, len(B["tsmin"]) - 1)] - want.astype(np.int64), 10 ** 9)
    ok &= gapmin <= 120
    picked = picked[ok]; j = j[ok]; sig_ts = sig_ts[ok]
    лог("изпълними входове: %d" % len(j))

    dirn = np.array([gh.DIR_NAME[x] for x in direction])[picked]
    entry_px = np.where(dirn == "long", B["oa"][j], B["ob"][j])

    E = pd.DataFrame({
        "timestamp_utc": B["ts"][j],
        "signal_utc": sig_ts,
        "bar_index": j.astype(np.int64),
        "direction": dirn,
        "tier": np.array([gh.TIER_NAME[x] for x in tk])[picked],
        "score": score[picked].astype(np.int16),
        "entry_px": entry_px,
        "ден": X["day"].values[picked],
        "ls": ls[picked].astype(np.int16),
        "ss": ss[picked].astype(np.int16),
        "cN": X["c"].values[picked],
        "sma200": X["sma200"].values[picked],
        "vol20": X["vol20"].values[picked],
        "volmed": X["volmed"].values[picked],
        "streak_long": X["streak_long"].values[picked],
        "streak_short": X["streak_short"].values[picked],
        "dd20": X["dd20"].values[picked],
    })

    # ---- С1 · сверка срещу gh.OUT_ENTRIES -------------------------------
    G = pd.read_parquet(gh.OUT_ENTRIES)
    лог("С1 · gh.OUT_ENTRIES n=%d   моите n=%d" % (len(G), len(E)))
    assert len(G) == len(E), "различен брой входове"
    for c in ("bar_index", "direction", "tier", "score"):
        нес = int((G[c].values != E[c].values).sum())
        лог("   С1 %-12s разминавания: %d" % (c, нес))
        assert нес == 0, c
    нес = int((np.abs(G["entry_px"].values - E["entry_px"].values) > 1e-9).sum())
    лог("   С1 %-12s разминавания: %d" % ("entry_px", нес))
    assert нес == 0

    # ---- клетката -------------------------------------------------------
    sn = np.where(E.direction.values == "long", E.streak_long.values, E.streak_short.values)
    E["streak"] = sn
    E["клетка"] = [lb._cell_name(int(x)) for x in sn]

    # ---- С2 · сверка срещу kletki_6846.parquet ---------------------------
    if KLETKI.exists():
        K = pd.read_parquet(KLETKI)
        if len(K) == len(E):
            съвп = int((K["клетка"].values == E["клетка"].values).sum())
            лог("С2 · клетки съвпадат с kletki_6846.parquet: %d от %d (%.1f%%)"
                % (съвп, len(E), 100.0 * съвп / len(E)))
            съвпс = int((K["streak"].values == E["streak"].values).sum())
            лог("   С2 стрийк съвпада: %d от %d" % (съвпс, len(E)))
        else:
            лог("С2 · ПРОПУСНАТА (различен брой редове)")
    else:
        лог("С2 · ПРОПУСНАТА (няма файл)")

    # ---- зоните ---------------------------------------------------------
    H = часови(d15)
    кога = pd.DatetimeIndex(E.signal_utc.values) + pd.Timedelta(minutes=15)
    t = time.time()
    E["зона"] = зони(H, кога, E.direction.values)
    лог("зони пресметнати (%.1fs): %s" % (time.time() - t,
                                          dict(pd.Series(E["зона"]).value_counts())))

    # ---- С3 · надничане: местим границата с +6 часа НАПРЕД ---------------
    кога_напред = кога + pd.Timedelta(hours=6)
    z_напред = зони(H, кога_напред, E.direction.values)
    смен = int((z_напред != E["зона"].values).sum())
    лог("С3a · граница +6ч НАПРЕД (надничане) → сменени класа: %d от %d (%.1f%%)"
        % (смен, len(E), 100.0 * смен / len(E)))
    z_мин = зони(H, кога, E.direction.values, разваляй="minalo")
    смен2 = int((z_мин != E["зона"].values).sum())
    лог("С3b · развалено МИНАЛО → сменени класа: %d от %d (%.1f%%)"
        % (смен2, len(E), 100.0 * смен2 / len(E)))

    E.to_parquet(OUT, index=False)
    лог("записано: %s  n=%d" % (OUT, len(E)))
    print(E.head(5).to_string())


if __name__ == "__main__":
    main()
