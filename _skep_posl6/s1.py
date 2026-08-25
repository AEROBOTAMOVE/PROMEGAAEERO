import sys, io, json, urllib.request, contextlib
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import live_bot as lb
print("VERSION =", lb.VERSION)

_orig = urllib.request.urlopen

# 1) МЪРТВА МРЕЖА
def dead(*a, **k):
    raise urllib.error.URLError("нет")
urllib.request.urlopen = dead
buf = io.StringIO()
сл = []
with contextlib.redirect_stdout(buf):
    r = lb._spot("XAU/USD", реф=4639.0, следа=сл)
print("A) мъртва мрежа: върна", r, "| отпечата", repr(buf.getvalue()), "| следа =", сл)
буф2 = io.StringIO(); 
with contextlib.redirect_stdout(буф2):
    r2 = lb._spot("XAU/USD", реф=4639.0)          # БЕЗ следа = поведението ОТПРЕДИ поправката
print("A') същото БЕЗ следа (=старият код):", r2, "| отпечата", repr(буф2.getvalue()))

# 2) СМЕНЕНА СХЕМА bid/ask -> buy/sell (само swissquote жив)
import time as _t
class Fake:
    def __init__(self, body): self.body=body
    def read(self): return self.body
    def __enter__(self): return self
    def __exit__(self,*a): return False
now_ms = _t.time()*1000
схема = json.dumps([{"ts": now_ms, "spreadProfilePrices":[{"buy":4639.0,"sell":4639.5}]}]).encode()
def sxema(req, *a, **k):
    u = req.full_url if hasattr(req,"full_url") else str(req)
    if "swissquote" in u: return Fake(схема)
    raise urllib.error.URLError("резервите също са мъртви")
urllib.request.urlopen = sxema
сл2 = []
r3 = lb._spot("XAU/USD", реф=4639.0, следа=сл2)
print("B) сменена схема: върна", r3, "| следа =", сл2)

# 3) ЗАТВОРЕН ПАЗАР (уикенд) — за сравнение
urllib.request.urlopen = dead
сл3 = []
r4 = lb._spot("XAU/USD", market_closed=True, реф=4639.0, следа=сл3)
print("C) уикенд + мъртва мрежа: върна", r4, "| следа =", сл3)
сл4 = []
r5 = lb._spot("XAU/USD", cme_pause=True, реф=4639.0, следа=сл4)
print("D) CME пауза + мъртва мрежа: върна", r5, "| следа =", сл4)
urllib.request.urlopen = _orig
