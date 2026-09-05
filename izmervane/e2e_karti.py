# -*- coding: utf-8 -*-
"""ИЗЛИЗАТ ЛИ НАИСТИНА НОВИТЕ КАРТИ · истински рън на main(), край до край.

Собственикът: «НЯМА КАК ДА ТРЪГНЕ ДО ПОНЕДЕЛНИК».
Трите нови карти (обзор · седмица · календар) са тествани със СИНТЕТИЧНИ
данни, които аз съм измислил. Тук се пуска ЦЕЛИЯТ main() в понеделник сутрин
7:30 София, с реални форми на данните, и се гледа КАКВО ИЗЛИЗА В ПОЩАТА.
"""
import io, json, os, sys, shutil, tempfile, time as _t
import datetime as dt
from pathlib import Path
import numpy as np, pandas as pd

os.chdir("repo")
sys.path.insert(0, ".")
import live_bot as lb

ПРАТЕНИ = []
_РЕАЛНИ = {k: getattr(lb, k) for k in
           ("_yf", "_rates", "_spot", "_cq_fetch", "_fng_live", "_send_raw",
            "_market_closed", "_cme_pause", "_nasdaq_fetch")}


def _серия(n, старт, дрейф, стъпка="D", seed=11):
    rng = np.random.default_rng(seed)
    c = старт + np.cumsum(rng.normal(дрейф, abs(старт) * 0.004, n))
    idx = pd.date_range(end="2026-09-07", periods=n, freq=stъпка) \
        if False else pd.date_range(end="2026-09-07", periods=n, freq=стъпка)
    return pd.DataFrame({"Open": c, "High": c * 1.003, "Low": c * 0.997,
                         "Close": c, "Volume": 1000}, index=idx)


D = {"GC=F": _серия(800, 3800, 0.8),
     "GDX": _серия(600, 40, 0.02, seed=2),
     "DX-Y.NYB": _серия(600, 100, -0.005, seed=3),
     "SI=F": _серия(900, 46, 0.001, "5min", seed=4)}


def _пусни(ден_час_utc, календар=True, етикет=""):
    """Цял main() в tmp папка, без мрежа, с ЗАКОВАН часовник."""
    del ПРАТЕНИ[:]
    lb._yf = lambda s, period="2y", interval="1d": D.get(
        s, _серия(900, 4000, 0.002, "5min", seed=7)).copy()
    lb._rates = lambda: pd.Series(2.0 - np.arange(600) * 0.0008,
                                  index=pd.date_range("2024-06-01", periods=600, freq="D"))
    lb._spot = lambda instr="XAU/USD", market_closed=False, cme_pause=False, **k: \
        {"bid": 4428.0, "ask": 4430.0, "mid": 4429.0, "src": "тест"}
    lb._cq_fetch = lambda now: None
    lb._nasdaq_fetch = (lambda now, дни=None: [
        {"name": "CPI", "dt": "2026-09-07T12:30:00Z", "impact": "critical", "по": "тест"},
        {"name": "Fed Interest Rate Decision", "dt": "2026-09-16T18:00:00Z",
         "impact": "critical", "по": "тест"},
    ]) if календар else (lambda now, дни=None: [])
    lb._fng_live = lambda timeout=8: None
    lb._send_raw = lambda t: (ПРАТЕНИ.append(t), "SENT (200)")[1]
    lb._market_closed = lambda *a, **k: False
    lb._cme_pause = lambda *a, **k: False
    tmp = Path(tempfile.mkdtemp())
    старо_argv = sys.argv
    sys.argv = ["live_bot.py", "--out", str(tmp), "--send",
                "--stats", "backtest_stats.json"]
    # ботът чете часа сам; заковаваме го чрез подмяна на datetime.now в _sofia
    import datetime as _d
    _истински = lb.datetime

    class _ФиксиранЧас(_d.datetime):
        @classmethod
        def now(cls, tz=None):
            _b = _d.datetime.fromisoformat(ден_час_utc)
            return _b.replace(tzinfo=_d.timezone.utc).astimezone(tz) if tz else _b

        @classmethod
        def utcnow(cls):
            return _d.datetime.fromisoformat(ден_час_utc)

    lb.datetime = _ФиксиранЧас
    код = None
    try:
        код = lb.main()
    except SystemExit as e:
        код = e.code
    except Exception as e:
        import traceback
        код = "ГРЪМНА: %s" % traceback.format_exc().strip().splitlines()[-1]
    finally:
        lb.datetime = _истински
        sys.argv = старо_argv
        for k, v in _РЕАЛНИ.items():
            setattr(lb, k, v)
    _дн = (tmp / "live_journal.jsonl")
    зап = {}
    if _дн.exists():
        _л = [x for x in _дн.read_text(encoding="utf-8").strip().split("\n") if x.strip()]
        if _л:
            зап = json.loads(_л[-1])
    _пощ = []
    _sl = (tmp / "sent_log.jsonl")
    if _sl.exists():
        for x in _sl.read_text(encoding="utf-8").strip().split("\n"):
            if x.strip():
                _пощ.append(json.loads(x))
    shutil.rmtree(tmp, ignore_errors=True)
    return код, list(ПРАТЕНИ), зап, _пощ


print("=" * 78)
print("ИСТИНСКИ РЪН · ПОНЕДЕЛНИК 07.09, 07:30 СОФИЯ (04:30 UTC)")
print("=" * 78)
код, пратени, зап, поща = _пусни("2026-09-07T04:30:00")
print("  изходен код :", код)
print("  пратени карти:", len(пратени))
_таг = [p.get("tag") for p in поща]
print("  тагове в пощата:", _таг or "НЯМА")
print("  бележки:", len(зап.get("notes") or []))
for n in (зап.get("notes") or [])[:12]:
    print("     ·", str(n)[:92])
print()
for i, т in enumerate(пратени):
    import re
    ч = re.sub(r"</?[a-z]+>", "", str(т))
    print("  ── КАРТА %d ──" % (i + 1))
    print("   " + ч.replace("\n", "\n   ")[:600])
    print()
print("=" * 78)
print("ПРОВЕРКА")
print("=" * 78)
_текст = "\n".join(str(x) for x in пратени)
for име, знак in (("ОБЗОР на деня", "ДЕНЯТ"), ("СЕДМИЦАТА", "СЕДМИЦАТА"),
                  ("календарна", "ПАЗАРЕН ФОН")):
    print("  %-16s %s" % (име, "✔ ИЗЛЕЗЕ" if знак in _текст else "🔴 НЕ ИЗЛЕЗЕ"))
