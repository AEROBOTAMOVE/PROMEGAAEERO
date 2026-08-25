# -*- coding: utf-8 -*-
"""СКЕПТИК-СТЕНД: зарежда ПРОИЗВОЛЕН live_bot.py по път и пуска истинския main()
без мрежа. Нищо в логиката на бота не се подменя — само четенията навън."""
import sys, io, os, json, shutil, importlib.util
from pathlib import Path
import numpy as np, pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = Path(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
os.chdir(BASE)
sys.path.insert(0, str(BASE))

lb = None
SENT = []
CFG = {}


def load(path, name="live_bot_x"):
    global lb
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    lb = m
    return m


def _mk(n, freq, end, px, step=0.0, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(end=pd.Timestamp(end), periods=n, freq=freq)
    close = px + np.cumsum(rng.normal(step, max(px * 0.0008, 0.01), n))
    high = close + abs(rng.normal(0, px * 0.0006, n))
    low = close - abs(rng.normal(0, px * 0.0006, n))
    op = close + rng.normal(0, px * 0.0003, n)
    return pd.DataFrame({"Open": op, "High": high, "Low": low, "Close": close,
                         "Volume": rng.integers(100, 1000, n)}, index=idx)


def fake_yf(sym, period="2y", interval="1d"):
    end = CFG.get("gold_end", "2026-08-21")
    intra = CFG.get("intra_end", end + " 12:00")
    if sym == "GC=F" and interval == "1d":
        return _mk(400, "B", end, CFG.get("gold_px", 4600.0), step=CFG.get("gold_step", 0.5), seed=2)
    if sym == "GC=F" and interval == "1m":
        return _mk(2000, "min", intra, CFG.get("gold_px", 4600.0), seed=3)
    if sym == "GC=F" and interval == "5m":
        return _mk(3000, "5min", intra, CFG.get("gold_px", 4600.0), seed=4)
    if sym == "GDX":
        return _mk(400, "B", end, 45.0, step=0.02, seed=5)
    if sym == "DX-Y.NYB":
        return _mk(400, "B", end, 98.0, step=-0.01, seed=6)
    if sym == "^TNX":
        return _mk(400, "B", end, 42.0, step=0.0, seed=7)
    if sym == "SI=F" and interval == "1d":
        return _mk(400, "B", end, 69.0, step=0.01, seed=8)
    if sym == "SI=F":
        return _mk(3000, "5min", intra, 69.0, seed=9)
    raise RuntimeError("непознат символ " + sym)


def fake_rates():
    idx = pd.date_range(end=pd.Timestamp(CFG.get("gold_end", "2026-08-21")), periods=400, freq="B")
    try:
        lb.ЛИХВИ_ИЗТОЧНИК.clear()
        lb.ЛИХВИ_ИЗТОЧНИК.update(вид="реални", тикер="DFII10", резерва=False, дни=1)
    except Exception:
        pass
    return pd.Series(np.linspace(2.0, 1.5, 400), index=idx)


def fake_spot(instr="XAU/USD", market_closed=False, cme_pause=False, **kw):
    mid = CFG.get("spot_mid_s", 69.0) if instr != "XAU/USD" else CFG.get("spot_mid", 4600.0)
    return {"bid": round(mid - 0.2, 3), "ask": round(mid + 0.2, 3), "mid": round(mid, 3),
            "src": "swq", "age_sec": 1.0}


def fake_send(text):
    SENT.append(text)
    return "SENT"


_REAL_DT = None


def patch():
    global _REAL_DT
    _REAL_DT = lb.datetime
    lb._yf = fake_yf
    lb._rates = fake_rates
    lb._spot = fake_spot
    lb._send_raw = fake_send
    lb._cq_fetch = lambda *a, **k: None
    lb._fng_live = lambda *a, **k: None


def set_now(iso):
    fixed = _REAL_DT.fromisoformat(iso)

    class FakeDT(_REAL_DT):
        @classmethod
        def now(cls, tz=None):
            return fixed.replace(tzinfo=tz) if tz is not None else fixed
    lb.datetime = FakeDT


def run(outdir, argv_extra=()):
    SENT.clear()
    old = sys.argv
    sys.argv = ["live_bot.py", "--out", str(outdir)] + list(argv_extra)
    buf = io.StringIO()
    real = sys.stdout
    sys.stdout = buf
    try:
        lb.main()
    finally:
        sys.stdout = real
        sys.argv = old
    return buf.getvalue()


def last_journal(outdir):
    p = Path(outdir) / "live_journal.jsonl"
    rows = [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]
    return rows[-1]


def fresh(outdir, seed_from=None):
    p = Path(outdir)
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True)
    (p / "data").mkdir(exist_ok=True)
    if seed_from:
        for f in Path(seed_from).glob("*.json"):
            shutil.copy(f, p / f.name)
    return p


def meta(outdir):
    return json.loads((Path(outdir) / "meta.json").read_text(encoding="utf-8"))
