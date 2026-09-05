# -*- coding: utf-8 -*-
"""mreja.py - the geometry family, enumerated in ONE place so the count that
goes into the multiple-comparison correction cannot drift away from the count
that was actually run."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import eng

LADDER = [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)]


def family():
    G = []
    def add(blok, name, *a, **k):
        g = eng.G(name, *a, **k); g["blok"] = blok; G.append(g)

    # A - една цел, БЕЗ стълба, 5 дни: целият R:R квадрат (целта по-близо от стопа и обратното)
    for sl in (10.0, 15.0, 20.0, 30.0, 40.0, 60.0):
        for tp in (5.0, 7.5, 10.0, 15.0, 20.0, 30.0, 40.0):
            add("A 1цел 5д", "TP%g SL%g 5д" % (tp, sl), [(1.0, tp)], sl, days=5)
    # B - същото, но КЪС хоризонт: 1 търговски ден
    for sl in (10.0, 20.0, 30.0, 40.0):
        for tp in (5.0, 7.5, 10.0, 15.0, 20.0):
            add("B 1цел 1д", "TP%g SL%g 1д" % (tp, sl), [(1.0, tp)], sl, days=1)
    # C - ИНТРАДЕЙ хоризонт в минути (само моят двигател може)
    for mn in (60, 120, 240, 480, 720):
        for tp, sl in ((5.0, 10.0), (5.0, 20.0), (10.0, 20.0), (10.0, 30.0), (15.0, 30.0), (20.0, 40.0)):
            add("C 1цел мин", "TP%g SL%g %dмин" % (tp, sl, mn), [(1.0, tp)], sl, minutes=mn)
    # D - стълби
    for sl in (20.0, 30.0, 40.0, 60.0):
        for dd in (1, 2, 5):
            add("D стълба", "стълба 7.5/12/20 SL%g %dд" % (sl, dd), LADDER, sl, True, days=dd)
    for sl in (20.0, 30.0):
        for dd in (1, 5):
            add("D стълба", "стълба 3/6/10 SL%g %dд" % (sl, dd), [(1/3, 3.0), (1/3, 6.0), (1/3, 10.0)], sl, True, days=dd)
            add("D стълба", "половини 5/10 SL%g %dд" % (sl, dd), [(0.5, 5.0), (0.5, 10.0)], sl, True, days=dd)
    # E - стоп на входа след МАЛКО движение в наша полза
    for bem in (2.0, 3.0, 5.0, 8.0):
        for tp, sl in ((10.0, 20.0), (20.0, 40.0)):
            for dd in (1, 5):
                add("E BE-движение", "TP%g SL%g BE@%g %dд" % (tp, sl, bem, dd), [(1.0, tp)], sl, be_move=bem, days=dd)
    # F - трал
    for tr in (3.0, 5.0, 8.0, 12.0, 20.0):
        for sl in (20.0, 40.0):
            for dd in (1, 5):
                add("F трал", "трал%g SL%g %dд (без цел)" % (tr, sl, dd), [], sl, trail=tr, days=dd)
    for tr in (5.0, 10.0):
        for tp in (15.0, 30.0):
            add("F трал", "трал%g + цел%g SL30 5д" % (tr, tp), [(1.0, tp)], 30.0, trail=tr, days=5)
    return G


if __name__ == "__main__":
    G = family()
    from collections import Counter
    print("ОБЩО ГЕОМЕТРИИ:", len(G))
    for k, v in Counter(g["blok"] for g in G).items():
        print("  %-14s %d" % (k, v))
    assert len({g["name"] for g in G}) == len(G), "дублирано име"
