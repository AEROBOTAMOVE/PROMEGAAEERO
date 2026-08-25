# -*- coding: utf-8 -*-
"""Пуска ИСТИНСКИЯ main() с ЗАМРАЗЕН часовник и СЧУПЕН само DX-Y.NYB.
Спира се точно СЛЕД макро-блока (патчнат _regime хвърля сигнал) и чете
локалните променливи на main() от траса — без да пипа кода."""
import sys, io, json, importlib.util, pathlib, datetime as _dt
import pandas as pd

MOD, OUT, ZAMR = sys.argv[1], sys.argv[2], sys.argv[3]      # напр. lb_star.py B_star/live 2026-08-16T22:11
HERE = pathlib.Path(__file__).parent
FROZEN = _dt.datetime.fromisoformat(ZAMR).replace(tzinfo=_dt.timezone.utc)

spec = importlib.util.spec_from_file_location(pathlib.Path(MOD).stem, HERE / MOD)
lb = importlib.util.module_from_spec(spec); sys.modules[spec.name] = lb
sys.argv = ["x", "--out", OUT]
spec.loader.exec_module(lb)

class _FakeDT(_dt.datetime):
    @classmethod
    def now(cls, tz=None):
        return FROZEN if tz else FROZEN.replace(tzinfo=None)
    @classmethod
    def utcnow(cls): return FROZEN.replace(tzinfo=None)
lb.datetime = _FakeDT

_бек = json.loads((HERE / OUT / "macro_backup.json").read_text(encoding="utf-8"))
def _рамка(ключ):
    d = pd.read_json(io.StringIO(_бек[ключ]["csv"]), orient="split")
    d.index = pd.to_datetime(d.index)
    return d
GDX = _рамка("миньори (GDX)")
ЗЛАТО = _рамка("миньори (GDX)").copy() * 40.0          # само за да не гръмне — макрото не зависи от него

_повиквания = []
def _yf_fake(sym, period="2y", interval="1d"):
    _повиквания.append((sym, interval))
    if sym == "DX-Y.NYB":
        raise RuntimeError("празни данни (Yahoo хълца)")
    if sym == "GC=F" and interval == "1d":
        return ЗЛАТО.copy()
    if sym == "GDX":
        return GDX.copy()
    raise RuntimeError(f"нямам мок за {sym}/{interval}")
lb._yf = _yf_fake
def _rates_fake():
    d = _рамка("лихви (FRED)")
    return d["rate"] if "rate" in d else d.iloc[:, 0]
lb._rates = _rates_fake

class СТОП(Exception): pass
def _regime_stop(*a, **k): raise СТОП()
lb._regime = _regime_stop

print("МОДУЛ:", MOD, "| замразен час UTC:", FROZEN.isoformat())
print("пазарът затворен ли е?", lb._market_closed(FROZEN.replace(tzinfo=None).isoformat(timespec='minutes')))
print("СТАР_МАКРО_Ч =", lb.СТАР_МАКРО_Ч)
_p = _бек["долар (DXY)"]["utc"]; _n = FROZEN.replace(tzinfo=None).isoformat(timespec='minutes')
print("печат на резерва:", _p)
print("СТЕННА възраст, ч:", round((pd.Timestamp(_n)-pd.Timestamp(_p)).total_seconds()/3600, 2))
print("ТЪРГОВСКА възраст, ч:", round(lb._търговски_минути(_p, _n)/60.0, 2))
print("-"*70)
try:
    lb.main()
    print("main() ИЗЛЕЗЕ БЕЗ да стигне _regime — виж дали е уикенд-клон")
except СТОП:
    tb = sys.exc_info()[2]
    рамки = []
    while tb: рамки.append(tb.tb_frame); tb = tb.tb_next
    m = [f for f in рамки if f.f_code.co_name == "main"][0]
    L = m.f_locals
    print("_макро_мъртво:", L.get("_макро_мъртво"))
    print("macro:", L.get("macro"))
    print("macro_health:", L.get("macro_health"))
    print("dxy_d е None?", L.get("dxy_d") is None)
    print("бележки:")
    for n in L.get("notes", []): print("   -", n)
