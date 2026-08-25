# -*- coding: utf-8 -*-
"""СКЕПТИК · пуска ИСТИНСКИЯ live_bot.main() офлайн в пясъчник със СЧУПЕН мозък."""
import sys, io, os, json, shutil
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)

SB = Path(sys.argv[1]).resolve()          # sb_now или sb_pre
sys.path.insert(0, str(SB))
os.chdir(SB)
import live_bot as lb
print("ФАЙЛ:", lb.__file__)
print("VERSION:", lb.VERSION)
print("CHART_BRAIN в средата:", repr(os.environ.get("CHART_BRAIN")))
print("CHART_BRAIN_ON:", lb.CHART_BRAIN_ON)
print("CB:", lb.CB)
print("CB_ГРЕШКА:", repr(getattr(lb, "CB_ГРЕШКА", "<НЯМА ТАКАВА ПРОМЕНЛИВА>")))

SENT = []
CFG = {"gold_end": "2026-08-20", "gold_px": 4600.0, "intra_end": "2026-08-20 12:00"}

def _mk(n, freq, end, px, step=0.0, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(end=pd.Timestamp(end), periods=n, freq=freq)
    close = px + np.cumsum(rng.normal(step, max(px*0.0008, 0.01), n))
    high = close + abs(rng.normal(0, px*0.0006, n))
    low = close - abs(rng.normal(0, px*0.0006, n))
    op = close + rng.normal(0, px*0.0003, n)
    return pd.DataFrame({"Open": op, "High": high, "Low": low, "Close": close,
                         "Volume": rng.integers(100, 1000, n)}, index=idx)

def fake_yf(sym, period="2y", interval="1d"):
    end = CFG["gold_end"]
    if sym == "GC=F" and interval == "1d":  return _mk(400, "B", end, CFG["gold_px"], step=0.5, seed=2)
    if sym == "GC=F" and interval == "1m":  return _mk(2000, "min", CFG["intra_end"], CFG["gold_px"], seed=3)
    if sym == "GC=F" and interval == "5m":  return _mk(3000, "5min", CFG["intra_end"], CFG["gold_px"], seed=4)
    if sym == "GDX":         return _mk(400, "B", end, 45.0, step=0.02, seed=5)
    if sym == "DX-Y.NYB":    return _mk(400, "B", end, 98.0, step=-0.01, seed=6)
    if sym == "^TNX":        return _mk(400, "B", end, 42.0, seed=7)
    if sym == "SI=F" and interval == "1d": return _mk(400, "B", end, 69.0, step=0.01, seed=8)
    if sym == "SI=F":        return _mk(3000, "5min", CFG["intra_end"], 69.0, seed=9)
    raise RuntimeError("непознат символ " + sym)

def fake_rates():
    idx = pd.date_range(end=pd.Timestamp(CFG["gold_end"]), periods=400, freq="B")
    lb.ЛИХВИ_ИЗТОЧНИК.clear()
    lb.ЛИХВИ_ИЗТОЧНИК.update(вид="реални", тикер="DFII10", резерва=False, дни=1)
    return pd.Series(np.linspace(2.0, 1.5, 400), index=idx)

def fake_spot(instr="XAU/USD", market_closed=False, cme_pause=False, **kw):
    mid = 69.0 if instr != "XAU/USD" else CFG["gold_px"]
    return {"bid": round(mid-0.2,3), "ask": round(mid+0.2,3), "mid": round(mid,3),
            "src": "swq", "age_sec": 1.0}

lb._yf = fake_yf; lb._rates = fake_rates; lb._spot = fake_spot
lb._send_raw = lambda t: (SENT.append(t), "SENT")[1]
lb._cq_fetch = lambda *a, **k: None
lb._fng_live = lambda *a, **k: None

_REAL_DT = lb.datetime
fixed = _REAL_DT.fromisoformat("2026-08-20T12:05:00+00:00")
class FakeDT(_REAL_DT):
    @classmethod
    def now(cls, tz=None):
        return fixed.replace(tzinfo=tz) if tz is not None else fixed.replace(tzinfo=None)
lb.datetime = FakeDT

out = SB / "out"
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True); (out/"data").mkdir()

sys.argv = ["live_bot.py", "--out", str(out)]
buf = io.StringIO(); real = sys.stdout; sys.stdout = buf
code = 0
try:
    lb.main()
except SystemExit as e:
    code = e.code
except Exception as e:
    code = f"{type(e).__name__}: {e}"
finally:
    sys.stdout = real
log = buf.getvalue()

print("\n=== STDOUT на бота (умира в лога на Actions) ===")
for ln in log.splitlines():
    if "мозъ" in ln or "мозък" in ln: print("  ", ln)
print("   [изход от main:", code, "]")

jp = out / "live_journal.jsonl"
print("\n=== ДНЕВНИКЪТ (чете се отвън) ===", jp.exists())
if jp.exists():
    rows = [json.loads(l) for l in jp.open(encoding="utf-8") if l.strip()]
    last = rows[-1]
    for n in last.get("notes", []):
        if "мозъ" in n: print("   БЕЛЕЖКА:", n)
    print("   всички бележки:", len(last.get("notes", [])))
