# -*- coding: utf-8 -*-
"""F24г · ЗАПИСВАМ ПРЕИЗМЕРЕНИТЕ СРЕБЪРНИ КЛЕТКИ В backtest_stats.json"""
import warnings, io, json, shutil
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
exec(io.open("F24_srebro.py", encoding="utf-8").read().split('RNG = np.random')[0]
     .replace('лог(f"сделки', '#').replace('print()', '#'))

RNG = np.random.default_rng(24)
КЛ = {"day1": lambda g: g["стрийк"] == 1, "fresh": lambda g: g["стрийк"].between(2, 3),
      "mixed": lambda g: g["стрийк"] == 0, "stale": lambda g: g["стрийк"] >= 4,
      "ultra": lambda g: (g["стрийк"].between(1, 3)) & (g["vr"] < 0.40)}
ГР = pd.Timestamp("2013-01-01")


def бут(x, дни, seed):
    r = np.random.default_rng(seed)
    d = pd.DataFrame({"n": x, "д": дни}).groupby("д")["n"].agg(["sum", "count"])
    S, C = d["sum"].to_numpy(), d["count"].to_numpy(); k = len(S)
    из = r.integers(0, k, size=(4000, k))
    m = S[из].sum(axis=1) / np.maximum(C[из].sum(axis=1), 1)
    return round(float(np.percentile(m, 2.5)), 4), round(float(np.percentile(m, 97.5)), 4), len(S)


нов = {}
for i, d in enumerate(("long", "short")):
    нов[d] = {}
    for j, (им, ф) in enumerate(КЛ.items()):
        g = T[(T["посока"] == d) & ф(T)]
        if len(g) < 30: continue
        x = g["нето"].to_numpy(); дни = g["ден"].to_numpy()
        lo, hi, nd = бут(x, дни, 1000 + i * 10 + j)
        ран = g[g["ден"] < ГР]["нето"].mean() if (g["ден"] < ГР).sum() >= 30 else np.nan
        къс = g[g["ден"] >= ГР]["нето"].mean() if (g["ден"] >= ГР).sum() >= 30 else np.nan
        съгл = bool(np.isfinite(ран) and np.isfinite(къс)
                    and np.sign(ран - 0.03) == np.sign(къс - 0.03))
        нов[d][им] = {
            "win": round(float((x > 0).mean() * 100), 1), "n": int(len(g)), "дни": int(nd),
            "_сурово": {"net": round(float(x.mean()), 4), "lo": lo, "hi": hi},
            "_епохи": {"2000-2012": round(float(ран), 4) if np.isfinite(ран) else None,
                       "2013-2026": round(float(къс), 4) if np.isfinite(къс) else None},
            "_епохи_съгласни": съгл}

p = "backtest_stats.json"
shutil.copy(p, p + ".преди_F24")
st = json.load(io.open(p, encoding="utf-8"))
стар = st.get("silver", {})

# КЛАСОВИТЕ клетки (premium/strong/medium/weak) НЕ се пипат — те са друго измерение
sv = {}
for d in ("long", "short"):
    sv[d] = {k: v for k, v in (стар.get(d, {}) or {}).items()
             if k in ("premium", "strong", "medium", "weak")}
    sv[d].update(нов[d])
sv["_метод"] = (
    "F24 · 12858 сделки от ДНЕВНИ барове silver_yahoo_full.csv 2000-08→2026-07, "
    "доставената сребърна геометрия (ТП 0.20/0.32/0.54 · стоп 0.54 · стълба 1/3 · "
    "стоп на входа след ТП1 · време-изход 21 дни · при съмнение в един ден СТОПЪТ бие). "
    "Блоков бутстрап ПО ДЕН, 4000 повторения, 95%. "
    "`_сурово` е БЕЗ разход; живите net/lo/hi се смятат от бота като `_сурово` минус "
    "СРЕБРО_СПРЕД (по подразбиране 0.03$).")
sv["_разделителна"] = ("ДНЕВНА. Златото е мерено на 7.96М едноминутни бара с двете страни "
                       "на спреда; среброто НЯМА такива данни. Затова сребърните числа са "
                       "ПО-ГРУБИ и по-скоро оптимистични, отколкото песимистични.")
sv["_епохи_бележка"] = ("Всяка ЛОНГ клетка сменя знака: печели 2000-2012, губи 2013-2026. "
                        "Тоест «ръбът» е от сребърния бичи пазар до 2011, не от правилото. "
                        "Клетка с разминаващи се епохи се брои за ШУМ, дори интервалът да е "
                        "над нулата.")
sv["_старо"] = {"защо": ("числата, по които ботът решаваше до 18.08. Нямат нито интервали, "
                         "нито записан метод, и не се възпроизвеждат: long/stale беше n=556, "
                         "преизмерено дава n=1204; long/fresh беше +0.111$, преизмерено +0.033$."),
                "стойности": {d: {k: v for k, v in (стар.get(d, {}) or {}).items()
                                  if k in ("fresh", "stale")} for d in ("long", "short")}}
st["silver"] = sv
json.dump(st, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("ЗАПИСАНО. Как ще изглежда при СРЕБРО_СПРЕД=0.03:")
print(f"  {'':14s} {'n':>6s} {'сурово':>9s} {'живо':>9s} {'95% живо':>20s} {'епохи':>9s}  ГЕЙТ")
for d in ("long", "short"):
    for им in КЛ:
        a = sv[d].get(им)
        if not a: continue
        s_ = a["_сурово"]; n_, l_, h_ = s_["net"] - .03, s_["lo"] - .03, s_["hi"] - .03
        шум = (l_ <= 0 <= h_) or not a["_епохи_съгласни"]
        отк = a["n"] >= 100 and (n_ <= 0 or шум)
        print(f"  {d:6s} {им:7s} {a['n']:6,d} {s_['net']:+9.4f} {n_:+9.4f} "
              f"[{l_:+7.4f}..{h_:+7.4f}] {'⚖️да' if a['_епохи_съгласни'] else '🔴не':>9s}  "
              f"{'ОТКАЗ' if отк else '❓пуска'}")
