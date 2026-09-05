# -*- coding: utf-8 -*-
"""r6_otgovor.py - четирите отговора, събрани, + готовият блок JSON.

1 · колко от ДОСТАВЕНИТЕ 6846 входа се менят (посока · клас · брой)
2 · картите при ЖИВАТА пауза (COOL_MIN=5), не само при мерената 45
3 · блокът `fresh`, готов за вграждане, в двата варианта
"""
from __future__ import annotations
import copy
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
TIER = np.array(["weak", "medium", "strong", "premium"])


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

    # ---- доставените 6846: техните чекпойнти -----------------------------
    d0, sc0, t0 = r2.resolve_tier(Z["1ден_ls"].astype(np.int16),
                                  Z["1ден_ss"].astype(np.int16), ml, живо=False)
    act0 = ok_hist & (d0 != 0) & (t0 > 0)
    k0 = ((d0 + 1) * 4 + t0).astype(np.int32)
    p0 = r2.antispam(act0, k0, np.where(d0 == 1, "long", "short"), t0, tsmin)
    p0 = p0[fill_ok[p0]]
    assert len(p0) == 6846

    дъски = {}
    for ет in ("ОБЩИ", "СВОИ", "СМЕС"):
        D, S, T, bd, bs, bt, best = r2.дъска(Z, ет, живо=True)
        дъски[ет] = (D, S, T, bd, bs, bt, best, r2.kluchove(D, T))

    лог("=" * 78)
    лог("1 · ВЪРХУ ДОСТАВЕНИТЕ 6846 ВХОДА: какво казва дъската със СВОИ линии")
    лог("=" * 78)
    for ет in ("ОБЩИ", "СВОИ", "СМЕС"):
        _, _, _, bd, bs, bt, best, _ = дъски[ет]
        нд = bd[p0]
        нт = bt[p0]
        нб = best[p0]
        смяна = int((нд != d0[p0]).sum())
        клас = int((нт != t0[p0]).sum())
        не1ден = int((нб != 6).sum())
        лог("   %-5s · посоката се мени %5d (%5.1f%%) · класът %5d (%5.1f%%) · "
            "победител ≠ «1ден» %5d (%5.1f%%)"
            % (ет, смяна, 100.0 * смяна / 6846, клас, 100.0 * клас / 6846,
               не1ден, 100.0 * не1ден / 6846))
        for стар, нов in ((1, -1), (-1, 1)):
            c = int(((d0[p0] == стар) & (нд == нов)).sum())
            лог("        %s → %s : %d" % ("лонг" if стар == 1 else "шорт",
                                          "лонг" if нов == 1 else "шорт", c))
        лог("        класове СЕГА: " + " · ".join(
            "%s %d" % (TIER[k], int((нт == k).sum())) for k in (1, 2, 3))
            + "   |   БЕЗ ръчката: " + " · ".join(
            "%s %d" % (TIER[k], int((t0[p0] == k).sum())) for k in (1, 2, 3)))

    лог("=" * 78)
    лог("2 · КАРТИТЕ при ЖИВАТА пауза COOL_MIN=%d / COOL_FLIP=%d (не мерените 45/15)"
        % (lb.COOL_MIN, lb.COOL_FLIP_MIN))
    лог("=" * 78)
    for ет in ("ОБЩИ", "СВОИ", "СМЕС"):
        _, _, _, bd, bs, bt, best, key = дъски[ет]
        act = ok_hist & (bt > 0) & (bd != 0)
        dn = np.where(bd == 1, "long", "short")
        for cool, flip, лбл in ((45, 15, "мерената 45/15"),
                                (lb.COOL_MIN, lb.COOL_FLIP_MIN, "ЖИВАТА %d/%d"
                                 % (lb.COOL_MIN, lb.COOL_FLIP_MIN))):
            pk = r2.antispam(act, key, dn, bt, tsmin, cool=cool, flip=flip)
            дни = len(np.unique(np.asarray(G["dord_entry"])[pk[fill_ok[pk]]]))
            лог("   %-5s · %-16s карти %7s · дни %4d · %5.1f карти/ден"
                % (ет, лбл, format(len(pk), ","), дни, len(pk) / max(дни, 1)))

    # ---- блокът --------------------------------------------------------
    st = json.load(io.open(REPO / "backtest_stats.json", encoding="utf-8"))
    нови = json.load(io.open(TUK / "r4_kletki.json", encoding="utf-8"))
    for ет, файл in (("СВОИ", "r6_blok_SVOI.json"), ("СМЕС", "r6_blok_SMES.json")):
        блок = {"long": {}, "short": {}}
        for dn in ("long", "short"):
            for c in ("day1", "fresh", "mixed", "stale"):
                нов = dict(нови[ет][dn][c])
                стар = st["fresh"][dn].get(c)
                if стар:
                    нов["_старо"] = {k: стар[k] for k in
                                     ("win", "net", "n", "дни", "lo", "hi") if k in стар}
                блок[dn][c] = нов
            if "ultra" in st["fresh"][dn]:
                блок[dn]["ultra"] = dict(st["fresh"][dn]["ultra"])
                блок[dn]["ultra"]["_забележка"] = (
                    "НЕ Е преизмерена - ботът не я чете (нула читатели в live_bot.py)")
        if "near_high" in нови[ет]["short"]:
            nh = dict(нови[ет]["short"]["near_high"])
            nh["_старо"] = {k: st["fresh"]["short"]["near_high"][k] for k in
                            ("win", "net", "n", "дни", "lo", "hi")}
            блок["short"]["near_high"] = nh
        io.open(TUK / файл, "w", encoding="utf-8").write(
            json.dumps({"fresh": блок}, ensure_ascii=False, indent=1))
        лог("записано %s" % файл)


if __name__ == "__main__":
    main()
