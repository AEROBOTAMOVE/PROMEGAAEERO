# -*- coding: utf-8 -*-
"""СКЕПТИК · част В: същото, но stdout-ът НА БЛОКА е уловен отделно (без съмнение кой какво печата)."""
import sys, os, io, json, shutil, tempfile, textwrap, contextlib, pathlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd, numpy as np
import live_bot as LB
SRC = open(LB.__file__, encoding="utf-8").read().split("\n")
i0 = next(i for i,l in enumerate(SRC) if l.strip() == "_макро_мъртво = []")
i1 = next(i for i,l in enumerate(SRC) if i>i0 and l.strip() == "time.sleep(1.2)")
БЛОК = textwrap.dedent("\n".join(SRC[i0:i1+1]))

def мокрамка(n=120):
    idx = pd.date_range("2026-02-20", periods=n, freq="D")
    return pd.DataFrame({c: np.linspace(30,40,n) for c in ("Open","High","Low","Close","Volume")}, index=idx)
def _yf_гърми(sym, period="2y", interval="1d"):
    if sym == "DX-Y.NYB": raise RuntimeError("HTTP 429 (симулиран)")
    return мокрамка()
def _rates_ок():
    return pd.Series(np.linspace(1.8,2.0,120), index=pd.date_range("2026-02-20",periods=120,freq="D"))

def пусни(stamp, часовник, етикет, стар=False):
    tmp = tempfile.mkdtemp(); out = pathlib.Path(tmp); (out/"data").mkdir(parents=True, exist_ok=True)
    (out/"macro_backup.json").write_text(json.dumps(
        {"долар (DXY)": {"utc": stamp, "csv": мокрамка().to_json(orient="split")}}, ensure_ascii=False), encoding="utf-8")
    notes=[]; блок = БЛОК.replace("if _въз_т <=","if _въз <=") if стар else БЛОК
    ns = {k:getattr(LB,k) for k in dir(LB) if not k.startswith("__")}
    ns.update({"pd":pd,"np":np,"io":io,"json":json,"time":__import__("time"),"out":out,
               "now_utc":часовник,"notes":notes,"_yf":_yf_гърми,"_rates":_rates_ок,
               "gdx_d":None,"dxy_d":None,"rr":None})
    буф = io.StringIO()
    with contextlib.redirect_stdout(буф):
        exec(compile(блок,"<блок>","exec"), ns)
    print(f"\n{'='*70}\n{етикет}")
    print(f"  _макро_мъртво = {ns['_макро_мъртво']}   ·  dxy_d получен: {ns['dxy_d'] is not None}")
    print(f"  notes  : {notes}")
    print(f"  печат на блока: {буф.getvalue().strip() or '(нищо)'}")
    shutil.rmtree(tmp, ignore_errors=True)

пусни("2026-08-14T20:56","2026-08-16T22:02","А · ЖИВИЯТ v14.2 · истинската уикендна дупка 49.10ч")
пусни("2026-08-14T20:56","2026-08-16T22:02","Б · КОДЪТ ОТПРЕДИ v14.0 · същите числа", стар=True)
пусни("2026-08-19T06:00","2026-08-20T22:00","В · КОНТРОЛА · 40ч ЖИВ застой (пазачът трябва да реже)")

print("\n\n########## СКЕПТИКЪТ ОБРЪЩА ОРЪДИЕТО КЪМ САМАТА ПОПРАВКА ##########")
for д, ет in ((5,"5 дни"),(13,"13 дни"),(14.5,"14.5 дни · ОТВЪД абсурдния праг"),(60,"60 дни")):
    stamp = (pd.Timestamp("2026-08-16T22:02") - pd.Timedelta(days=д)).isoformat()
    tm = LB._търговски_минути(stamp, "2026-08-16T22:02")/60.0
    print(f"  резерв на {д:>5} дни ({ет:<32}) → търговска възраст {tm:8.2f}ч → приема ли се? {tm <= LB.СТАР_МАКРО_Ч}")
