# -*- coding: utf-8 -*-
"""adv3_tavan_den.py — ВРАТАТА, КОЯТО mer.py И mer_gejt.py НЕ МОДЕЛИРАТ.

live_bot.py:8162-8171 · ТАВАН_ВХОД_ДЕН (yml -> vars.MAX_ENTRIES_DAY):
    има ли вече N отворени входа ДНЕС -> _adv_ok = False -> сделка НЕ се отваря.
Нито potok.пробег, нито гейтът в mer_gejt.направи_гейт го имат
(той е в live_bot.main(), НЕ в _advice_entry).

Тук пробегът е копие на potok.пробег с ЕДНО добавено звено: ТАВАН НА
ВХОДОВЕТЕ ЗА ТЪРГОВСКИ ДЕН. Всичко останало е дословно същото.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

ТУК = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУК))
import jiv                                                        # noqa: E402
import potok                                                      # noqa: E402
import mer                                                        # noqa: E402

REPS = 5000
SEED = 20260905


def пробег_с_дневен_таван(D, B, cfg, геом_fn, таван_ден=0):
    """potok.пробег + ТАВАН_ВХОД_ДЕН. таван_ден<=0 -> изключен (= potok.пробег)."""
    n = D["n"]
    tsmin = D["tsmin"]; act = D["act"]
    dname = D["dname"]; tname = D["tname"]; tier = D["tier"]
    fill_ok = D["fill_ok"]; bidx = D["bar_index"]
    pxl = D["px_long"]; pxs = D["px_short"]; sof = D["sofia_h"]
    stl = D["streak_long"]; sts = D["streak_short"]; dord = D["dord"]

    cool_min = cfg["cool_min"]; cool_flip = cfg["cool_flip"]
    cap = cfg["cap"] if cfg["cap"] else 10 ** 9
    guard_on = cfg["guard"]; guard_h = cfg["guard_h"]; guard_st = cfg["guard_stops"]

    last_key = ""; last_dir = ""; last_tier = 0
    last_sent = None; key_since = None
    отворени = []
    guard_t = {"long": None, "short": None}
    guard_n = {"long": 0, "short": 0}
    вх_ден = {}
    карти = 0; карти_reoffer = 0
    сп_таван = 0; сп_пазач = 0; сп_ден = 0
    сделки = []

    for i in range(n):
        t = tsmin[i]
        if отворени:
            ост = []
            for ex_t, dr, ист in отворени:
                if ex_t <= t:
                    if ист:
                        guard_n[dr] += 1
                        guard_t[dr] = ex_t
                else:
                    ост.append((ex_t, dr, ист))
            отворени = ост
        if not act[i]:
            last_key = ""
            continue
        dr = dname[i]; tr = int(tier[i]); k = dr + ":" + tname[i]
        mins = None if last_sent is None else (t - last_sent)
        tier_up = (tr > last_tier) and (dr == last_dir)
        cool_ok = (mins is None or mins >= cool_min
                   or (dr != last_dir and mins >= cool_flip) or tier_up)
        слот = len(отворени) < cap
        streak = int(stl[i] if dr == "long" else sts[i])
        reoffer = False
        if cfg["reoffer"]:
            key_age_h = ((t - key_since) / 60.0
                         if (last_key == k and key_since is not None) else None)
            reoffer = (слот and tr >= cfg["reoffer_tier"] and mins is not None
                       and mins >= potok._праг_ч(cfg, dr, streak) * 60
                       and key_age_h is not None
                       and key_age_h <= potok._таван_ч(cfg, dr, streak)
                       and cfg["reoffer_lo"] <= int(sof[i]) <= cfg["reoffer_hi"])
        should = (last_key != k or tier_up or reoffer) and cool_ok
        if not should:
            continue
        карти += 1
        if reoffer and last_key == k:
            врата = "РЕ-ОФЕР"
            карти_reoffer += 1
        elif tier_up and last_key == k:
            врата = "TIER_UP"
        else:
            врата = "нов ключ"
        key_since = key_since if (last_key == k and key_since is not None) else t
        last_key, last_dir, last_tier, last_sent = k, dr, tr, t

        if guard_on:
            gt = guard_t[dr]
            n_g = guard_n[dr] if (gt is not None and 0 <= (t - gt) / 60.0 < guard_h) else 0
            if n_g >= guard_st:
                сп_пазач += 1
                continue
        # --- НОВОТО ЗВЕНО: ТАВАН_ВХОД_ДЕН (live_bot.py:8162) ---
        д = int(dord[i])
        if таван_ден > 0 and вх_ден.get(д, 0) >= таван_ден:
            сп_ден += 1
            continue
        if not слот:
            сп_таван += 1
            continue
        if not fill_ok[i]:
            continue
        i0 = int(bidx[i])
        px = float(pxl[i] if dr == "long" else pxs[i])
        r = jiv.бързо(i0, dr, px, геом_fn(dr), B)
        if r is None:
            continue
        ист_стоп = (r["kind"] == "stop" and abs(r["gross"]) > 0.05)
        отворени.append((int(B["tsmin"][r["exit_index"]]), dr, ист_стоп))
        вх_ден[д] = вх_ден.get(д, 0) + 1
        сделки.append((i, i0, dr, px, r["net"], r["kind"], д,
                       r["n_fills"], r["net_per_fill"], врата, streak))
    return dict(карти=карти, карти_reoffer=карти_reoffer, сп_таван=сп_таван,
                сп_пазач=сп_пазач, сп_ден=сп_ден, сделки=сделки)


def main():
    B = jiv.лента(); G = jiv.решетка(); D = potok.подготви(G)
    брой_дни = int(B["dord"][-1]) + 1
    години = (B["tsmin"][-1] - B["tsmin"][0]) / (60 * 24 * 365.25)
    ЖИВ = potok.жива_настройка()
    С0 = dict(potok.СТАР)
    С6 = dict(С0, cap=ЖИВ["cap"], guard=True, guard_h=ЖИВ["guard_h"],
              guard_stops=ЖИВ["guard_stops"], cool_min=ЖИВ["cool_min"],
              cool_flip=ЖИВ["cool_flip"], reoffer=True,
              reoffer_h=ЖИВ["reoffer_h"], reoffer_h_fresh=ЖИВ["reoffer_h_fresh"],
              max_age=ЖИВ["max_age"], max_age_fresh=ЖИВ["max_age_fresh"],
              reoffer_lo=ЖИВ["reoffer_lo"], reoffer_hi=ЖИВ["reoffer_hi"],
              reoffer_tier=ЖИВ["reoffer_tier"])

    r0 = пробег_с_дневен_таван(D, B, С0, mer.геом_доставена, 0)
    v0 = mer.по_дни(r0["сделки"], брой_дни)
    print("\nСВЕРКА: стъпало 0 = %d сделки (mer.py дава 6846)" % len(r0["сделки"]))

    rb = пробег_с_дневен_таван(D, B, С6, mer.геом_жива, 0)
    print("СВЕРКА: стъпало 6 = %d сделки (mer.py дава 22099)" % len(rb["сделки"]))
    dd = np.array([x[6] for x in rb["сделки"]])
    _, cnt = np.unique(dd, return_counts=True)
    print("\nВХОДОВЕ НА ТЪРГОВСКИ ДЕН в ЖИВИЯ УРЕД на mer.py:")
    print("  дни със сделки %d | медиана %.0f | средно %.2f | 90-и %.0f | максимум %d"
          % (len(cnt), np.median(cnt), cnt.mean(), np.percentile(cnt, 90), cnt.max()))
    for пр in (1, 2, 3, 5, 12):
        print("    дни с над %2d входа: %5d (%4.1f%%) | сделки над квотата: %6d (%4.1f%% от всички)"
              % (пр, int((cnt > пр).sum()), 100.0 * (cnt > пр).mean(),
                 int(np.clip(cnt - пр, 0, None).sum()),
                 100.0 * np.clip(cnt - пр, 0, None).sum() / len(dd)))

    print("\n" + "=" * 122)
    print("ЖИВИЯТ УРЕД ПРИ ЖИВИЯ ДНЕВЕН ТАВАН | всичко останало е дословно същото")
    print("=" * 122)
    for тд in (0, 5, 3, 2, 1):
        r = пробег_с_дневен_таван(D, B, С6, mer.геом_жива, тд)
        net = np.array([x[4] for x in r["сделки"]])
        d6 = np.array([x[6] for x in r["сделки"]])
        m, lo, hi, дни = jiv.бутстрап_по_ден(net, d6, REPS, SEED)
        v6 = mer.по_дни(r["сделки"], брой_дни)
        dv = v6 - v0
        жив = np.nonzero(np.abs(v0) + np.abs(v6) > 0)[0]
        dm, dlo, dhi, dд = jiv.бутстрап_по_ден(dv[жив], жив, REPS, SEED)
        print("  ТАВАН_ВХОД_ДЕН=%-8s n=%6d  $/сделка %+.3f  общо %+8.1f$  /год %+8.2f$"
              "  ||  Δ спрямо СТАРИЯ: %+.3f$/ден [%+.3f..%+.3f] %s  Δ/год %+8.2f$"
              % (("изключен" if тд == 0 else str(тд)), len(net), m, net.sum(),
                 net.sum() / години, dm, dlo, dhi, jiv.присъда(dlo, dhi, dд),
                 dv.sum() / години))


if __name__ == "__main__":
    main()
