# -*- coding: utf-8 -*-
"""r7_kontrol.py - последните проверки, преди числата да се цитират.

К1 · ЧИСТИЯТ ефект на ръчката върху ДОСТАВЕНИТЕ 6846: ОБЩИ срещу СВОИ
     (една и съща `_resolve`/`_tier`, мени се САМО откъде идват линиите)
К2 · какво КАЗВА живият гейт на всяка клетка ДНЕС - изпълнена функция, не памет
К3 · разпределение на точките (score) по режим - откъде идва ПРЕМИУМ
"""
from __future__ import annotations
import io
import json
import sys
import time
from pathlib import Path
import numpy as np

TUK = Path(__file__).resolve().parent
IZM = TUK.parent
REPO = IZM.parent
KONV = IZM / "mer_celiyat-konveyer"
for p in (str(KONV), str(IZM / "mer_mnozhitelite"), str(IZM), str(REPO)):
    sys.path.insert(0, p)
import pq_lite as pl                                                 # noqa: E402
import live_bot as lb                                                # noqa: E402
import r2_vhodove as r2                                              # noqa: E402

T0 = time.time()


def лог(*a):
    print("[%7.1fs]" % (time.time() - T0), *a, flush=True)


def main():
    Z = dict(np.load(TUK / "r1_ramki.npz"))
    G = pl.read_columns(KONV / "reshetka.parquet")
    G.pop("__meta__", None)
    tsmin = G["ts"] // 60_000_000
    ok_hist = np.asarray(G["ok_hist"])
    fill_ok = np.asarray(G["fill_ok"])
    ml = Z["ml"].astype(np.int16)
    d0, sc0, t0 = r2.resolve_tier(Z["1ден_ls"].astype(np.int16),
                                  Z["1ден_ss"].astype(np.int16), ml, живо=False)
    act0 = ok_hist & (d0 != 0) & (t0 > 0)
    p0 = r2.antispam(act0, ((d0 + 1) * 4 + t0).astype(np.int32),
                     np.where(d0 == 1, "long", "short"), t0, tsmin)
    p0 = p0[fill_ok[p0]]
    Дб = {}
    for ет in ("ОБЩИ", "СВОИ", "СМЕС"):
        Дб[ет] = r2.дъска(Z, ет, живо=True)
    лог("К1 · ЧИСТИЯТ ефект на РАМКИ_СВОИ_ЛИНИИ (една и съща _resolve/_tier)")
    for ет in ("СВОИ", "СМЕС"):
        a = Дб["ОБЩИ"]
        b = Дб[ет]
        for име, маска, N in (("доставените 6846 входа", p0, len(p0)),
                              ("ВСИЧКИ чекпойнти с история", np.flatnonzero(ok_hist),
                               int(ok_hist.sum()))):
            пос = int((a[3][маска] != b[3][маска]).sum())
            кл = int((a[5][маска] != b[5][маска]).sum())
            рм = int((a[6][маска] != b[6][маска]).sum())
            лг = int(((a[3][маска] == 1) & (b[3][маска] == -1)).sum())
            шл = int(((a[3][маска] == -1) & (b[3][маска] == 1)).sum())
            лог("   ОБЩИ→%-5s · %-26s посока %6d (%5.1f%%)  [лонг→шорт %5d · шорт→лонг %5d]"
                "  клас %6d (%5.1f%%)  рамка %6d (%5.1f%%)"
                % (ет, име, пос, 100.0 * пос / N, лг, шл, кл, 100.0 * кл / N,
                   рм, 100.0 * рм / N))

    лог("К2 · ЖИВИЯТ гейт, ИЗПЪЛНЕН върху всяка клетка (доставени клетки)")
    st = json.load(io.open(REPO / "backtest_stats.json", encoding="utf-8"))
    for стрийк, кофа in ((1, "day1"), (2, "fresh"), (0, "mixed"), (5, "stale")):
        for dn in ("long", "short"):
            txt, ok = lb._advice_entry(dn, стрийк, st, None, False, 0, sym="XAUUSD",
                                       stale_price=False, dd20=None)
            seg = st["fresh"][dn].get(кофа, {})
            лог("   %-5s %-6s (n=%-5s дни=%-4s нето=%+.3f [%+.3f,%+.3f]) → %s | %s"
                % (dn, кофа, seg.get("n"), seg.get("дни"), seg.get("net", 0),
                   seg.get("lo", 0), seg.get("hi", 0), "ПУСКА" if ok else "РЕЖЕ",
                   txt[:58]))

    лог("К3 · разпределение на ТОЧКИТЕ на победителя (само ok_hist)")
    for ет in ("ОБЩИ", "СВОИ", "СМЕС"):
        bs = Дб[ет][4][ok_hist]
        bt = Дб[ет][5][ok_hist]
        ред = " · ".join("%d:%4.1f%%" % (v, 100.0 * (bs == v).mean())
                         for v in range(3, 9))
        лог("   %-5s точки %s | премиум %.1f%%" % (ет, ред, 100.0 * (bt == 3).mean()))


if __name__ == "__main__":
    main()
