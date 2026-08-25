# -*- coding: utf-8 -*-
"""СКЕПТИК · възпроизвеждане на находката за _spot."""
import sys, io, json, time, importlib.util, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import importlib.util as _iu
_sp=_iu.spec_from_file_location('lb137', r'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/_skep_posl_token/lb137.py')
LB=_iu.module_from_spec(_sp); _sp.loader.exec_module(LB)
print("VERSION в ЖИВИЯ файл =", LB.VERSION)
print("файл:", LB.__file__)

class _Resp:
    def __init__(self, payload): self._p = payload.encode()
    def read(self): return self._p
    def __enter__(self): return self
    def __exit__(self, *a): return False

_ORIG = urllib.request.urlopen

def mk(handler):
    def fake(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        return handler(url)
    return fake

now_ms = time.time()*1000
SWQ_OK = json.dumps([{"ts": now_ms, "spreadProfilePrices":[{"bid":4638.10,"ask":4638.60}]}])
SWQ_NEW_SCHEMA = json.dumps([{"ts": now_ms, "spreadProfilePrices":[{"buy":4638.10,"sell":4638.60}]}])
CB_OK = json.dumps({"bid":"4641.20","ask":"4641.80"})

def h_dead(url): raise OSError("мрежата е мъртва")
def h_schema_swq_only(url):
    if "swissquote" in url: return _Resp(SWQ_NEW_SCHEMA)
    if "binance"    in url: raise urllib.error.HTTPError(url,451,"Unavailable For Legal Reasons",None,None)
    if "coinbase"   in url: return _Resp(CB_OK)
    raise OSError("kraken")
def h_schema_all_dead(url):
    if "swissquote" in url: return _Resp(SWQ_NEW_SCHEMA)
    raise OSError("резервите също мълчат")

def пусни(име, handler, следа):
    urllib.request.urlopen = mk(handler)
    буф = io.StringIO(); стар = sys.stdout; sys.stdout = буф
    изкл = None
    try:
        r = LB._spot("XAU/USD", market_closed=False, cme_pause=False)
    except Exception as e:
        r = "ИЗКЛЮЧЕНИЕ"; изкл = repr(e)
    finally:
        sys.stdout = стар; urllib.request.urlopen = _ORIG
    print(f"\n--- {име} ---")
    print("  върна           :", r)
    print("  отпечата        :", repr(буф.getvalue()))
    print("  вдигна изключение:", изкл or "НЕ")
    print("  следа           :", следа)
    return r

пусни("A. мъртва мрежа, БЕЗ следа (=поведението на v13.7)", h_dead, None)
пусни("B. мъртва мрежа, СЪС следа (v14.2)", h_dead, [])
пусни("C. СМЕНЕНА СХЕМА само в Swissquote, резервите ЖИВИ", h_schema_swq_only, [])
пусни("D. СМЕНЕНА СХЕМА + всички резерви мъртви", h_schema_all_dead, [])
