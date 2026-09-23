# -*- coding: utf-8 -*-
"""selftest_zhivo.py — ЖИВАТА ЧАСТ на гейта (v18.89 · SELFTEST_CACHE).

🔴🔴 22.09 · ЗАЩО СЪЩЕСТВУВА ТОЗИ ФАЙЛ.
Гейтът пред всеки рън стигна 317 секунди (беше ~150), а ботът върви на 5
минути — сигналите излизаха ~5 минути късно. Целият selftest е
ДЕТЕРМИНИСТИЧЕН: същият код → същият резултат. Затова, когато ТОЧНО този код
вече е минал ЦЕЛИЯ selftest зелен (кешът в aero-bot.yml пази белег с хеша на
кода и датата), пълният тест не се пуска пак.

НО ДВЕ НЕЩА НЕ СА В ХЕША И СЕ МЕНЯТ МЕЖДУ ДВА РЪНА С ЕДИН И СЪЩ КОД:
  1) GIT — темата на последния commit. П47 сравнява VERSION с нея; тя се мени
     при всяко качване и при всеки state-комит. Тук се проверява СЪЩАТА
     аритметика през `dev_versiya.провери` (той е дословният близнак на П47 и
     се пази от П153/П158).
  2) ЧАСОВНИКЪТ — main() чете истинското време: уикенд, дневна пауза,
     празник на CME, петъчната вечер, сутрешният прозорец. Затова тук се
     пуска ЕДИН истински main() по ИСТИНСКИЯ часовник (без мрежа, без
     пращане, в своя папка) и се иска: изход 0, ред в дневника с ТЕКУЩАТА
     версия, и нито едно изключение.

Всичко останало (кодът) е проверено от ПЪЛНИЯ selftest за същия хеш.
Червен изход тук спира бота точно както червен пълен selftest: последният ред
е в същия вид («SELFTEST FAIL: …»), защото тревогата в yml чете него.

    python selftest_zhivo.py     → изход 0 (гейтът пуска) или 1 (спрян)
"""
import contextlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

ПАДНАЛИ = []
_БРОЙ = [0]


def ck(име, ок):
    ок = bool(ок)
    _БРОЙ[0] += 1
    print(("PASS" if ок else "FAIL"), "·", име)
    if not ок:
        ПАДНАЛИ.append(име)


# ── 1 · ГИТ · версията срещу последния commit (близнакът на П47) ──────
_dv = importlib.util.module_from_spec(
    importlib.util.spec_from_file_location("dev_versiya", "dev_versiya.py"))
importlib.util.spec_from_file_location("dev_versiya", "dev_versiya.py").loader.exec_module(_dv)
_код_версия = 1
try:
    with contextlib.redirect_stdout(io.StringIO()) as _из:
        _код_версия = _dv.провери("live_bot.py")
    _текст_версия = _из.getvalue().strip().replace("\n", " · ")[:160]
except Exception as _е:
    _текст_версия = "%s: %s" % (type(_е).__name__, str(_е)[:80])
# БЕЗ git (разпакетиран архив) проверката се ПРОПУСКА, не минава — дословно
# както П47 в целия selftest. Тишина тук е капанът от 05.09: единствената
# падаща проверка беше и единствената пропусната.
if _код_версия != 0 and ("БЕЗ GIT" in _текст_версия or "не мога да проверя" in _текст_версия):
    ck("ЖИВО 1 ПРОПУСНАТА, не минала — %s" % _текст_версия[:90], True)
    print("    ⚠️ ЖИВО 1: версията НЕ е сверена (няма git)")
else:
    ck("ЖИВО 1 · VERSION не изостава от последния commit (%s)" % _текст_версия,
       _код_версия == 0)

# ── 2 · ЧАСОВНИКЪТ · един истински main() СЕГА, без мрежа и без пращане ──
spec = importlib.util.spec_from_file_location("lb", "live_bot.py")
lb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lb)
ck("ЖИВО 2 · live_bot.py се внася и носи версия (%s)" % lb.VERSION,
   isinstance(lb.VERSION, str) and lb.VERSION.startswith("v"))


def _fx(n, freq, px, drift=0.0):
    """Синтетична свещна серия, която свършва СЕГА (същото като в selftest)."""
    _ед = {"D": "D", "5min": "5min", "1h": "h"}.get(freq, freq)
    кр = pd.Timestamp.utcnow().tz_localize(None).floor("min")
    нач = кр - pd.tseries.frequencies.to_offset(_ед) * (n - 1)
    и = pd.date_range(нач, periods=n, freq=_ед)
    c = px + np.arange(n) * drift + np.sin(np.arange(n) / 7.0) * 2.0
    return pd.DataFrame({"Open": c, "High": c + 1.5, "Low": c - 1.5, "Close": c,
                         "Volume": 1000.0}, index=и)


_D = {"GC=F": _fx(800, "D", 3800, 0.35), "GDX": _fx(600, "D", 40, 0.02),
      "DX-Y.NYB": _fx(600, "D", 100, -0.005), "SI=F": _fx(900, "5min", 46.0, 0.001)}
_ИНТ = _fx(900, "5min", 4000, 0.002)
_SP = {"bid": 4079.0, "ask": 4079.5, "mid": 4079.25, "src": "тест", "age_sec": 2}
_пратени = []
lb._yf = lambda s, period="2y", interval="1d": _D.get(s, _ИНТ).copy()
lb._rates = lambda: pd.Series(2.0 - np.arange(600) * 0.0008,
                              index=pd.date_range("2024-06-01", periods=600, freq="D"))
lb._spot = lambda instr="XAU/USD", market_closed=False, cme_pause=False, **к: dict(_SP)
lb._cq_fetch = lambda now: None
lb._nasdaq_fetch = lambda now, дни=None: []
lb._fng_live = lambda timeout=8: None
lb._zlaten_pyt = lambda minuti=None, notes=None: (
    pd.DataFrame({"Open": [], "High": [], "Low": [], "Close": []},
                 index=pd.DatetimeIndex([])), "проба")
lb._send_raw = lambda t, *а, **к: (_пратени.append(t), "SENT (200)")[1]
time.sleep = lambda *а, **к: None
# ЧАСОВНИКЪТ НЕ СЕ ПОДМЕНЯ — точно той е причината този файл да съществува:
# уикендът, дневната пауза, празникът на CME и петъчната вечер се съдят СЕГА.
_д = Path(tempfile.mkdtemp(prefix="zhivo_"))
_аргв = sys.argv
sys.argv = ["live_bot.py", "--out", str(_д), "--stats", "backtest_stats.json",
            "--balance", "1000", "--risk", "2", "--send"]
_код = 0
try:
    with contextlib.redirect_stdout(io.StringIO()):
        lb.main()
except SystemExit as _е:
    _код = _е.code if isinstance(_е.code, int) else 1
except Exception as _е:
    _код = "ГРЪМНА: %s: %s" % (type(_е).__name__, str(_е)[:120])
finally:
    sys.argv = _аргв
ck("ЖИВО 3 · main() по ИСТИНСКИЯ часовник минава до края (изход %s)" % _код, _код == 0)
_жф = _д / "live_journal.jsonl"
_редове = ([x for x in _жф.read_text(encoding="utf-8").splitlines() if x.strip()]
           if _жф.exists() else [])
ck("ЖИВО 4 · рънът остави ред в дневника", len(_редове) == 1)
if _редове:
    import json as _js
    _зп = _js.loads(_редове[-1])
    ck("ЖИВО 5 · редът носи ТЕКУЩАТА версия (%s)" % _зп.get("v"), _зп.get("v") == lb.VERSION)
    ck("ЖИВО 6 · редът носи час и статус",
       bool(_зп.get("run_utc")) and isinstance(_зп.get("status"), list))
shutil.rmtree(_д, ignore_errors=True)

# ── 3 · ПРИСЪДАТА · в същия вид, който тревогата в yml чете ───────────
if ПАДНАЛИ:
    print("SELFTEST FAIL:", len(ПАДНАЛИ), "от", _БРОЙ[0], "→", ПАДНАЛИ)
    sys.exit(1)
if _БРОЙ[0] < 4:
    print("SELFTEST FAIL: само %d проверки — нещо се е самоизключило" % _БРОЙ[0])
    sys.exit(1)
print("SELFTEST: ВСИЧКО ЗЕЛЕНО · %d теста (живата част; целият мина за същия код)"
      % _БРОЙ[0])
