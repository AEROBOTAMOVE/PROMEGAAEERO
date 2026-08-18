# -*- coding: utf-8 -*-
"""
geom_harness.py — AERO geometry harness (READ-ONLY on the bot; writes only into the scratchpad).

QUESTION IT ANSWERS
    Should the shipped gold ladder
        TP1 +7.5 / TP2 +12 / TP3 +20, STOP -20, one third at each TP, stop->break-even after TP1
    be replaced by a flat
        TP +15.0 / STOP -15.0, single target, R:R 1.0 ?

WHAT IT DOES
    1. Reconstructs the bot's own «1ден» signal (live_bot._macro / _refs / _scores / _resolve /
       _tier) from the daily macro CSVs + daily gold resampled from the 1-min bid/ask parquet,
       and writes the resulting entry set to geom_entries.parquet.
    2. Simulates any geometry forward, bar by bar, on the 1-min bid/ask tape, on the correct
       side of the spread, with no lookahead.
    3. Validates itself (synthetic hand-computable case, shift-by-one-bar, blind control).
    4. Prints the shipped geometry as the baseline.

HONESTY NOTES (read before believing any number)
    * Gold here is SPOT XAUUSD (the tape the bot's spot-ledger actually trades). The live bot
      computes the «1ден» frame on Yahoo GC=F futures. Both the current bar and the references
      come off the SAME curve in the bot ("«1ден» Е на кривата на refs → без корекция",
      live_bot.py:1417), so a constant futures-spot basis cancels out of every test in _scores.
      What does NOT cancel: the two curves are not identical minute for minute.
    * The daily bar is built on the CME/FX convention: 17:00 New York = day close, bar labelled
      by its close date (verified against the data — the tape has a 1h break 17:00-18:00 ET and
      the weekly gap runs Fri 17:00 ET -> Sun 18:00 ET).
    * The bot re-evaluates every few minutes on a PARTIAL daily bar. This harness re-evaluates
      on a 15-minute checkpoint grid, also on the partial daily bar. Coarser than live.
    * Entries fire on a change of the bot's anti-spam fingerprint (live_bot.py:1450) with the
      45/15-minute cooldown (live_bot.py:1458). The v5.8a 4-hour re-offer, the US shield, the
      stop-guard, the CyberQuant macro shield and the silver pipeline are NOT applied; the US
      shield state is recorded per entry as a column so it can be filtered afterwards.
    * Cost model: entry and every exit are taken on the side of the spread a real fill would
      use, so the REAL spread present in the tape at those bars is already paid. On top of that
      a flat slippage of 0.02 $/oz per TRADE is subtracted. Commission/financing are NOT modelled.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# ----------------------------------------------------------------------------- paths
SCRATCH = Path(r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----"
                r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad")
P1MIN = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\parquet\xauusd_1min_bid_ask.parquet")
P15MIN = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\parquet\xauusd_15min_bid_ask.parquet")
F_GDX = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\gdx_us_d.csv")
F_DXY = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\dxy_yahoo_full.csv")
F_RR = Path(r"C:\Users\User\Downloads\ЛОЦО\f6_data\DFII10.csv")
OUT_ENTRIES = SCRATCH / "geom_entries.parquet"
OUT_REPORT = SCRATCH / "geom_report.json"

# ----------------------------------------------------------------------------- constants
SLIP_PER_TRADE = 0.02        # $/oz, stated assumption, charged once per trade
TIME_EXIT_DAYS = 5           # trading days
COOL_MIN = 45                # live_bot.py:1458
COOL_FLIP_MIN = 15           # live_bot.py:1459
MIN_HISTORY = 200            # live_bot.py:1256  (enough_history)
BLIND_SEED = 20260729

TIER_NAME = {0: "weak", 1: "medium", 2: "strong", 3: "premium"}
DIR_NAME = {1: "long", -1: "short", 0: "wait"}

GEOM_SHIPPED = {
    "name": "shipped ladder 7.5/12/20 · SL 20 · thirds · BE after TP1",
    "tps": [(1 / 3, 7.5), (1 / 3, 12.0), (1 / 3, 20.0)],
    "sl": 20.0,
    "be_after_tp1": True,
}
GEOM_FLAT = {
    "name": "flat 150p/150p  TP +15.0 · SL -15.0 · single target",
    "tps": [(1.0, 15.0)],
    "sl": 15.0,
    "be_after_tp1": False,
}


def log(*a):
    print(*a, flush=True)


# ============================================================================= 1. tape
def load_tape():
    """1-minute bid/ask tape as plain numpy arrays + a trading-day ordinal per bar."""
    t0 = time.time()
    cols = ["timestamp_utc", "open_bid", "high_bid", "low_bid", "close_bid",
            "open_ask", "high_ask", "low_ask", "close_ask"]
    d = pq.read_table(P1MIN, columns=cols).to_pandas()
    d = d.sort_values("timestamp_utc").reset_index(drop=True)
    cache = SCRATCH / "gh_dayord_1min.npy"
    if cache.exists():
        dord = np.load(cache)
        assert len(dord) == len(d), "stale day-ordinal cache"
    else:
        ny = d.timestamp_utc.dt.tz_convert("America/New_York")
        day = (ny + pd.Timedelta(hours=7)).dt.normalize().dt.tz_localize(None)
        dord = pd.factorize(day, sort=False)[0].astype(np.int32)   # day is already sorted
        np.save(cache, dord)
    assert (np.diff(dord) >= 0).all(), "day ordinal not monotone"
    B = {
        "ts": d.timestamp_utc.values,
        "tsmin": d.timestamp_utc.values.astype("datetime64[m]").astype(np.int64),
        "ob": d.open_bid.values, "hb": d.high_bid.values, "lb": d.low_bid.values,
        "cb": d.close_bid.values,
        "oa": d.open_ask.values, "ha": d.high_ask.values, "la": d.low_ask.values,
        "ca": d.close_ask.values,
        "dord": dord,
        "hour": d.timestamp_utc.dt.hour.values.astype(np.int8),
    }
    for k in ("hb", "lb", "ob", "ha", "la", "oa"):
        assert not np.isnan(B[k]).any(), f"NaN in {k}"
    assert (B["ca"] >= B["cb"]).all(), "ask below bid somewhere"
    log(f"[tape] {len(d):,} 1-min bars  {d.timestamp_utc.iloc[0]} .. {d.timestamp_utc.iloc[-1]}"
        f"  ({time.time() - t0:.1f}s)")
    return B


# ============================================================================= 2. signal
def build_entries(B):
    """Mirror of live_bot._macro/_refs/_scores/_resolve/_tier for the «1ден» frame,
    evaluated on a 15-minute checkpoint grid over the PARTIAL daily bar."""
    t0 = time.time()
    cols = ["timestamp_utc", "open_bid", "high_bid", "low_bid", "close_bid",
            "open_ask", "high_ask", "low_ask", "close_ask"]
    d = pq.read_table(P15MIN, columns=cols).to_pandas().sort_values("timestamp_utc").reset_index(drop=True)
    d["o"] = (d.open_bid + d.open_ask) / 2
    d["h"] = (d.high_bid + d.high_ask) / 2
    d["l"] = (d.low_bid + d.low_ask) / 2
    d["c"] = (d.close_bid + d.close_ask) / 2
    ny = d.timestamp_utc.dt.tz_convert("America/New_York")
    d["day"] = (ny + pd.Timedelta(hours=7)).dt.normalize().dt.tz_localize(None)

    daily = d.groupby("day").agg(Open=("o", "first"), High=("h", "max"),
                                 Low=("l", "min"), Close=("c", "last"))
    idx = daily.index
    log(f"[signal] daily bars {len(daily)}  {idx[0].date()} .. {idx[-1].date()}")

    gdx = pd.read_csv(F_GDX, parse_dates=["Date"]).set_index("Date")["Close"]
    dxy = pd.read_csv(F_DXY, parse_dates=["Date"]).set_index("Date")["Close"]
    rr = pd.read_csv(F_RR)
    rr["observation_date"] = pd.to_datetime(rr["observation_date"])
    rr["DFII10"] = pd.to_numeric(rr["DFII10"], errors="coerce")
    rr = rr.dropna().set_index("observation_date")["DFII10"]

    g = daily["Close"]
    gd = gdx.reindex(idx).ffill()          # live_bot._macro
    dx = dxy.reindex(idx).ffill()
    r = rr.reindex(idx).ffill()

    # macro is computed on gold_h = completed days STRICTLY BEFORE the live day -> .shift(1)
    raw_min = (gd.pct_change(50) - g.pct_change(50)).shift(1)
    raw_dol = (-(dx.pct_change(20))).shift(1)
    raw_rat = (-(r - r.shift(20))).shift(1)
    m_min = (raw_min > 0).fillna(False)
    m_dol = (raw_dol > 0).fillna(False)
    m_rat = (raw_rat > 0).fillna(False)
    # live never sees a NaN macro (it pulls 2y of every input); before GDX exists the
    # comparison silently yields False, which would fabricate a short bias -> excluded.
    mac_ok = raw_min.notna() & raw_dol.notna() & raw_rat.notna()

    R = pd.DataFrame(index=idx)
    R["sma50"] = g.rolling(50).mean().shift(1)      # _refs on gold_h
    R["sma20"] = g.rolling(20).mean().shift(1)
    R["ago5"] = g.shift(6)                          # c.shift(5).iloc[-1] of gold_h
    R["ago20"] = g.shift(21)
    R["low20"] = daily["Low"].rolling(20).min().shift(1)
    R["high20"] = daily["High"].rolling(20).max().shift(1)
    R["n_hist"] = np.arange(len(idx))               # len(gold_h)
    R["mac_ok"] = mac_ok.values
    R["m_min"] = m_min.values
    R["m_dol"] = m_dol.values
    R["m_rat"] = m_rat.values

    d["run_h"] = d.groupby("day")["h"].cummax()     # PARTIAL daily bar at this checkpoint
    d["run_l"] = d.groupby("day")["l"].cummin()
    X = d.join(R, on="day")

    # _scores reads Close/High/Low of the LAST bar of the frame = the partial daily bar
    cN, hN, lN = X.c.values, X.run_h.values, X.run_l.values
    s50, s20, a5, a20, l20, h20 = (X.sma50.values, X.sma20.values, X.ago5.values,
                                   X.ago20.values, X.low20.values, X.high20.values)
    nn = lambda a: ~np.isnan(a)
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
    ls = ml + lp                      # _scores long score
    ss = (3 - ml) + sp                # _scores short score
    m3l = ml == 3
    m3s = ml == 0

    def tier(score, m3):              # _tier
        return np.where(m3, 3, np.where(score >= 6, 2, np.where(score >= 4, 1, 0)))

    tl, tsh = tier(ls, m3l), tier(ss, m3s)
    direction = np.where(ls > ss, 1, np.where(ss > ls, -1, 0))       # _resolve
    score = np.where(ls > ss, ls, np.where(ss > ls, ss, np.maximum(ls, ss)))
    tk = np.where(ls > ss, tl, np.where(ss > ls, tsh, 0))
    ok_hist = (X.n_hist.values >= MIN_HISTORY) & X.mac_ok.values
    actionable = (direction != 0) & (tk > 0) & ok_hist
    log(f"[signal] checkpoints {len(X):,}  actionable {int(actionable.sum()):,}")

    # ---- anti-spam mirror (live_bot.py:1439-1476, WITHOUT the v5.8a re-offer) ----
    tsmin = X.timestamp_utc.values.astype("datetime64[m]").astype(np.int64)
    keys = np.where(actionable,
                    np.char.add(np.char.add(np.array([DIR_NAME[x] for x in direction]), ":"),
                                np.array([TIER_NAME[x] for x in tk])), "")
    last_key = ""
    last_dir = ""
    last_tier = 0
    last_ts = None
    picked = []
    for i in range(len(X)):
        if not actionable[i]:
            last_key = ""          # live_bot.py:1439 — setup died -> key reset
            continue
        k = keys[i]
        dr = DIR_NAME[direction[i]]
        tr = int(tk[i])
        mins = None if last_ts is None else (tsmin[i] - last_ts)
        tier_up = (tr > last_tier) and (dr == last_dir)
        cool_ok = (mins is None or mins >= COOL_MIN
                   or (dr != last_dir and mins >= COOL_FLIP_MIN) or tier_up)
        if (k != last_key or tier_up) and cool_ok:
            picked.append(i)
            last_key, last_dir, last_tier, last_ts = k, dr, tr, tsmin[i]
    log(f"[signal] cards after anti-spam: {len(picked):,}  ({time.time() - t0:.1f}s)")

    # ---- map decision time -> executable 1-min entry bar ----
    # the 15-min checkpoint bar labelled T closes at T+15m; the decision is only knowable then,
    # so the fill is the first 1-min bar at or after T+15m.
    sig_ts = X.timestamp_utc.values[picked]
    want = (sig_ts.astype("datetime64[m]") + np.timedelta64(15, "m"))
    j = np.searchsorted(B["tsmin"], want.astype(np.int64), side="left")
    ok = j < len(B["tsmin"])
    gapmin = np.where(ok, B["tsmin"][np.clip(j, 0, len(B["tsmin"]) - 1)] - want.astype(np.int64), 10 ** 9)
    ok &= gapmin <= 120            # do not chase an entry across a weekend/holiday hole
    picked = np.array(picked)[ok]
    j = j[ok]
    sig_ts = sig_ts[ok]
    log(f"[signal] executable entries: {len(j):,}  (dropped {int((~ok).sum())} unfillable)")

    dirn = np.array([DIR_NAME[x] for x in direction])[picked]
    entry_px = np.where(dirn == "long", B["oa"][j], B["ob"][j])    # live_bot._entry_side
    ny_entry = pd.DatetimeIndex(B["ts"][j]).tz_localize("UTC").tz_convert("America/New_York")
    et_min = ny_entry.hour * 60 + ny_entry.minute
    us_shield = ((et_min >= 8 * 60 + 25) & (et_min <= 9 * 60 + 15))   # live_bot.SHIELD_ET

    E = pd.DataFrame({
        "timestamp_utc": B["ts"][j],                 # the bar the fill happens on
        "signal_utc": sig_ts,                        # the 15-min checkpoint that decided it
        "bar_index": j.astype(np.int64),
        "direction": dirn,
        "tier": np.array([TIER_NAME[x] for x in tk])[picked],
        "score": score[picked].astype(np.int16),
        "entry_px": entry_px,
        "spread_at_entry": (B["ca"][j] - B["cb"][j]),
        "us_shield_short_block": us_shield & (dirn == "short"),
    })
    E.to_parquet(OUT_ENTRIES, index=False)
    log(f"[signal] wrote {OUT_ENTRIES}  n={len(E)}")
    return E


# ============================================================================= 3. simulator
def _one_trade(i0, direction, entry_px, geom, B):
    """Walk forward bar by bar from the bar AFTER i0. Returns dict or None."""
    s = 1 if direction == "long" else -1
    tps = geom["tps"]
    tp_lv = [entry_px + s * dist for _f, dist in tps]
    cur_sl = entry_px - s * geom["sl"]
    be = geom["be_after_tp1"]

    dord = B["dord"]
    n = len(dord)
    a = i0 + 1                                      # STRICTLY after the entry bar
    end_ord = dord[i0] + TIME_EXIT_DAYS
    b = int(np.searchsorted(dord, end_ord, side="left"))
    b = min(b, n)
    if a >= b:
        return None

    if s == 1:                                      # long exits on the BID
        op = B["ob"][a:b].tolist(); hi = B["hb"][a:b].tolist(); lo = B["lb"][a:b].tolist()
    else:                                           # short exits on the ASK
        op = B["oa"][a:b].tolist(); hi = B["ha"][a:b].tolist(); lo = B["la"][a:b].tolist()

    filled = [False] * len(tps)
    rem = 1.0
    gross = 0.0
    n_tp = 0
    n_fills = 0          # П3 (одит 18.08): БРОЙ ИЗПЪЛНЕНИЯ, не крака на позицията
    exit_k = None
    kind = None
    for k in range(len(op)):
        o = op[k]; h = hi[k]; l = lo[k]
        # --- STOP FIRST (pessimistic, mirrors live_bot.track_trade line 1059) ---
        if (l <= cur_sl) if s == 1 else (h >= cur_sl):
            gap = (o <= cur_sl) if s == 1 else (o >= cur_sl)
            px = o if gap else cur_sl                # gap beyond the level fills at the open
            gross += rem * s * (px - entry_px)
            rem = 0.0
            n_fills += 1
            exit_k = k
            if n_tp == 0:
                kind = "stop"
            elif be:
                kind = f"be-stop-after-tp{n_tp}"
            else:
                kind = f"stop-after-tp{n_tp}"
            break
        # --- take profits, in ladder order, like live_bot ---
        for ti in range(len(tps)):
            if filled[ti]:
                continue
            lv = tp_lv[ti]
            if (h >= lv) if s == 1 else (l <= lv):
                gap = (o >= lv) if s == 1 else (o <= lv)
                px = o if gap else lv
                gross += tps[ti][0] * s * (px - entry_px)
                rem -= tps[ti][0]
                filled[ti] = True
                n_tp += 1
                n_fills += 1
                if ti == 0 and be:
                    cur_sl = entry_px               # break-even, live from the NEXT bar
        if rem <= 1e-12:
            exit_k = k
            kind = f"tp{len(tps)}"
            break

    if exit_k is None:                              # --- time exit ---
        if b < n:
            o_exit = B["ob"][b] if s == 1 else B["oa"][b]
            exit_idx = b
        else:
            o_exit = B["cb"][n - 1] if s == 1 else B["ca"][n - 1]
            exit_idx = n - 1
        gross += rem * s * (o_exit - entry_px)
        rem = 0.0
        n_fills += 1
        kind = f"time-after-tp{n_tp}" if n_tp else "time"
    else:
        exit_idx = a + exit_k

    net = gross - SLIP_PER_TRADE
    # 🔴 П3 (одит 18.08) · `net` вади слипа ВЕДНЪЖ на сделка. Мерено: стълбата
    # прави 2.122 изпълнения, едноцелевите — 1.000. Тоест многокраките геометрии
    # плащат по-малко, отколкото биха платили наистина, и това е СИСТЕМНО
    # предимство (−0.0224$/сделка за доставената). `net` НЕ се мени, за да
    # останат записаните числа възпроизводими; истината идва до него.
    net_per_fill = gross - SLIP_PER_TRADE * n_fills
    return {"exit_index": int(exit_idx), "gross": gross, "net": net,
            "net_per_fill": net_per_fill, "n_fills": int(n_fills), "kind": kind,
            "n_tp": n_tp,
            "hold_min": int((B["tsmin"][exit_idx] - B["tsmin"][i0])),
            "spread_exit": float(B["ca"][exit_idx] - B["cb"][exit_idx])}


def simulate_paired(entries, geom, B):
    """Every entry, no non-overlap skipping. Overlapping trades are NOT tradeable as a
    portfolio, but they give a PAIRED sample: geometry A and geometry B on the same
    entries, so the difference isolates the geometry from entry-timing luck."""
    idxs = entries["bar_index"].values
    dirs = entries["direction"].values
    pxs = entries["entry_px"].values
    net = np.full(len(idxs), np.nan)
    for p in range(len(idxs)):
        r = _one_trade(int(idxs[p]), dirs[p], float(pxs[p]), geom, B)
        if r is not None:
            net[p] = r["net"]
    return net


def simulate(entries, geom, B, non_overlap=True, label="", ne_e_sravnenie=False):
    """entries: DataFrame with bar_index, direction, entry_px (chronological).

    🔴 П1 (одит 18.08) · BLOCKER. При non_overlap=True филтърът ползва
    `busy_until = r["exit_index"]` — ИЗХОД на самата геометрия. Значи всяка
    геометрия получава РАЗЛИЧНА извадка входове. Мерено: от едни и същи 6846
    входа излизат 950 (широка) до 2970 (тясна) сделки, Jaccard пада до 0.295,
    и КЛАСАЦИЯТА СЕ ОБРЪЩА (доставената е 1-ва сдвоено, 3-та неприпокрито;
    една геометрия мърда с 0.557$/сделка само от избора на подизвадка — повече
    от целия разсейн между геометриите).

    Затова: за СРАВНЕНИЕ между геометрии се ползва САМО `simulate_paired`.
    Тази функция дава ТЪРГУЕМ портфейл на ЕДНА геометрия — законна употреба,
    но не и сравнение. За да я извикаш с non_overlap=True, трябва да заявиш
    `ne_e_sravnenie=True`, тоест да кажеш на глас, че знаеш какво правиш.
    """
    if non_overlap and not ne_e_sravnenie:
        raise ValueError(
            "geom_harness П1: simulate(non_overlap=True) НЕ Е сравнение между "
            "геометрии — филтърът зависи от изхода на самата геометрия и всяка "
            "получава различна извадка (950 срещу 2970 сделки; класацията се "
            "обръща). За сравнение ползвай simulate_paired(). Ако наистина ти "
            "трябва търгуем портфейл на ЕДНА геометрия, извикай с "
            "ne_e_sravnenie=True.")
    idxs = entries["bar_index"].values
    dirs = entries["direction"].values
    pxs = entries["entry_px"].values
    order = np.argsort(idxs, kind="stable")
    res = []
    skipped = 0
    busy_until = -1
    for p in order:
        i0 = int(idxs[p])
        if non_overlap and i0 <= busy_until:
            skipped += 1
            continue
        r = _one_trade(i0, dirs[p], float(pxs[p]), geom, B)
        if r is None:
            skipped += 1
            continue
        r["entry_index"] = i0
        r["direction"] = dirs[p]
        r["entry_utc"] = B["ts"][i0]
        r["tier"] = entries["tier"].values[p] if "tier" in entries else ""
        busy_until = r["exit_index"]
        res.append(r)
    T = pd.DataFrame(res)
    T.attrs["skipped"] = skipped
    T.attrs["geom"] = geom["name"]
    T.attrs["label"] = label
    return T


def summarize(T, geom_name, skipped=None):
    if len(T) == 0:
        return {"n": 0}
    net = T["net"].values
    out = {
        "geometry": geom_name,
        "n_trades": int(len(T)),
        "skipped_overlapping": int(T.attrs.get("skipped", skipped or 0)),
        "win_rate_pct": round(float((net > 0).mean() * 100), 2),
        "usd_per_trade_net": round(float(net.mean()), 4),
        "total_usd_net": round(float(net.sum()), 2),
        "gross_per_trade": round(float(T["gross"].mean()), 4),
        "median_hold_min": int(np.median(T["hold_min"].values)),
        "mean_hold_min": int(T["hold_min"].mean()),
        "exit_kinds": {k: int(v) for k, v in T["kind"].value_counts().items()},
        "span": f"{pd.Timestamp(T['entry_utc'].min()).date()} .. {pd.Timestamp(T['entry_utc'].max()).date()}",
        "long_per_trade": round(float(net[T.direction.values == "long"].mean()), 4)
                          if (T.direction.values == "long").any() else None,
        "short_per_trade": round(float(net[T.direction.values == "short"].mean()), 4)
                           if (T.direction.values == "short").any() else None,
        "n_long": int((T.direction.values == "long").sum()),
        "n_short": int((T.direction.values == "short").sum()),
    }
    sd = net.std(ddof=1) if len(net) > 1 else 0.0
    out["t_stat"] = round(float(net.mean() / (sd / np.sqrt(len(net)))), 3) if sd > 0 else None
    ntp = T["n_tp"].values
    out["reached_tp1_pct"] = round(float((ntp >= 1).mean() * 100), 2)
    out["reached_tp2_pct"] = round(float((ntp >= 2).mean() * 100), 2)
    out["reached_tp3_pct"] = round(float((ntp >= 3).mean() * 100), 2)
    out["mean_spread_at_exit"] = round(float(T["spread_exit"].mean()), 3)
    # 🔴 П4 (одит 18.08) · КОЛКО ОТ СДЕЛКИТЕ РЕШАВА ТАЙМЕРЪТ, а не геометрията.
    # Мерено при 5 дни: 0.06% (тясна) до 49.46% (широка). Тоест при широка
    # геометрия половината сделки не са резултат на стопове и цели. Без това
    # число сравнението изглежда като сравнение на геометрии, а не е.
    _kind = T["kind"].astype(str)
    out["time_exit_pct"] = round(float(_kind.str.startswith("time").mean() * 100), 2)
    out["stop_exit_pct"] = round(float(_kind.str.contains("stop").mean() * 100), 2)
    # 🔴 П3 · разходът на ИЗПЪЛНЕНИЕ до разхода на сделка
    if "n_fills" in T:
        out["mean_fills_per_trade"] = round(float(T["n_fills"].mean()), 3)
        out["usd_per_trade_net_per_fill"] = round(float(T["net_per_fill"].mean()), 4)
        out["slip_model_note"] = (
            "`usd_per_trade_net` вади слипа ВЕДНЪЖ на сделка (както винаги е било). "
            "`usd_per_trade_net_per_fill` го вади на ИЗПЪЛНЕНИЕ. Победител, който "
            "печели само по първото, НЕ е победител — многокраките геометрии са "
            "системно облагодетелствани от първия модел.")
    if "tier" in T and T["tier"].astype(str).str.len().max() > 0:
        out["per_tier_usd"] = {k: [int(len(v)), round(float(v["net"].mean()), 3)]
                               for k, v in T.groupby("tier")}
    return out


def show(title, s):
    log("")
    log("=" * 78)
    log(title)
    log("=" * 78)
    for k, v in s.items():
        log(f"  {k:24s} {v}")


# ============================================================================= 4. validation
def _fake_tape(rows):
    """rows = list of (open_bid, high_bid, low_bid, close_bid, spread). ask = bid + spread."""
    ob = np.array([r[0] for r in rows], float)
    hb = np.array([r[1] for r in rows], float)
    lb = np.array([r[2] for r in rows], float)
    cb = np.array([r[3] for r in rows], float)
    sp = np.array([r[4] for r in rows], float)
    n = len(rows)
    return {
        "ts": pd.date_range("2020-01-01", periods=n, freq="1min").values,
        "tsmin": np.arange(n, dtype=np.int64) + 26298000,
        "ob": ob, "hb": hb, "lb": lb, "cb": cb,
        "oa": ob + sp, "ha": hb + sp, "la": lb + sp, "ca": cb + sp,
        "dord": np.zeros(n, np.int32),
        "hour": np.zeros(n, np.int8),
    }


def validate_synthetic():
    log("")
    log("### VALIDATION (a) — synthetic, hand-computable")
    ok = True

    # --- A1 LONG: TP1 then break-even stop -------------------------------------
    # entry bar 0: open_ask = 2000.00 -> entry 2000.00 (long buys the ASK)
    # bar 1: bid high 2005      -> nothing (TP1 level 2007.50)
    # bar 2: bid open 2004, high 2008.10 -> TP1 fills AT the level 2007.50 (no gap)
    #        same bar: TP2 level 2012 not touched
    # bar 3: bid open 2003, low 1999.50  -> stop is now break-even 2000.00, touched, no gap
    # expected gross = 1/3*(2007.50-2000) + 2/3*(2000-2000) = 2.5 ; net = 2.48
    rows = [(1999.8, 2000.2, 1999.5, 2000.0, 0.20),
            (2000.0, 2005.0, 1999.9, 2004.0, 0.20),
            (2004.0, 2008.1, 2003.5, 2007.9, 0.20),
            (2003.0, 2003.5, 1999.5, 2000.5, 0.20),
            (2000.0, 2001.0, 1999.0, 2000.0, 0.20)]
    F = _fake_tape(rows)
    entry = F["oa"][0]
    assert abs(entry - 2000.0) < 1e-9, entry
    r = _one_trade(0, "long", entry, GEOM_SHIPPED, F)
    exp = 2.5 - SLIP_PER_TRADE
    good = abs(r["net"] - exp) < 1e-9 and r["kind"] == "be-stop-after-tp1" and r["n_tp"] == 1
    ok &= good
    log(f"  A1 long TP1->BE     net={r['net']:.4f} exp={exp:.4f} kind={r['kind']}  "
        f"{'PASS' if good else 'FAIL'}")

    # --- A2 stop and TP in the SAME bar -> STOP must win ------------------------
    # bar 1 bid: low 1979.0 (stop 1980.00 touched) AND high 2008.0 (TP1 touched)
    rows = [(1999.8, 2000.2, 1999.5, 2000.0, 0.20),
            (2000.0, 2008.0, 1979.0, 1990.0, 0.20),
            (1990.0, 1991.0, 1989.0, 1990.0, 0.20)]
    F = _fake_tape(rows)
    r = _one_trade(0, "long", 2000.0, GEOM_SHIPPED, F)
    exp = -20.0 - SLIP_PER_TRADE
    good = abs(r["net"] - exp) < 1e-9 and r["kind"] == "stop" and r["n_tp"] == 0
    ok &= good
    log(f"  A2 stop beats TP    net={r['net']:.4f} exp={exp:.4f} kind={r['kind']}  "
        f"{'PASS' if good else 'FAIL'}")

    # --- A3 GAP beyond the stop fills at the OPEN, not the level ----------------
    rows = [(1999.8, 2000.2, 1999.5, 2000.0, 0.20),
            (1975.0, 1976.0, 1970.0, 1974.0, 0.20)]
    F = _fake_tape(rows)
    r = _one_trade(0, "long", 2000.0, GEOM_SHIPPED, F)
    exp = (1975.0 - 2000.0) - SLIP_PER_TRADE
    good = abs(r["net"] - exp) < 1e-9 and r["kind"] == "stop"
    ok &= good
    log(f"  A3 gap fills @open  net={r['net']:.4f} exp={exp:.4f}  {'PASS' if good else 'FAIL'}")

    # --- A4 SHORT full ladder, exits on the ASK --------------------------------
    # short enters at the BID of bar 0 = 2000.00 (bid), spread 0.20 -> ask 2000.20
    # TP levels on the ask: 1992.50 / 1988.00 / 1980.00 ; stop ask 2020.00
    rows = [(2000.0, 2000.4, 1999.6, 2000.0, 0.20),      # entry bar (bid open 2000.0)
            (1999.0, 1999.5, 1992.0, 1992.4, 0.20),      # ask low 1992.20 -> TP1 @1992.50
            (1992.4, 1993.0, 1987.5, 1987.8, 0.20),      # ask low 1987.70 -> TP2 @1988.00
            (1987.8, 1988.0, 1979.5, 1979.6, 0.20)]      # ask low 1979.70 -> TP3 @1980.00
    F = _fake_tape(rows)
    entry = F["ob"][0]
    assert abs(entry - 2000.0) < 1e-9
    r = _one_trade(0, "short", entry, GEOM_SHIPPED, F)
    exp = (7.5 + 12.0 + 20.0) / 3 - SLIP_PER_TRADE
    good = abs(r["net"] - exp) < 1e-9 and r["kind"] == "tp3" and r["n_tp"] == 3
    ok &= good
    log(f"  A4 short full ladder net={r['net']:.4f} exp={exp:.4f} kind={r['kind']}  "
        f"{'PASS' if good else 'FAIL'}")

    # --- A5 FLAT geometry on the same A1 path ----------------------------------
    # entry 2000.00 long, TP 2015 / SL 1985 ; the A1 path never reaches either ->
    # extend so the bid finally reaches 2015.30 -> TP fills at 2015.00
    rows = [(1999.8, 2000.2, 1999.5, 2000.0, 0.20),
            (2000.0, 2005.0, 1999.9, 2004.0, 0.20),
            (2004.0, 2008.1, 2003.5, 2007.9, 0.20),
            (2007.9, 2015.3, 2007.0, 2015.0, 0.20)]
    F = _fake_tape(rows)
    r = _one_trade(0, "long", 2000.0, GEOM_FLAT, F)
    exp = 15.0 - SLIP_PER_TRADE
    good = abs(r["net"] - exp) < 1e-9 and r["kind"] == "tp1"
    ok &= good
    log(f"  A5 flat TP          net={r['net']:.4f} exp={exp:.4f} kind={r['kind']}  "
        f"{'PASS' if good else 'FAIL'}")

    # --- A6 no-lookahead: the ENTRY bar itself must never produce an exit -------
    # bar 0 bid low 1900 would blow the stop, but it is the entry bar -> ignored
    rows = [(1999.8, 2100.0, 1900.0, 2000.0, 0.20),
            (2000.0, 2000.5, 1999.5, 2000.0, 0.20),
            (2000.0, 2000.5, 1999.5, 2000.0, 0.20)]
    F = _fake_tape(rows)
    r = _one_trade(0, "long", 2000.0, GEOM_SHIPPED, F)
    good = r["kind"].startswith("time")
    ok &= good
    log(f"  A6 entry bar unused kind={r['kind']}  {'PASS' if good else 'FAIL'}")

    log(f"  --> synthetic validation {'PASS' if ok else 'FAIL'}")
    return ok


def validate_shift(E, B):
    log("")
    log("### VALIDATION (b) — shift every entry forward by one bar")
    base = simulate(E, GEOM_SHIPPED, B, ne_e_sravnenie=True, label="base")
    E2 = E.copy()
    E2["bar_index"] = E2["bar_index"] + 1
    E2 = E2[E2.bar_index < len(B["dord"])].copy()
    E2["entry_px"] = np.where(E2.direction.values == "long",
                              B["oa"][E2.bar_index.values], B["ob"][E2.bar_index.values])
    sh = simulate(E2, GEOM_SHIPPED, B, label="shift+1")
    a = summarize(base, "base")["usd_per_trade_net"]
    b = summarize(sh, "shift+1")["usd_per_trade_net"]
    good = abs(a - b) > 1e-9
    log(f"  base   $/trade = {a:+.4f}   n={len(base)}")
    log(f"  +1 bar $/trade = {b:+.4f}   n={len(sh)}")
    log(f"  delta          = {b - a:+.4f}   -> {'PASS (no stale index / no lookahead)' if good else 'FAIL'}")
    return good, base


def blind_entries(E, B, seed=BLIND_SEED):
    """Random entry timestamps drawn from the SAME hour-of-day distribution and the same
    long/short mix, inside the same span."""
    rng = np.random.default_rng(seed)
    lo = int(E.bar_index.min())
    hi = int(E.bar_index.max())
    hours = B["hour"][lo:hi + 1]
    pools = {h: np.flatnonzero(hours == h) + lo for h in range(24)}
    real_hours = pd.DatetimeIndex(E.timestamp_utc).hour.values
    picks = np.array([rng.choice(pools[h]) for h in real_hours])
    dirs = E.direction.values.copy()
    return pd.DataFrame({
        "bar_index": picks,
        "direction": dirs,
        "entry_px": np.where(dirs == "long", B["oa"][picks], B["ob"][picks]),
        "tier": E.tier.values,
        "timestamp_utc": B["ts"][picks],
    }).sort_values("bar_index").reset_index(drop=True)


def validate_blind(E, B):
    log("")
    log("### VALIDATION (c) — blind control: random entries, same hour-of-day mix")
    Eb = blind_entries(E, B)
    out = {}
    for g in (GEOM_SHIPPED, GEOM_FLAT):
        T = simulate(Eb, g, B, label="blind")
        s = summarize(T, "BLIND " + g["name"])
        show("BLIND CONTROL — " + g["name"], s)
        out[g["name"]] = s
    v = out[GEOM_SHIPPED["name"]]["usd_per_trade_net"]
    good = abs(v) < 1.5
    log(f"  --> blind $/trade (shipped geometry) = {v:+.4f}  "
        f"{'PASS (no structural edge baked into the simulator)' if good else 'FAIL'}")
    return good, out


# ============================================================================= main
def main():
    B = load_tape()
    ok_syn = validate_synthetic()
    if not ok_syn:
        log("SYNTHETIC VALIDATION FAILED — stopping.")
        sys.exit(1)

    E = build_entries(B)
    ok_shift, base = validate_shift(E, B)
    ok_blind, blind = validate_blind(E, B)

    s_ship = summarize(base, GEOM_SHIPPED["name"])
    show("BASELINE — SHIPPED GEOMETRY", s_ship)

    T_flat = simulate(E, GEOM_FLAT, B, ne_e_sravnenie=True, label="flat")
    s_flat = summarize(T_flat, GEOM_FLAT["name"])
    show("CHALLENGER — FLAT 150p / 150p", s_flat)

    # ---- paired test: both geometries on EVERY entry (overlapping, not tradeable, but paired)
    ps = simulate_paired(E, GEOM_SHIPPED, B)
    pf = simulate_paired(E, GEOM_FLAT, B)
    m = ~(np.isnan(ps) | np.isnan(pf))
    diff = pf[m] - ps[m]
    # 🔴 П2 (одит 18.08) · ДОТУК ТУК СЕ РЕСЕМПЛИРАШЕ КАТО НЕЗАВИСИМО. Не е:
    # средно 6.4 сделки текат едновременно в момента на вход (макс 37),
    # автокорелация на разликата lag1 +0.340, lag2 +0.365. Мерена ширина на
    # интервала: iid 0.4878$ срещу блоков 0.83–0.94$ → 1.70–1.92× ПО-ТЕСЕН.
    # Контрола: същият блоков бутстрап върху РАЗБЪРКАНА последователност дава
    # отношение 0.98, тоест разширението е истинска зависимост, не артефакт.
    # Сега: блоков бутстрап ПО КАЛЕНДАРЕН ДЕН, като в F28/F30/F31.
    rng = np.random.default_rng(BLIND_SEED)
    _dni = pd.to_datetime(pd.Series(B["ts"])[E["bar_index"].values[m]].values).normalize()
    _g = pd.DataFrame({"d": diff, "day": _dni.values}).groupby("day")["d"].agg(["sum", "count"])
    _S, _C = _g["sum"].to_numpy(), _g["count"].to_numpy()
    _k = len(_S)
    _iz = rng.integers(0, _k, size=(4000, _k))
    boot = _S[_iz].sum(axis=1) / np.maximum(_C[_iz].sum(axis=1), 1)
    ci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

    # --- VALIDATION (d): the two code paths must agree trade-for-trade -------------
    assert E.bar_index.is_unique, "duplicate entry bars"
    ref = pd.Series(ps, index=E.bar_index.values)
    got = base.set_index("entry_index")["net"]
    delta = (got - ref.reindex(got.index)).abs().max()
    ok_pair = bool(delta < 1e-12)
    log("")
    log("### VALIDATION (d) — non-overlap simulator vs paired simulator, trade for trade")
    log(f"  max |difference| over {len(got)} shared trades = {delta:.2e}  "
        f"{'PASS' if ok_pair else 'FAIL'}")
    log("")
    log("### PAIRED TEST — both geometries on all %d entries (overlap allowed)" % len(E))
    log(f"  paired n            = {int(m.sum())}")
    log(f"  shipped $/trade     = {ps[m].mean():+.4f}")
    log(f"  flat    $/trade     = {pf[m].mean():+.4f}")
    log(f"  flat - shipped      = {diff.mean():+.4f}   95% bootstrap CI "
        f"[{ci[0]:+.4f}, {ci[1]:+.4f}]")
    log(f"  -> {'flat is better with 95% confidence' if ci[0] > 0 else ('shipped is better with 95% confidence' if ci[1] < 0 else 'NOT separable at 95% — the two geometries are statistically tied')}")

    log("")
    log("=" * 78)
    log("HEAD TO HEAD (identical entry set, identical tape, identical cost model)")
    log("=" * 78)
    bs = blind[GEOM_SHIPPED["name"]]["usd_per_trade_net"]
    bf = blind[GEOM_FLAT["name"]]["usd_per_trade_net"]
    log(f"  shipped : {s_ship['usd_per_trade_net']:+.4f} $/trade  x {s_ship['n_trades']} "
        f"= {s_ship['total_usd_net']:+.2f} $   win {s_ship['win_rate_pct']}%   "
        f"(blind control {bs:+.4f}  ->  edge over random {s_ship['usd_per_trade_net'] - bs:+.4f})")
    log(f"  flat    : {s_flat['usd_per_trade_net']:+.4f} $/trade  x {s_flat['n_trades']} "
        f"= {s_flat['total_usd_net']:+.2f} $   win {s_flat['win_rate_pct']}%   "
        f"(blind control {bf:+.4f}  ->  edge over random {s_flat['usd_per_trade_net'] - bf:+.4f})")

    rep = {"validations": {"synthetic": ok_syn, "shift_one_bar": bool(ok_shift),
                           "blind_control": bool(ok_blind),
                           "paired_vs_nonoverlap_identical": ok_pair},
           "cost_model": {"spread": "real, from the tape, on the correct side of every fill",
                          "slippage_usd_per_trade": SLIP_PER_TRADE,
                          "commission": "not modelled"},
           "paired": {"n": int(m.sum()), "shipped": round(float(ps[m].mean()), 4),
                      "flat": round(float(pf[m].mean()), 4),
                      "flat_minus_shipped": round(float(diff.mean()), 4),
                      "ci95": [round(ci[0], 4), round(ci[1], 4)]},
           "shipped": s_ship, "flat": s_flat, "blind": blind}
    OUT_REPORT.write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    log(f"\n[report] {OUT_REPORT}")


if __name__ == "__main__":
    main()
