# -*- coding: utf-8 -*-
"""r3_neta.py - нетото на ВСЕКИ вход от двата режима, с ЖИВАТА геометрия.

ЛОНГ  ТП 75/120/200 пипса (7.5/12/20$) · стоп 130п (13$) · по 1/3 · БЕ след ТП1
ШОРТ  ТП 50/100/200 пипса (5/10/20$)  · стоп 130п (13$) · ½¼¼   · БЕ след ТП1
Хоризонт 21 ТЪРГОВСКИ дни (= ДНИ_МАКС 30 календарни, live_bot).
Двигателят е dvig.една - сверен ред по ред с gh._one_trade (0 разминавания).

СВЕРКА С3: същият двигател, същата ГЕОМЕТРИЯ на geom_harness (7.5/12/20 ст20,
5 дни), пуснат върху доставените входове, трябва да върне числата на
gh._one_trade - проверява се на 300 случайни входа тук, наново.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path
import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
for p in (str(IZM / "mer_mnozhitelite"), str(IZM), str(REPO)):
    sys.path.insert(0, p)
import dvig                                                          # noqa: E402
import live_bot as lb                                                # noqa: E402

T0 = time.time()
ДНИ = 21
Г_ЛОНГ = {"name": "жива лонг", "tps": [(1 / 3, 7.5), (1 / 3, 12.0), (1 / 3, 20.0)],
          "sl": 13.0, "be_after_tp1": True, "days": ДНИ}
Г_ШОРТ = {"name": "жива шорт", "tps": [(0.5, 5.0), (0.25, 10.0), (0.25, 20.0)],
          "sl": 13.0, "be_after_tp1": True, "days": ДНИ}
KMAP = {"stop": 1, "tp3": 3, "time": 4}


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


def проверка_геометрия():
    """Геометрията ТУК срещу живия live_bot._геом - не срещу паметта ми."""
    ntp, sl, дял = lb._геом("long")
    assert tuple(ntp) == (7.5, 12.0, 20.0) and abs(sl - 13.0) < 1e-9, (ntp, sl)
    assert abs(дял[0] - 1 / 3) < 1e-9
    ntp, sl, дял = lb._геом("short")
    assert tuple(ntp) == (5.0, 10.0, 20.0) and abs(sl - 13.0) < 1e-9, (ntp, sl)
    assert tuple(дял) == (0.5, 0.25, 0.25)
    лог("геометрията е прочетена от живия live_bot._геом ✅")


def сверка(B, seed=11, k=300):
    # pyarrow е блокиран от Windows App Control в тази среда (виж pq_lite.py).
    # geom_harness го иска само за ЧЕТЕНЕ на лентата; `_one_trade` не го пипа.
    # Затова се внася празна кукла - функцията, която сверявам, остава ОРИГИНАЛНАТА.
    import types
    if "pyarrow" not in sys.modules:
        pa = types.ModuleType("pyarrow")
        paq = types.ModuleType("pyarrow.parquet")
        pa.parquet = paq
        sys.modules["pyarrow"] = pa
        sys.modules["pyarrow.parquet"] = paq
    import geom_harness as gh
    E = np.load(TUK / "r2_vhodove.npz")
    idx = E["ОБЩИ_bar"][:k]
    d = E["ОБЩИ_dir"][:k]
    px = E["ОБЩИ_px"][:k]
    rng = np.random.default_rng(seed)
    sel = rng.permutation(len(idx))[:k]
    лош = 0
    for p in sel:
        dd = "long" if d[p] == 1 else "short"
        a = dvig.една(int(idx[p]), dd, float(px[p]), dvig.GEOM, B)
        b = gh._one_trade(int(idx[p]), dd, float(px[p]), gh.GEOM_SHIPPED, B)
        if (a is None) != (b is None):
            лош += 1
            continue
        if a is None:
            continue
        if abs(a["net"] - b["net"]) > 1e-9 or a["kind"] != b["kind"]:
            лош += 1
    лог("С3 · dvig срещу gh._one_trade на %d входа: %d разминавания" % (len(sel), лош))
    assert лош == 0


def бяг(idxs, dirs, pxs, B):
    n = len(idxs)
    net = np.full(n, np.nan)
    exi = np.full(n, -1, np.int64)
    kind = np.zeros(n, np.int8)
    t = time.time()
    for p in range(n):
        dd = "long" if dirs[p] == 1 else "short"
        r = dvig.една(int(idxs[p]), dd, float(pxs[p]),
                      Г_ЛОНГ if dd == "long" else Г_ШОРТ, B)
        if r is not None:
            net[p] = r["net"]
            exi[p] = r["exit_index"]
            k = r["kind"]
            kind[p] = KMAP.get(k, 2 if k.startswith(("be-stop", "stop-after")) else 4)
        if p and p % 20000 == 0:
            лог("   %s / %s (%.0fs)" % (format(p, ","), format(n, ","), time.time() - t))
    return net, exi, kind


def main():
    проверка_геометрия()
    B = dvig.лента()
    сверка(B)
    E = np.load(TUK / "r2_vhodove.npz")
    out = {}
    for етикет in ("ОБЩИ", "СВОИ", "СМЕС"):
        idxs = E[етикет + "_bar"]
        dirs = E[етикет + "_dir"]
        pxs = E[етикет + "_px"]
        лог("%s · смятам %s сделки" % (етикет, format(len(idxs), ",")))
        net, exi, kind = бяг(idxs, dirs, pxs, B)
        out[етикет + "_net"] = net
        out[етикет + "_exi"] = exi
        out[етикет + "_kind"] = kind
        out[етикет + "_exts"] = np.where(exi >= 0, B["tsmin"][np.clip(exi, 0, len(B["tsmin"]) - 1)],
                                         np.iinfo(np.int64).max)
        лог("   с нето %s · средно %.4f$" % (format(int(np.isfinite(net).sum()), ","),
                                             np.nanmean(net)))
    np.savez_compressed(TUK / "r3_neta.npz", **out)
    лог("записано r3_neta.npz")


if __name__ == "__main__":
    main()
