# -*- coding: utf-8 -*-
"""jiv.py — УРЕДЪТ, КОЙТО МЕРИ ЖИВИЯ БОТ.

ЗАЩО СЪЩЕСТВУВА
    `geom_harness.py` мери ЕДНА сделка на едни готови входове. Живият бот НЕ Е
    това: той има ПОВТОРНО ПРЕДЛАГАНЕ (нов вход от СТАР сетъп), ТАВАН 12
    ЕДНОВРЕМЕННИ сделки и СТОП-ПАЗАЧ, който заключва посоката след стоп.
    Трите менят кои сделки изобщо СЪЩЕСТВУВАТ — не геометрията им.

КАКВО МОДЕЛИРА (трите най-тежки, преброени от живия дневник — виж README)
    1. РЕ-ОФЕР      · live_bot.py:7729   (`reoffer`)
    2. ТАВАН 12     · live_bot.py:8504/8508/9088  (`_слот_свободен`, ТАВАН_СДЕЛКИ:773)
    3. СТОП-ПАЗАЧ   · live_bot.py:7938   (`_пазач_n >= ПАЗАЧ_СТОПОВЕ`, 2611/2634/2695)
    плюс живата пауза COOL_MIN/COOL_FLIP = 5/5 (live_bot.py:2594/2824), докато
    geom_harness ползва 45/15 (geom_harness.py:64-65) — СТАРИТЕ стойности.

    ⚠️ РЕДОВЕТЕ СА ЧЕТЕНИ НА 05.09.2026 при `git rev-parse HEAD` = 6e8e9ee07
    (v18.58). live_bot.py се пише в същия ден — по-рано в тази сесия същите
    места бяха на 7614 / 8389 / 7823. Не вярвай на реда, вярвай на израза.

КАКВО НЕ МОДЕЛИРА (казано, не премълчано)
    · CyberQuant макро-щита (календар на събития не съществува за 22 години)
    · мозъка (chart_brain) — отделен производител на карти
    · СТРИЙК_ПАЗАЧ (пази срещу ревизия на данни ВЪТРЕ в деня; при бектест
      стрийкът се смята веднъж и не може да мигне)
    · ключът на анти-спама в живия бот се строи от 7-те рамки; тук, както и в
      geom_harness, е само «1ден»

БЕЗ pyarrow: DLL-ите са блокирани от Windows App Control на тази машина
(виж mer_celiyat-konveyer/pq_lite.py). Лентата идва от .npy кеша,
решетката — през pq_lite.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ТУК = Path(__file__).resolve().parent
IZM = ТУК.parent
REPO = IZM.parent
КЕШ_ЛЕНТА = IZM / "mer_shortyt" / "_cache"
РЕШЕТКА_PQ = IZM / "mer_celiyat-konveyer" / "reshetka.parquet"
SCRATCH = Path(r"C:\Users\User\AppData\Local\Temp\claude"
               r"\C--Users-User-Downloads-----"
               r"\2674809c-6765-4e6e-873d-82958246267b\scratchpad")
ВХОДОВЕ_PQ = SCRATCH / "geom_entries.parquet"

SLIP_PER_TRADE = 0.02          # geom_harness.py:62 — същата стойност, дословно

_T0 = time.time()


def лог(*a):
    print("[%7.1fs]" % (time.time() - _T0), *a, flush=True)


# --------------------------------------------------------------------- четци
def _pq():
    sys.path.insert(0, str(IZM / "mer_celiyat-konveyer"))
    import pq_lite
    return pq_lite


def лента():
    """B точно както gh.load_tape() го връща — от .npy кеша (numpy сам)."""
    keys = ("ob", "oa", "ha", "la", "ca", "cb", "hb", "lb", "dord", "tsmin")
    B = {k: np.load(КЕШ_ЛЕНТА / (k + ".npy")) for k in keys}
    лог("лента %s бара" % format(len(B["ob"]), ","))
    return B


def доставени_входове():
    """Точно `geom_entries.parquet` — 6846-те входа на СТАРИЯ уред."""
    d = _pq().read_columns(str(ВХОДОВЕ_PQ))
    d["direction"] = np.array([x.decode() for x in d["direction"]])
    d["tier"] = np.array([x.decode() for x in d["tier"]])
    return d


def решетка():
    """530 659 15-мин чекпойнта с всичко, което ботът е ВИЖДАЛ.
    Произведена от mer_celiyat-konveyer/k0_reshetka.py (огледало на
    gh.build_entries + допълнителните колони)."""
    d = _pq().read_columns(str(РЕШЕТКА_PQ))
    лог("решетка %s чекпойнта" % format(len(d["ts"]), ","))
    return d


# --------------------------------------------------------------------- сделка
def едно(i0, посока, entry_px, geom, B):
    """ЕДНА сделка, ред по ред срещу `gh._one_trade` (geom_harness.py:283-374).

    Разлики САМО там, където живото го иска:
      · `дни` е параметър на геометрията (gh има глобално TIME_EXIT_DAYS=5,
        живият бот държи ДНИ_МАКС=30 календарни ≈ 21 търговски)
    Всичко останало е ДОСЛОВНО същото: стоп ПРЕДИ цел в бара, гап през нивото
    се пълни на OPEN, стоп-на-входа се въоръжава от СЛЕДВАЩИЯ бар, входният
    бар не се ползва, изход по време на OPEN на първия бар след прозореца.
    Сверено в sverka.py: 0 разминавания на всичките 6846 входа.
    """
    s = 1 if посока == "long" else -1
    tps = geom["tps"]
    tp_lv = [entry_px + s * dist for _f, dist in tps]
    cur_sl = entry_px - s * geom["sl"]
    be = geom["be_after_tp1"]

    dord = B["dord"]
    n = len(dord)
    a = i0 + 1
    end_ord = dord[i0] + geom["дни"]
    b = int(np.searchsorted(dord, end_ord, side="left"))
    b = min(b, n)
    if a >= b:
        return None

    if s == 1:
        op = B["ob"][a:b].tolist(); hi = B["hb"][a:b].tolist(); lo = B["lb"][a:b].tolist()
    else:
        op = B["oa"][a:b].tolist(); hi = B["ha"][a:b].tolist(); lo = B["la"][a:b].tolist()

    filled = [False] * len(tps)
    rem = 1.0
    gross = 0.0
    n_tp = 0
    n_fills = 0
    exit_k = None
    kind = None
    for k in range(len(op)):
        o = op[k]; h = hi[k]; l = lo[k]
        if (l <= cur_sl) if s == 1 else (h >= cur_sl):
            gap = (o <= cur_sl) if s == 1 else (o >= cur_sl)
            px = o if gap else cur_sl
            gross += rem * s * (px - entry_px)
            rem = 0.0
            n_fills += 1
            exit_k = k
            if n_tp == 0:
                kind = "stop"
            elif be:
                kind = "be-stop-after-tp%d" % n_tp
            else:
                kind = "stop-after-tp%d" % n_tp
            break
        for ti in range(len(tps)):
            if filled[ti]:
                continue
            lv = tp_lv[ti]
            if (h >= lv) if s == 1 else (l <= lv):
                gap = (o >= lv) if s == 1 else (o <= lv)
                px = o if gap else lv
                gross += tps[ti][0] * s * (px - entry_px)
                rem -= tps[ti][0]
                filled[ti] = True
                n_tp += 1
                n_fills += 1
                if ti == 0 and be:
                    cur_sl = entry_px
        if rem <= 1e-12:
            exit_k = k
            kind = "tp%d" % len(tps)
            break

    if exit_k is None:
        if b < n:
            o_exit = B["ob"][b] if s == 1 else B["oa"][b]
            exit_idx = b
        else:
            o_exit = B["cb"][n - 1] if s == 1 else B["ca"][n - 1]
            exit_idx = n - 1
        gross += rem * s * (o_exit - entry_px)
        rem = 0.0
        n_fills += 1
        kind = ("time-after-tp%d" % n_tp) if n_tp else "time"
    else:
        exit_idx = a + exit_k

    return {"exit_index": int(exit_idx), "gross": gross,
            "net": gross - SLIP_PER_TRADE,
            "net_per_fill": gross - SLIP_PER_TRADE * n_fills,
            "n_fills": int(n_fills), "kind": kind, "n_tp": n_tp,
            "hold_min": int(B["tsmin"][exit_idx] - B["tsmin"][i0])}


# --------------------------------------------------------------------- геометрии
def Г(name, tps, sl, be_after_tp1=True, дни=5):
    return {"name": name, "tps": list(tps), "sl": float(sl),
            "be_after_tp1": bool(be_after_tp1), "дни": int(дни)}


# ДОСТАВЕНАТА (geom_harness.GEOM_SHIPPED) — за сверката
ДОСТАВЕНА_5Д = Г("доставена 7.5/12/20 · SL 20 · трети · BE след ТП1",
                 [(1 / 3, 7.5), (1 / 3, 12.0), (1 / 3, 20.0)], 20.0, True, 5)

# ЖИВАТА геометрия към 05.09.2026, ИЗПЪЛНЕНА от live_bot._геом в тази сесия:
#   long  → ((7.5, 12.0, 20.0), 13.0, (1/3, 1/3, 1/3))
#   short → ((5.0, 10.0, 20.0), 13.0, (0.5, 0.25, 0.25))
# при живия хоризонт ДНИ_МАКС=30 календарни ≈ 21 търговски (live_bot.py:816, 6334)
ЖИВА_LONG = Г("жива ЛОНГ 75/120/200 · SL 130п · трети · BE след ТП1",
              [(1 / 3, 7.5), (1 / 3, 12.0), (1 / 3, 20.0)], 13.0, True, 21)
ЖИВА_SHORT = Г("жива ШОРТ 50/100/200 · SL 130п · ½¼¼ · BE след ТП1",
               [(0.5, 5.0), (0.25, 10.0), (0.25, 20.0)], 13.0, True, 21)


def жива_геом(посока, дни=21):
    g = dict(ЖИВА_LONG if посока == "long" else ЖИВА_SHORT)
    g["дни"] = int(дни)
    return g


# --------------------------------------------------------------------- статистика
def бутстрап_по_ден(vals, dayid, reps=5000, seed=20260905):
    """Блоков бутстрап ПО ДЕН (не по сделка). Връща (средно, lo, hi)."""
    vals = np.asarray(vals, float)
    dayid = np.asarray(dayid)
    ok = ~np.isnan(vals)
    v = vals[ok]; dd = dayid[ok]
    if len(v) == 0:
        return (np.nan, np.nan, np.nan, 0)
    u, inv = np.unique(dd, return_inverse=True)
    S = np.bincount(inv, weights=v)
    C = np.bincount(inv).astype(float)
    k = len(u)
    rng = np.random.default_rng(seed)
    iz = rng.integers(0, k, size=(reps, k))
    bm = S[iz].sum(1) / np.maximum(C[iz].sum(1), 1)
    return (float(v.mean()), float(np.percentile(bm, 2.5)),
            float(np.percentile(bm, 97.5)), int(k))


def присъда(lo, hi, дни):
    if дни < 100:
        return "⚪ под 100 дни — не се съди"
    if lo > 0:
        return "✅ ДОКАЗАНО+"
    if hi < 0:
        return "🛑 ДОКАЗАНО−"
    return "⚪ НЕДОКАЗАНА"


# --------------------------------------------------------------------- бърз двигател
class _Прозорец:
    """Кеш на монотонните екстремуми в прозореца на сделката, за да отговаря
    «първият бар от k0 нататък с high>=X / low<=Y» с двоично търсене вместо
    ново обхождане. Копие на mer_shortyt/eng._Ctx, разширено за ДВЕТЕ посоки."""
    __slots__ = ("hi", "lo", "op", "m", "_c")

    def __init__(self, hi, lo, op):
        self.hi = hi; self.lo = lo; self.op = op; self.m = len(hi); self._c = {}

    def _acc(self, k0):
        c = self._c.get(k0)
        if c is None:
            c = (np.maximum.accumulate(self.hi[k0:]),
                 -np.minimum.accumulate(self.lo[k0:]))
            self._c[k0] = c
        return c

    def first_ge(self, k0, X):
        if k0 >= self.m:
            return -1
        cmx, _ = self._acc(k0)
        i = int(np.searchsorted(cmx, X, "left"))
        return k0 + i if i < len(cmx) else -1

    def first_le(self, k0, Y):
        if k0 >= self.m:
            return -1
        _, ncm = self._acc(k0)
        i = int(np.searchsorted(ncm, -Y, "left"))
        return k0 + i if i < len(ncm) else -1


def прозорец(i0, geom, B):
    dord = B["dord"]; n = len(dord)
    a = i0 + 1
    b = int(np.searchsorted(dord, dord[i0] + geom["дни"], "left"))
    return a, min(b, n)


def бързо(i0, посока, entry_px, geom, B, ctx=None, ab=None):
    """Същата физика като `едно`, но с двоични търсения вместо бар по бар.
    Сверено с `едно` (значи и с gh._one_trade) в sverka2.py — 0 разминавания."""
    s = 1 if посока == "long" else -1
    n = len(B["dord"])
    a, b = ab if ab is not None else прозорец(i0, geom, B)
    if a >= b:
        return None
    if ctx is None:
        if s == 1:
            ctx = _Прозорец(B["hb"][a:b], B["lb"][a:b], B["ob"][a:b])
        else:
            ctx = _Прозорец(B["ha"][a:b], B["la"][a:b], B["oa"][a:b])
    op, m = ctx.op, ctx.m
    lo_arr, hi_arr = ctx.lo, ctx.hi

    tps = geom["tps"]
    lv = [entry_px + s * d for _f, d in tps]
    cur = entry_px - s * geom["sl"]
    be = geom["be_after_tp1"]
    gross = 0.0; rem = 1.0; n_tp = 0; n_fills = 0
    exit_k = None; kind = None
    k0 = 0; ti = 0
    while True:
        # стоп: за ЛОНГ първият low<=cur; за ШОРТ първият high>=cur
        ks = ctx.first_le(k0, cur) if s == 1 else ctx.first_ge(k0, cur)
        kt = -1
        if ti < len(lv):
            kt = ctx.first_ge(k0, lv[ti]) if s == 1 else ctx.first_le(k0, lv[ti])
        if ks != -1 and (kt == -1 or ks <= kt):
            o = op[ks]
            gap = (o <= cur) if s == 1 else (o >= cur)
            px = o if gap else cur
            gross += rem * s * (px - entry_px)
            rem = 0.0; n_fills += 1; exit_k = ks
            kind = ("stop" if n_tp == 0 else
                    (("be-stop-after-tp%d" % n_tp) if be
                     else ("stop-after-tp%d" % n_tp)))
            break
        if kt == -1:
            break
        o = op[kt]
        ext = hi_arr[kt] if s == 1 else lo_arr[kt]
        while ti < len(lv) and ((ext >= lv[ti]) if s == 1 else (ext <= lv[ti])):
            gap = (o >= lv[ti]) if s == 1 else (o <= lv[ti])
            px = o if gap else lv[ti]
            gross += tps[ti][0] * s * (px - entry_px)
            rem -= tps[ti][0]
            if ti == 0 and be:
                cur = entry_px
            ti += 1; n_tp += 1; n_fills += 1
        if rem <= 1e-12:
            exit_k = kt; kind = "tp%d" % len(tps)
            break
        k0 = kt + 1
        if k0 >= m:
            break

    if exit_k is None:
        if b < n:
            o_exit = B["ob"][b] if s == 1 else B["oa"][b]
            exit_idx = b
        else:
            o_exit = B["cb"][n - 1] if s == 1 else B["ca"][n - 1]
            exit_idx = n - 1
        gross += rem * s * (o_exit - entry_px)
        n_fills += 1
        kind = ("time-after-tp%d" % n_tp) if n_tp else "time"
    else:
        exit_idx = a + exit_k
    return {"exit_index": int(exit_idx), "gross": gross,
            "net": gross - SLIP_PER_TRADE,
            "net_per_fill": gross - SLIP_PER_TRADE * n_fills,
            "n_fills": int(n_fills), "kind": kind, "n_tp": n_tp,
            "hold_min": int(B["tsmin"][exit_idx] - B["tsmin"][i0])}
