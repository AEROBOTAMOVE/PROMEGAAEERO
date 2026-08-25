# -*- coding: utf-8 -*-
"""E2E: пуска ЦЕЛИЯ main() с посока short и стрийк 2 и чете реда в дневника."""
import sys, io, os, json, time, tempfile, contextlib, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.argv = ["x"]
import pandas as pd, numpy as np
from pathlib import Path
import live_bot as lb

def _fx(n, start, freq, px, drift=0.0):
    i = pd.date_range(start, periods=n, freq=freq)
    c = px + np.arange(n) * drift + np.sin(np.arange(n) / 7.0) * 2.0
    return pd.DataFrame({"Open": c, "High": c + 1.5, "Low": c - 1.5, "Close": c,
                         "Volume": 1000.0}, index=i)

_SP = {"bid": 4079.0, "ask": 4079.5, "mid": 4079.25, "src": "тест", "age_sec": 2}
_REAL = {k: getattr(lb, k) for k in ("_yf", "_rates", "_spot", "_cq_fetch", "_fng_live",
                                     "_send_raw", "_resolve", "_streaks")}

def run(force_dir, streaks):
    D = {"GC=F": _fx(800, "2024-01-01", "D", 3800, 0.35),
         "GDX": _fx(600, "2024-06-01", "D", 40, 0.02),
         "DX-Y.NYB": _fx(600, "2024-06-01", "D", 100, -0.005),
         "SI=F": _fx(900, "2026-07-20", "5min", 46.0, 0.001)}
    sent = []
    lb._yf = lambda s, period="2y", interval="1d": D.get(s, _fx(900, "2026-07-20", "5min", 4000, 0.002)).copy()
    lb._rates = lambda: pd.Series(2.0 - np.arange(600) * 0.0008,
                                  index=pd.date_range("2024-06-01", periods=600, freq="D"))
    lb._spot = lambda instr="XAU/USD", market_closed=False, cme_pause=False: _SP
    lb._cq_fetch = lambda now: None
    lb._fng_live = lambda timeout=8: None
    lb._send_raw = lambda t: (sent.append(t), "SENT (200)")[1]
    lb._resolve = lambda ls, ss, macro: (force_dir, 7, "premium", "ПРЕМИУМ")
    lb._streaks = lambda g, gd, dx, rr: dict(streaks)
    time.sleep = lambda *a, **k: None
    tmp = Path(tempfile.mkdtemp())
    old = sys.argv
    sys.argv = ["live_bot.py", "--out", str(tmp), "--stats", "backtest_stats.json",
                "--balance", "1000", "--risk", "2", "--send", "--force"]
    code = 0
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            lb.main()
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    except Exception as e:
        import traceback; traceback.print_exc()
        code = f"ГРЪМНА: {type(e).__name__}: {e}"
    finally:
        sys.argv = old
        for k, v in _REAL.items():
            setattr(lb, k, v)
    j = [json.loads(x) for x in (tmp / "live_journal.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    shutil.rmtree(tmp, ignore_errors=True)
    return code, j[0]

for d, st in (("short", {"short": 2, "long": 0}), ("short", {"short": 3, "long": 0}),
              ("short", {"short": 1, "long": 0}), ("long", {"long": 2, "short": 0})):
    code, rec = run(d, st)
    g = rec.get("gate")
    print("=" * 70)
    print(f"посока={d} streaks={st} код={code}")
    print("  dd20 в дневника:", rec.get("dd20") if "dd20" in rec else (g or {}).get("dd20"))
    if g:
        print("  gate.cell      =", g.get("cell"))
        print("  gate.streak    =", g.get("streak"))
        print("  gate.by        =", g.get("by"))
        print("  gate.ok        =", g.get("ok"))
        print("  gate.мерено    =", json.dumps(g.get("мерено"), ensure_ascii=False))
        print("  gate.why       =", g.get("why"))
        print("  gate.dd20      =", g.get("dd20"))
        м = (g.get("мерено") or {}).get("кофа")
        print("  >>> НЕСЪВПАДЕНИЕ" if (g.get("by") == "клетка" and м not in (None,) and
              м not in (g.get("cell"), "пресен ден-%s" % g.get("streak"), "mixed", "stale")) else "  >>> ок")
    else:
        print("  gate = None")
