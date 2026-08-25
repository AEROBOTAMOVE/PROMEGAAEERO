# -*- coding: utf-8 -*-
"""Точно проверката на П18 (част 2), но с ЖИВИЯ stats и dd20 подаден — както прави main()."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.argv = ["x"]
import live_bot as lb
BS = json.load(open('backtest_stats.json', encoding='utf-8'))
КОФА_НА_КЛЕТКА = {"day1": "пресен ден-1", "fresh": "пресен ден-{s}", "mixed": "mixed", "stale": "stale"}
print("%-6s %-3s %-8s %-9s %-14s %-6s %s" % ("dir", "s", "cell", "dd20", "мерено.кофа", "by", "ok"))
for d in ("long", "short"):
    for s in (0, 1, 2, 3, 4, 5):
        for dd in (None, 0.001, 0.02):
            tr = {}
            txt, ok = lb._advice_entry(d, s, BS, None, False, 0, sym="XAUUSD", dd20=dd, trace=tr)
            cell = lb._cell_name(s)
            м = (tr.get("мерено") or {})
            бележка = ""
            if tr.get("by") == "клетка" and м.get("net") is not None:
                # кое нето БИ важало според cell?
                fr = BS["fresh"][d]
                очаквано = (fr.get("day1") if s == 1 else fr.get("fresh") if 2 <= s <= 3
                            else fr.get("mixed") if s == 0 else fr.get("stale")) or {}
                if abs(float(м["net"]) - float(очаквано.get("net", -999))) > 1e-9:
                    бележка = "  <<< П18 БИ ПАДНАЛ: съди по %.2f, а cell «%s» е %.2f" % (
                        м["net"], cell, очаквано.get("net", float("nan")))
            print("%-6s %-3s %-8s %-9s %-14s %-6s %-5s%s" % (
                d, s, cell, dd, м.get("кофа"), tr.get("by"), ok, бележка))
