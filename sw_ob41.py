# -*- coding: utf-8 -*-
"""Адверсарна проверка на находка №41: '_мозък_следене' гълта стопове.
РЕАЛНИ данни: live/brain_result.jsonl (15 записа) + live/live_journal.jsonl (3554 ръна)
+ истински 5м барове GC=F от Yahoo, преведени в спот чрез базиса от дневника."""
import sys, io, json, os
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd, numpy as np

D = os.path.dirname(os.path.abspath(__file__))
J = [json.loads(l) for l in io.open(os.path.join(D, "live/live_journal.jsonl"), encoding="utf-8")]
R = [json.loads(l) for l in io.open(os.path.join(D, "live/brain_result.jsonl"), encoding="utf-8")]

# --- 1) серия price_user точно както я смята ботът (ред 3008) ---
rows = []
for x in J:
    sp, bar, bs = x.get("spot"), x.get("bar"), x.get("basis")
    if sp is not None:
        pu = float(sp)
    elif bar is not None and bs is not None:
        pu = round(float(bar) - float(bs), 2)
    else:
        pu = None
    rows.append((pd.Timestamp(x["run_utc"]), pu, x.get("basis"), x.get("stale_bar")))
S = pd.DataFrame(rows, columns=["ts", "pu", "basis", "stale"]).dropna(subset=["pu"]).set_index("ts").sort_index()
print("рънове с цена:", len(S), S.index.min(), "→", S.index.max())
d = S.index.to_series().diff().dt.total_seconds().div(60)
print("пауза между рънове (мин): медиана %.1f  p90 %.1f  max %.1f" % (d.median(), d.quantile(.9), d.max()))

# --- 2) истински 5м барове ---
CACHE = os.path.join(D, "sw_gc5m.pkl")
if os.path.exists(CACHE):
    B = pd.read_pickle(CACHE)
else:
    import yfinance as yf
    B = yf.download("GC=F", period="1mo", interval="5m", progress=False, auto_adjust=False)
    if isinstance(B.columns, pd.MultiIndex):
        B.columns = B.columns.droplevel(1)
    B.index = B.index.tz_convert("UTC").tz_localize(None)
    B.to_pickle(CACHE)
print("барове GC=F 5м:", len(B), B.index.min(), "→", B.index.max())

# базис за всеки бар: последният известен базис от дневника (както го ползва ботът)
bs = S["basis"].dropna()
bs = bs[~bs.index.duplicated(keep="last")]
bas = bs.reindex(bs.index.union(B.index)).ffill().reindex(B.index)
print("базис по баровете: медиана %.2f  мин %.2f  макс %.2f  стд %.2f"
      % (bas.median(), bas.min(), bas.max(), bas.std()))

def scal(rec):
    """точно логиката на _мозък_следене: една скаларна цена на рън, стопът пръв."""
    зн = 1 if rec["посока"] == "long" else -1
    t0, t1 = pd.Timestamp(rec["отворен"]), pd.Timestamp(rec["затворен"])
    ц1взета = False
    for ts, p in S["pu"].loc[S.index > t0].items():
        if (p - rec["стоп"]) * зн <= 0:
            return ("стоп", rec["стоп"], ts, ц1взета)
        if rec.get("цел2") is not None and (p - rec["цел2"]) * зн >= 0:
            return ("цел2", rec["цел2"], ts, ц1взета)
        if not ц1взета and (p - rec["цел1"]) * зн >= 0:
            ц1взета = True
        if ts > t1 + pd.Timedelta(hours=6):
            break
    return (None, None, None, ц1взета)

def barw(rec, until=None):
    """логиката на track_trade: High/Low на 5м бар, стопът пръв."""
    зн = 1 if rec["посока"] == "long" else -1
    t0 = pd.Timestamp(rec["отворен"])
    t1 = until if until is not None else pd.Timestamp(rec["затворен"])
    ц1взета = False
    sub = B.loc[(B.index > t0) & (B.index <= t1)]
    for ts, r in sub.iterrows():
        hi = float(r["High"]) - float(bas.loc[ts]); lo = float(r["Low"]) - float(bas.loc[ts])
        if pd.isna(hi) or pd.isna(lo):
            continue
        sl = (lo <= rec["стоп"]) if зн == 1 else (hi >= rec["стоп"])
        if sl:
            return ("стоп", rec["стоп"], ts, ц1взета, (rec["стоп"] - lo) if зн == 1 else (hi - rec["стоп"]))
        if rec.get("цел2") is not None and ((hi >= rec["цел2"]) if зн == 1 else (lo <= rec["цел2"])):
            return ("цел2", rec["цел2"], ts, ц1взета, 0.0)
        if not ц1взета and ((hi >= rec["цел1"]) if зн == 1 else (lo <= rec["цел1"])):
            ц1взета = True
    return (None, None, None, ц1взета, 0.0)

print("\n" + "=" * 108)
print("№ посока  отворен          записан изход      | СКАЛАР-реплика       | БАР-реплика (High/Low)     разлика")
print("=" * 108)
съвп = 0; разл = []
for i, rec in enumerate(R, 1):
    s = scal(rec)
    b = barw(rec)
    ok = (s[0] == rec["изход"])
    съвп += ok
    марж = ""
    if b[0] != rec["изход"]:
        марж = "  ⚠ РАЗЛИКА (дълбочина %.2f$)" % b[4]
        разл.append((i, rec, b))
    print("%2d %-5s %s  %-5s %8.2f | %-5s %s %s | %-5s %s%s"
          % (i, rec["посока"], rec["отворен"], rec["изход"], rec["резултат"],
             str(s[0]), str(s[2])[:16], "✓" if ok else "✗",
             str(b[0]), str(b[2])[:16], марж))
print("\nскалар-репликата възпроизвежда записа: %d/%d" % (съвп, len(R)))
