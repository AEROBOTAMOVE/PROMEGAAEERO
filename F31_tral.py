# -*- coding: utf-8 -*-
"""
F31 · РЕГИСТРИРАН ТЕСТ · ТРАЛИНГ-СТОП

ЗАПИСАНО ПРЕДИ ИЗМЕРВАНЕТО. Сменя ли се вариант, праг или критерий след първия
резултат — това е нов тест с ново име, не поправка на този.

## Защо точно това
Инвентарът на всичко правено по геометрията (18.08) показа, че ЕДНО измерение
никога не е мерено както трябва: ТРАЛИНГЪТ. Думата «trail» се среща 0 пъти в
geom_harness.py — двигателят просто няма такава физика. Единственото досегашно
измерване е с ДРУГ инструмент, при СТАРИЯ гейт отпреди 04.08, n=1705:
трал 1×ATR след ТП1 → Δ+0.138$, t=+1.11. Тоест «нищо не се доказва, но не е
и убито».

Всичко останало по геометрията вече е затворено:
· размер (F22 → F28 → F28б → F30 → ДРИФТ)
· форма на прибиране (F23, 0 от 4)
· махане на стопа-на-входа (тествано при 21 дни: −0.1137 с BE срещу −0.2748 без)
· ATR-мащабиране (89.6% от преимуществото идва от 7% от сделките → концентрация)
· четири цели по ¼ (Δ−0.119, ДОКАЗАНО по-лошо)

## Как разширявам двигателя, без да го променям
Не пипам geom_harness.py. Пиша СВОЙ ходач `_trail_trade`, огледален на
`GH._one_trade` ред по ред, с ЕДНА добавка: подвижен стоп.

🔴 ЗАДЪЛЖИТЕЛНА ПРОВЕРКА ПРЕДИ ВСЯКО ЧИСЛО: при ИЗКЛЮЧЕН тралинг моят ходач
трябва да дава БИТ-В-БИТ същите резултати като GH._one_trade на всичките 6846
входа. Не съвпадне ли — числата не струват нищо и тестът спира. Това е
единствената защита срещу «поправих физиката, без да искам».

## Какво меря — ЗАКОВАНО
Трал, ВЪОРЪЖЕН СЛЕД ТП1 (както живият бот вече мести стопа на входа там),
на разстояние D под най-високото достигнато (за лонг):
    cur_sl = max(cur_sl, най-висок_bid − D)
Варианти: D = 7.5 / 10 / 15 / 20$ · плюс «трал от входа» (без чакане на ТП1)
при D = 15$. Пет сравнения.

## Критерии за убиване — ЗАКОВАНИ
1. Сдвоена разлика спрямо доставената, 99.0% интервал (Bonferroni за 5
   сравнения) НАД нулата, И
2. превъзходство ≥ +0.20$/сделка, И
3. бие в ДВЕТЕ епохи (граница 2014-01-01), И
4. 🔴 РАБОТИ И В ШОРТ. Това е поуката от F30: ефект само в ЛОНГ значи
   изложеност на 22-годишния ръст на златото, не умение. Тралингът реже
   печалбите отгоре — ако помага само в лонг, е дрифт.

Не мине ли и четирите → THREAD_ENDS, тралингът се записва като проверен и
отхвърлен, и РЕД 5 е изчерпан.

## Известни граници
· Слипът се вади ВЕДНЪЖ на сделка (одит П3). Тралингът НЕ мени броя крака
  спрямо доставената (и двете имат 3), значи корекцията ги мести еднакво.
· 21 търговски дни, както живият бот.
"""
import sys, warnings, time
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
SP = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad"
sys.path.insert(0, SP)
import geom_harness as GH
GH.TIME_EXIT_DAYS = 21

t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)


def _trail_trade(i0, direction, entry_px, geom, B, trail=None, trail_from_entry=False):
    """ОГЛЕДАЛО на GH._one_trade + подвижен стоп. trail=None → същото поведение."""
    s = 1 if direction == "long" else -1
    tps = geom["tps"]
    tp_lv = [entry_px + s * dist for _f, dist in tps]
    cur_sl = entry_px - s * geom["sl"]
    be = geom["be_after_tp1"]

    dord = B["dord"]; n = len(dord)
    a = i0 + 1
    end_ord = dord[i0] + GH.TIME_EXIT_DAYS
    b = min(int(np.searchsorted(dord, end_ord, side="left")), n)
    if a >= b:
        return None
    if s == 1:
        op = B["ob"][a:b].tolist(); hi = B["hb"][a:b].tolist(); lo = B["lb"][a:b].tolist()
    else:
        op = B["oa"][a:b].tolist(); hi = B["ha"][a:b].tolist(); lo = B["la"][a:b].tolist()

    filled = [False] * len(tps); rem = 1.0; gross = 0.0; n_tp = 0
    exit_k = None; kind = None
    въоръжен = bool(trail) and trail_from_entry
    връх = entry_px                       # най-добрата достигната цена
    for k in range(len(op)):
        o = op[k]; h = hi[k]; l = lo[k]
        # --- СТОПЪТ ПЪРВИ (песимистично, като живия бот) ---
        if (l <= cur_sl) if s == 1 else (h >= cur_sl):
            gap = (o <= cur_sl) if s == 1 else (o >= cur_sl)
            px = o if gap else cur_sl
            gross += rem * s * (px - entry_px); rem = 0.0; exit_k = k
            kind = ("stop" if n_tp == 0 else
                    (f"be-stop-after-tp{n_tp}" if be else f"stop-after-tp{n_tp}"))
            break
        # --- целите, по реда на стълбата ---
        for ti in range(len(tps)):
            if filled[ti]:
                continue
            lv = tp_lv[ti]
            if (h >= lv) if s == 1 else (l <= lv):
                gap = (o >= lv) if s == 1 else (o <= lv)
                px = o if gap else lv
                gross += tps[ti][0] * s * (px - entry_px)
                rem -= tps[ti][0]; filled[ti] = True; n_tp += 1
                if ti == 0 and be:
                    cur_sl = entry_px
                if ti == 0 and trail and not trail_from_entry:
                    въоръжен = True
        if rem <= 1e-12:
            exit_k = k; kind = f"tp{len(tps)}"; break
        # --- ТРАЛИНГЪТ: СЛЕД проверката на стопа за този бар, значи новото ниво
        #     важи от СЛЕДВАЩИЯ бар. Иначе стоп и трал биха се хванали в един и
        #     същ бар — поглед напред вътре в бара.
        if въоръжен and trail:
            връх = max(връх, h) if s == 1 else min(връх, l)
            нов = връх - trail if s == 1 else връх + trail
            cur_sl = max(cur_sl, нов) if s == 1 else min(cur_sl, нов)

    if exit_k is None:
        if b < n:
            o_exit = B["ob"][b] if s == 1 else B["oa"][b]; exit_idx = b
        else:
            o_exit = B["cb"][n - 1] if s == 1 else B["ca"][n - 1]; exit_idx = n - 1
        gross += rem * s * (o_exit - entry_px); rem = 0.0
        kind = f"time-after-tp{n_tp}" if n_tp else "time"
    else:
        exit_idx = a + exit_k
    return {"exit_index": int(exit_idx), "gross": gross,
            "net": gross - GH.SLIP_PER_TRADE, "kind": kind, "n_tp": n_tp}


B = GH.load_tape(); E = GH.build_entries(B)
ДЕН = pd.to_datetime(pd.Series(B["ts"])[E["bar_index"].values].values).normalize()
dirs = E["direction"].values
idxs = E["bar_index"].values; pxs = E["entry_px"].values
ГЕОМ = {"name": "доставената", "sl": 20.0,
        "tps": [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], "be_after_tp1": True}
лог(f"входове: {len(E):,} · време-изход {GH.TIME_EXIT_DAYS}д")

# ══ ЗАДЪЛЖИТЕЛНАТА ПРОВЕРКА: изключен трал == оригиналът, БИТ В БИТ ══
лог("сверявам ходача с оригинала (без трал)…")
разл = 0; макс = 0.0
for p in range(len(idxs)):
    r1 = GH._one_trade(int(idxs[p]), dirs[p], float(pxs[p]), ГЕОМ, B)
    r2 = _trail_trade(int(idxs[p]), dirs[p], float(pxs[p]), ГЕОМ, B, trail=None)
    if (r1 is None) != (r2 is None):
        разл += 1; continue
    if r1 is None:
        continue
    d = abs(r1["net"] - r2["net"])
    макс = max(макс, d)
    if d > 1e-12 or r1["kind"] != r2["kind"] or r1["n_tp"] != r2["n_tp"]:
        разл += 1
print()
print("=" * 84)
print(f"СВЕРКА С ОРИГИНАЛА · разминавания: {разл} · max|Δnet| = {макс:.2e}")
if разл or макс > 1e-12:
    print("🔴 ХОДАЧЪТ НЕ Е ОГЛЕДАЛО — числата по-долу не струват нищо. СПИРАМ.")
    sys.exit(1)
print("✅ БИТ В БИТ същият. Разширението не е пипнало физиката.")
print("=" * 84)

ВАР = [("0 доставената (без трал)", None, False),
       ("1 трал 7.5$ след ТП1", 7.5, False),
       ("2 трал 10$ след ТП1", 10.0, False),
       ("3 трал 15$ след ТП1", 15.0, False),
       ("4 трал 20$ след ТП1", 20.0, False),
       ("5 трал 15$ ОТ ВХОДА", 15.0, True)]
N = {}
for име, тр, отвх in ВАР:
    v = np.full(len(idxs), np.nan)
    for p in range(len(idxs)):
        r = _trail_trade(int(idxs[p]), dirs[p], float(pxs[p]), ГЕОМ, B, тр, отвх)
        if r is not None:
            v[p] = r["net"]
    N[име] = v
    лог(f"  {име:26s} {np.nanmean(v):+7.3f}$/oz")

RNG = np.random.default_rng(31)
д = pd.Series(ДЕН)


def разлика(a, b, маска=None, alpha=99.0):
    ок = np.isfinite(a) & np.isfinite(b)
    if маска is not None: ок &= маска
    if ок.sum() < 200: return None
    dd = pd.DataFrame({"d": a[ок] - b[ок], "day": д[ок].values})
    g = dd.groupby("day")["d"].agg(["sum", "count"])
    S, C = g["sum"].to_numpy(), g["count"].to_numpy(); k = len(S)
    из = RNG.integers(0, k, size=(4000, k))
    m = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    a_ = (100 - alpha) / 2
    return S.sum()/C.sum(), np.percentile(m, a_), np.percentile(m, 100 - a_), int(ок.sum())


база = N["0 доставената (без трал)"]
print()
print("=" * 92)
print("F31 · ТРАЛИНГ · сдвоено, блоков бутстрап по ден, 99.0% (Bonferroni за 5)")
print("=" * 92)
поб = []
for име, _, _ in ВАР:
    if име.startswith("0"):
        print(f"  {име:26s} {np.nanmean(база):+8.3f}$   —"); continue
    r = разлика(N[име], база)
    dd, lo, hi, n = r
    ок = lo > 0 and dd >= 0.20
    print(f"  {име:26s} {np.nanmean(N[име]):+8.3f}$  {dd:+8.3f}$  "
          f"[{lo:+7.3f} .. {hi:+7.3f}]  {'✅ БИЕ' if ок else 'не бие'}")
    if ок: поб.append(име)

print()
print("=" * 92)
print("ПОУКАТА ОТ F30 · работи ли и в ШОРТ (иначе е дрифт, не умение)")
print("=" * 92)
for име, _, _ in ВАР:
    if име.startswith("0"): continue
    rl = разлика(N[име], база, dirs == "long")
    rs = разлика(N[име], база, dirs == "short")
    двете = rl and rs and rl[0] > 0 and rs[0] > 0
    print(f"  {име:26s} ЛОНГ {rl[0]:+7.3f}$ · ШОРТ {rs[0]:+7.3f}$  "
          f"{'⚖️ и двете' if двете else '🔴 само едната'}")

print()
if not поб:
    print("НИТО ЕДИН ТРАЛ НЕ БИЕ ДОСТАВЕНАТА → F31 THREAD_ENDS")
    print("РЕД 5 е изчерпан: размер, форма, стоп-на-входа, ATR, брой цели, тралинг.")
else:
    гр = pd.Timestamp("2014-01-01"); ранни = (д < гр).to_numpy()
    for име in поб:
        ра, къ = разлика(N[име], база, ранни), разлика(N[име], база, ~ранни)
        rs = разлика(N[име], база, dirs == "short")
        print(f"  {име:26s} 2006-13 {ра[0]:+.3f} · 2014-26 {къ[0]:+.3f} · ШОРТ {rs[0]:+.3f}")
лог("готово")
