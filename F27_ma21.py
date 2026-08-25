# -*- coding: utf-8 -*-
"""
F25 · РЕГИСТРИРАН ТЕСТ · КАРТАТА «📌 НИВО» ЛЪЖЕ ЛИ

ЗАПИСАНО ПРЕДИ ИЗМЕРВАНЕТО.

## Поводът
Собственикът пита какво значи «👁 само знак · не влизам, сметката е на минус».
Проверих: този ред е ЗАКОВАН в `_ma_alert_msg` (live_bot.py:1464). Функцията
получава мерените числа (`mb`) и `macro` — и НЕ ПОЛЗВА НИТО ЕДНОТО (потвърдено
с AST). А същите числа в `backtest_stats.json` казват ОБРАТНОТО:

    long  ma50   n=470  win 62.8%  нето +4.64$
    long  ma200  n=186  win 61.3%  нето +3.69$
    short ma50   n=421  win 62.7%  нето +4.55$
    short ma200  n=193  win 57.0%  нето +2.41$

Картата казва «на минус» върху събитие, което файлът брои за +4.64$. Едното от
двете е невярно. И трите тези числа НЯМАТ `lo`/`hi` — точно като сребърните,
които днес се оказаха невъзпроизводими.

## Хипотеза
Числата `ma_bounce` са от същата непроверена партида като сребърните. Ако е
така, преизмерването под ДОСТАВЕНАТА геометрия ще ги свие драстично или ще ги
покаже като шум.

## Какво меря — ЗАКОВАНО
Условието е буквално от `_regime` (live_bot.py:456-460):
    long_maX  = low <= smaX and close > smaX
    short_maX = high >= smaX and close < smaX
върху ДНЕВНИ барове, сглобени от самата лента. Вход на затварянето на деня,
после ДОСТАВЕНАТА геометрия през `geom_harness` (ТП 7.5/12/20 · стоп 20 ·
стълба 1/3 · стоп на входа след ТП1 · време-изход), с РЕАЛНИЯ спред от лентата
(лонг излиза на bid, шорт на ask).
Блоков бутстрап ПО ДЕН, 4000 повторения, 95%.
Едно палене на ден на ключ — както прави `ma_sent` в бота.

## Кога казвам, че картата е права
Ако преизмереното нето е ≤ 0 или интервалът минава през нулата → «на минус» е
близо до истината и се пренаписва на мереното.
Ако е уверено положително → редът е ГРЕШЕН и се сменя с числото.

## Разлика от живото, която НЕ крия
Ботът съди по НЕЗАВЪРШЕН дневен бар (`iloc[-1]` е днешният, в движение), значи
може да пали и да се отпалва в рамките на деня. Тук меря ПОТВЪРДЕНАТА версия
(на затваряне) — тоест по-ДОБРОТО от двете. Излезе ли и тя нула, живата е
по-лоша, не по-добра.
"""
import sys, warnings, time, io, json
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

SP = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad"
sys.path.insert(0, SP)
import geom_harness as GH
GH.TIME_EXIT_DAYS = 21   # 🔴 живото: live_bot.py:2204 «age >= 30» календарни ≈ 21 търговски

t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)

B = GH.load_tape()
n = len(B["dord"])

# ── дневни барове от самата лента (mid), + индекс на последния бар за деня ──
лог("сглобявам дневни барове от лентата…")
mid_h = (B["hb"] + B["ha"]) / 2.0
mid_l = (B["lb"] + B["la"]) / 2.0
mid_c = (B["cb"] + B["ca"]) / 2.0
d = pd.DataFrame({"d": B["dord"], "h": mid_h, "l": mid_l, "c": mid_c})
g = d.groupby("d")
DAY = pd.DataFrame({"high": g["h"].max(), "low": g["l"].min(),
                    "close": g["c"].last(), "last_i": g.apply(lambda x: x.index[-1])})
DAY = DAY.reset_index(drop=False).rename(columns={"d": "dord"})
лог(f"  {len(DAY):,} търговски дни")

# 🔴 живото:  връща df.iloc[:-1] → средните са само от ЗАВЪРШЕНИ дни
DAY["sma50"] = DAY["close"].shift(1).rolling(50).mean()
DAY["sma200"] = DAY["close"].shift(1).rolling(200).mean()

СЪБИТИЯ = {
    "long_ma50":   lambda r: r.low <= r.sma50 and r.close > r.sma50,
    "short_ma50":  lambda r: r.high >= r.sma50 and r.close < r.sma50,
    "long_ma200":  lambda r: r.low <= r.sma200 and r.close > r.sma200,
    "short_ma200": lambda r: r.high >= r.sma200 and r.close < r.sma200,
}
ГЕОМ = {"name": "доставената", "sl": 20.0,
        "tps": [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], "be_after_tp1": True}

RNG = np.random.default_rng(25)
ТС = pd.to_datetime(pd.Series(B["ts"]))
СТАРО = json.load(io.open("backtest_stats.json", encoding="utf-8")).get("ma_bounce", {})

print()
print("=" * 96)
print("F27 · ОТСКОК (ЖИВИЯТ ХОРИЗОНТ 21д) ОТ ПЪЛЗЯЩА СРЕДНА · доставената геометрия, реален спред от лентата")
print("=" * 96)
print(f"  {'събитие':13s} {'СТАРО n':>8s} {'СТАРО нето':>11s} {'МОЕ n':>7s} "
      f"{'МОЕ нето':>10s} {'95% интервал':>22s}  присъда")

изход = {}
for име, тест in СЪБИТИЯ.items():
    посока, ma = име.split("_", 1)
    редове = []
    for r in DAY.itertuples():
        if not np.isfinite(getattr(r, "sma200" if ma == "ma200" else "sma50", np.nan)):
            continue
        try:
            ако = тест(r)
        except Exception:
            continue
        if not ако:
            continue
        i0 = int(r.last_i)
        if i0 + 1 >= n:
            continue
        вх = B["ca"][i0] if посока == "long" else B["cb"][i0]   # плащаш спреда на входа
        res = GH._one_trade(i0, посока, float(вх), ГЕОМ, B)
        if res is not None:
            редове.append((res["net"], ТС.iloc[i0].normalize()))
    if len(редове) < 30:
        print(f"  {име:13s} малко ({len(редове)})")
        continue
    T = pd.DataFrame(редове, columns=["net", "ден"])
    dd = T.groupby("ден")["net"].agg(["sum", "count"])
    S, C = dd["sum"].to_numpy(), dd["count"].to_numpy(); k = len(S)
    из = RNG.integers(0, k, size=(4000, k))
    m = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    lo, hi = float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))
    ср = float(T["net"].mean())
    ст = (СТАРО.get(посока, {}) or {}).get(ma, {}) or {}
    шум = lo <= 0 <= hi
    пр = "🔴 ШУМ" if шум else ("✅ ПЕЧЕЛИ" if ср > 0 else "❌ ГУБИ")
    print(f"  {име:13s} {ст.get('n', '—'):>8} {ст.get('net', '—'):>11} {len(T):>7,d} "
          f"{ср:>+10.3f} [{lo:+8.3f} .. {hi:+8.3f}]  {пр}")
    изход[име] = {"n": len(T), "net": round(ср, 3), "lo": round(lo, 3), "hi": round(hi, 3),
                  "win": round(float((T["net"] > 0).mean() * 100), 1), "дни": int(k),
                  "шум": bool(шум)}

json.dump(изход, io.open("F27_ma21.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print()
поб = [k for k, v in изход.items() if not v["шум"] and v["net"] > 0]
if поб:
    print(f"УВЕРЕНО ПОЛОЖИТЕЛНИ: {', '.join(поб)}")
    print("→ редът «сметката е на минус» е ГРЕШЕН за тези и трябва да носи числото")
else:
    print("НИТО ЕДНО НЕ Е УВЕРЕНО ПОЛОЖИТЕЛНО → «не влизам» е правилното поведение,")
    print("но текстът трябва да цитира МЕРЕНОТО, а старите числа да падат от файла.")
лог("готово")
