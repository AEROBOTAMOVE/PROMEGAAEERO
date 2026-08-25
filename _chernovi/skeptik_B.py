# -*- coding: utf-8 -*-
"""СКЕПТИК · част Б: ИЗПЪЛНЯВАМ САМИЯ БЛОК от живия live_bot.py (нищо не преписвам).
Изрязвам редовете на макро-цикъла ДОСЛОВНО от файла и ги пускам с фиксиран часовник."""
import sys, os, io, json, types, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd, numpy as np
import live_bot as LB

SRC = open(LB.__file__, encoding="utf-8").read().split("\n")

# --- намирам блока по МАРКЕРИ, не по твърди номера ---
i0 = next(i for i,l in enumerate(SRC) if l.strip() == "_макро_мъртво = []")
i1 = next(i for i,l in enumerate(SRC) if i>i0 and l.strip() == "time.sleep(1.2)")
БЛОК = "\n".join(SRC[i0:i1+1])
print(f"изрязах редове {i0+1}..{i1+1} от {LB.__file__}")
print(f"проверка че вътре Е решаващият ред: "
      f"{[l.strip() for l in SRC[i0:i1+1] if 'СТАР_МАКРО_Ч' in l]}")
import textwrap
БЛОК = textwrap.dedent(БЛОК)

# --- фалшив _yf: гърми САМО за DXY, за другите връща истинска рамка ---
def мокрамка(n=120, кол=("Open","High","Low","Close","Volume")):
    idx = pd.date_range("2026-02-20", periods=n, freq="D")
    return pd.DataFrame({c: np.linspace(30, 40, n) for c in кол}, index=idx)

def _yf_гърми(sym, period="2y", interval="1d"):
    if sym == "DX-Y.NYB":
        raise RuntimeError("HTTP 429 от Yahoo (симулиран хълцук)")
    return мокрамка()

def _rates_ок():
    idx = pd.date_range("2026-02-20", periods=120, freq="D")
    return pd.Series(np.linspace(1.8, 2.0, 120), index=idx)

def пусни(петък_stamp, часовник, етикет, стар_режим=False):
    tmp = tempfile.mkdtemp(prefix="skeptik_")
    out = __import__("pathlib").Path(tmp); (out/"data").mkdir(parents=True, exist_ok=True)
    # резервът се записва ТОЧНО както го пише самият live_bot (ред с _бек[_име] = ...)
    рамка = мокрамка()
    (out/"macro_backup.json").write_text(json.dumps(
        {"долар (DXY)": {"utc": петък_stamp, "csv": рамка.to_json(orient="split")}},
        ensure_ascii=False), encoding="utf-8")
    notes = []
    ns = {k: getattr(LB, k) for k in dir(LB) if not k.startswith("__")}
    блок = БЛОК
    if стар_режим:                       # версията ОТПРЕДИ v14.0, дословно от git
        блок = блок.replace("if _въз_т <= СТАР_МАКРО_Ч", "if _въз <= СТАР_МАКРО_Ч")
    ns.update({"pd": pd, "np": np, "io": io, "json": json, "time": __import__("time"),
               "out": out, "now_utc": часовник, "notes": notes,
               "_yf": _yf_гърми, "_rates": _rates_ок,
               "gdx_d": None, "dxy_d": None, "rr": None,
               "_load_state": LB._load_state, "_търговски_минути": LB._търговски_минути,
               "СТАР_МАКРО_Ч": LB.СТАР_МАКРО_Ч})
    exec(compile(блок, "<блок от live_bot.py>", "exec"), ns)
    мъртви = ns["_макро_мъртво"]
    print(f"\n{'='*74}\n{етикет}")
    print(f"  резерв от : {петък_stamp}   часовник: {часовник}")
    print(f"  стенна възраст  : {(pd.Timestamp(часовник)-pd.Timestamp(петък_stamp)).total_seconds()/3600:.2f}ч")
    print(f"  търговска възр. : {LB._търговски_минути(петък_stamp, часовник)/60.0:.2f}ч")
    print(f"  _макро_мъртво   : {мъртви}")
    print(f"  dxy_d взет ли е : {ns['dxy_d'] is not None}")
    for n in notes: print("    ·", n)
    shutil.rmtree(tmp, ignore_errors=True)
    return мъртви

ПЕТЪК = "2026-08-14T20:56"      # ИСТИНСКИЯТ последен петъчен рън (от живия журнал)
НЕДЕЛЯ = "2026-08-16T22:02"     # ИСТИНСКИЯТ първи рън след уикенда
print("пазарът затворен ли е в", НЕДЕЛЯ, "?", LB._market_closed(НЕДЕЛЯ))

a = пусни(ПЕТЪК, НЕДЕЛЯ, "А · ЖИВИЯТ КОД (v14.2) · петък→неделя, 49.1ч")
b = пусни(ПЕТЪК, НЕДЕЛЯ, "Б · СТАРИЯТ КОД (преди v14.0) · същите числа", стар_режим=True)
c = пусни("2026-08-19T06:00", "2026-08-20T22:00", "В · КОНТРОЛА: 40ч ЖИВ застой сред седмицата (пазачът пак ли реже?)")
