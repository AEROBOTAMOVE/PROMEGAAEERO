# -*- coding: utf-8 -*-
"""СКЕПТИК · част Г: дупката В САМАТА ПОПРАВКА, прекарана през ЖИВИЯ блок."""
import sys, os, io, json, shutil, tempfile, textwrap, contextlib, pathlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd, numpy as np, live_bot as LB
SRC = open(LB.__file__, encoding="utf-8").read().split("\n")
i0 = next(i for i,l in enumerate(SRC) if l.strip()=="_макро_мъртво = []")
i1 = next(i for i,l in enumerate(SRC) if i>i0 and l.strip()=="time.sleep(1.2)")
БЛОК = textwrap.dedent("\n".join(SRC[i0:i1+1]))
def мр(n=120):
    return pd.DataFrame({c:np.linspace(30,40,n) for c in ("Open","High","Low","Close","Volume")},
                        index=pd.date_range("2026-02-20",periods=n,freq="D"))
def _yf_г(sym,period="2y",interval="1d"):
    if sym=="DX-Y.NYB": raise RuntimeError("HTTP 429")
    return мр()
def _r(): return pd.Series(np.linspace(1.8,2.0,120), index=pd.date_range("2026-02-20",periods=120,freq="D"))
ЧАС="2026-08-20T14:00"   # сряда, среден ден, пазарът отворен
def пусни(дни):
    stamp=(pd.Timestamp(ЧАС)-pd.Timedelta(days=дни)).isoformat(timespec="minutes")
    tmp=tempfile.mkdtemp(); out=pathlib.Path(tmp); (out/"data").mkdir(parents=True,exist_ok=True)
    (out/"macro_backup.json").write_text(json.dumps(
        {"долар (DXY)":{"utc":stamp,"csv":мр().to_json(orient="split")}},ensure_ascii=False),encoding="utf-8")
    notes=[]; ns={k:getattr(LB,k) for k in dir(LB) if not k.startswith("__")}
    ns.update({"pd":pd,"np":np,"io":io,"json":json,"time":__import__("time"),"out":out,
               "now_utc":ЧАС,"notes":notes,"_yf":_yf_г,"_rates":_r,"gdx_d":None,"dxy_d":None,"rr":None})
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(БЛОК,"<блок>","exec"),ns)
    shutil.rmtree(tmp,ignore_errors=True)
    return stamp, ns["_макро_мъртво"], ns["dxy_d"] is not None, notes
print(f"часовник: {ЧАС} (сряда, пазар отворен: {not LB._market_closed(ЧАС)})   СТАР_МАКРО_Ч={LB.СТАР_МАКРО_Ч}")
print(f"{'възраст':>12} | {'резервът приет?':^16} | бележка")
print("-"*90)
for д in (1, 2, 3, 7, 13, 13.9, 14.1, 20, 60, 365):
    stamp, мъртви, взет, notes = пусни(д)
    n = notes[0] if notes else "—"
    print(f"{д:>9} дни | {('ДА' if взет else 'НЕ'):^16} | {n}")
