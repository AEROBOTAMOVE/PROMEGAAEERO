# -*- coding: utf-8 -*-
"""adv · АТАКА срещу F25 (отскок от MA). Само чете."""
import sys, warnings, time, io, json
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

SP = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad"
sys.path.insert(0, SP)
import geom_harness as GH

t0 = time.time()
лог = lambda s: print(f"[{time.time()-t0:6.1f}s] {s}", flush=True)
B = GH.load_tape()
n = len(B["dord"])
ТС = pd.to_datetime(pd.Series(B["ts"]))

# ── дневни барове, точно както F25 ────────────────────────────────────────────
mid_h = (B["hb"] + B["ha"]) / 2.0
mid_l = (B["lb"] + B["la"]) / 2.0
mid_c = (B["cb"] + B["ca"]) / 2.0
d = pd.DataFrame({"d": B["dord"], "h": mid_h, "l": mid_l, "c": mid_c})
g = d.groupby("d")
DAY = pd.DataFrame({"high": g["h"].max(), "low": g["l"].min(), "close": g["c"].last(),
                    "last_i": g.apply(lambda x: x.index[-1])}).reset_index(drop=False).rename(columns={"d": "dord"})
DAY["дата"] = ТС.iloc[DAY["last_i"].values].dt.normalize().values
лог(f"{len(DAY):,} дни · {DAY['дата'].iloc[0]} → {DAY['дата'].iloc[-1]}")
print(f"  спред в лентата: медиана {np.median(B['ca']-B['cb']):.4f}$ · "
      f"средно {np.mean(B['ca']-B['cb']):.4f}$ · 90% {np.percentile(B['ca']-B['cb'],90):.4f}$")

# F25:   sma включва ДНЕШНОТО затваряне
DAY["sma50_f25"] = DAY["close"].rolling(50).mean()
DAY["sma200_f25"] = DAY["close"].rolling(200).mean()
# ЖИВО: live_bot `_hist` = gold_d.iloc[:-1] → sma САМО от ЗАВЪРШЕНИ дни (без днешния)
DAY["sma50_live"] = DAY["close"].rolling(50).mean().shift(1)
DAY["sma200_live"] = DAY["close"].rolling(200).mean().shift(1)

ГЕОМ = {"name": "доставената", "sl": 20.0,
        "tps": [(1/3, 7.5), (1/3, 12.0), (1/3, 20.0)], "be_after_tp1": True}
СЪБ = ["long_ma50", "short_ma50", "long_ma200", "short_ma200"]


def палене(конв):
    """връща {име: DataFrame(dord,last_i,close,high,low)} на палещите дни"""
    из = {}
    for име in СЪБ:
        посока, ma = име.split("_", 1)
        s = DAY[f"{ma.replace('ma','sma')}_{конв}"]
        ок = s.notna()
        if посока == "long":
            m = ок & (DAY["low"] <= s) & (DAY["close"] > s)
        else:
            m = ок & (DAY["high"] >= s) & (DAY["close"] < s)
        из[име] = DAY[m]
    return из


P = {к: палене(к) for к in ("f25", "live")}
print()
print("=" * 104)
print("1 · SMA ОТ ЗАВЪРШЕНИ ДНИ ЛИ Е · live_bot `_hist` реже последния ден, F25 не реже")
print("=" * 104)
print(f"  {'събитие':13s} {'F25 n':>7s} {'ЖИВО n':>7s} {'общи':>6s} {'само F25':>9s} {'само живо':>10s}")
for име in СЪБ:
    a = set(P["f25"][име]["dord"]); b = set(P["live"][име]["dord"])
    print(f"  {име:13s} {len(a):7d} {len(b):7d} {len(a & b):6d} {len(a - b):9d} {len(b - a):10d}")
print("  → ако «само F25»/«само живо» са голям дял, F25 мери ДРУГО събитие, не живото.")
print()


def сделки(дни, посока, вход_на, tex, slip=None):
    стар_tex, стар_slip = GH.TIME_EXIT_DAYS, GH.SLIP_PER_TRADE
    GH.TIME_EXIT_DAYS = tex
    if slip is not None: GH.SLIP_PER_TRADE = slip
    out = []
    for i0 in дни["last_i"].to_numpy():
        i0 = int(i0)
        if i0 + 1 >= n: continue
        if вход_на == "ask":   вх = B["ca"][i0] if посока == "long" else B["cb"][i0]
        elif вход_на == "mid": вх = (B["ca"][i0] + B["cb"][i0]) / 2.0
        r = GH._one_trade(i0, посока, float(вх), ГЕОМ, B)
        if r is not None:
            out.append((r["net"], r["gross"], ТС.iloc[i0].normalize(), r["kind"]))
    GH.TIME_EXIT_DAYS, GH.SLIP_PER_TRADE = стар_tex, стар_slip
    return pd.DataFrame(out, columns=["net", "gross", "ден", "kind"])


def блок_ки(x, L=10, Bn=4000, seed=25):
    rng = np.random.default_rng(seed); m = len(x)
    if m < L * 2: L = max(2, m // 4)
    nb = int(np.ceil(m / L))
    st = rng.integers(0, max(m - L + 1, 1), size=(Bn, nb))
    из = (st[:, :, None] + np.arange(L)[None, None, :]).reshape(Bn, -1)[:, :m]
    v = x[np.minimum(из, m - 1)].mean(axis=1)
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def iid_ки(x, Bn=4000, seed=25):
    rng = np.random.default_rng(seed); m = len(x)
    v = x[rng.integers(0, m, size=(Bn, m))].mean(axis=1)
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


print("=" * 104)
print("2 · ВРЕМЕ-ИЗХОДЪТ · geom_harness реже на 5 ТЪРГОВСКИ дни; live_bot.py:2125-2127 реже на")
print("    30 КАЛЕНДАРНИ дни (≈21 търговски). F25 мери сделка, каквато ботът НЕ прави.")
print("=" * 104)
print(f"  {'събитие':13s} {'конв':5s} {'n':>5s} " + "".join(f"{f'изход {t}д':>13s}" for t in (5, 10, 15, 21)))
СЪХР = {}
for конв in ("f25", "live"):
    for име in СЪБ:
        посока = име.split("_")[0]
        ред = f"  {име:13s} {конв:5s}"
        first = True
        for tex in (5, 10, 15, 21):
            Tr = сделки(P[конв][име], посока, "ask", tex)
            if first: ред += f" {len(Tr):5d}"; first = False
            ред += f"{Tr['net'].mean():+13.3f}"
            СЪХР[(конв, име, tex)] = Tr
        print(ред)
print()
print(f"  {'събитие':13s} {'конв':5s} {'изход':>6s} {'нето':>9s} {'iid 95% (F25)':>21s} {'блоков 95%':>21s}  присъда")
for конв in ("f25", "live"):
    for име in СЪБ:
        for tex in (5, 21):
            Tr = СЪХР[(конв, име, tex)]
            x = Tr["net"].to_numpy()
            lo1, hi1 = iid_ки(x); lo2, hi2 = блок_ки(x)
            пр = "ШУМ" if lo2 <= 0 <= hi2 else ("ПЕЧЕЛИ" if x.mean() > 0 else "ГУБИ")
            print(f"  {име:13s} {конв:5s} {tex:5d}д {x.mean():+9.3f} [{lo1:+8.3f},{hi1:+8.3f}] "
                  f"[{lo2:+8.3f},{hi2:+8.3f}]  {пр}")
print()

print("=" * 104)
print("3 · ПРЕКАЛЕНО ПЕСИМИСТИЧЕН ЛИ Е ВХОДЪТ · спред на входа + 0.02$ приплъзване")
print("=" * 104)
print(f"  {'събитие':13s} {'вход ask+slip':>14s} {'вход mid+slip':>14s} {'вход mid, 0 slip':>17s} {'БРУТО':>9s}")
for име in СЪБ:
    посока = име.split("_")[0]
    a = сделки(P["live"][име], посока, "ask", 21)
    b = сделки(P["live"][име], посока, "mid", 21)
    c = сделки(P["live"][име], посока, "mid", 21, slip=0.0)
    print(f"  {име:13s} {a['net'].mean():+14.3f} {b['net'].mean():+14.3f} "
          f"{c['net'].mean():+17.3f} {a['gross'].mean():+9.3f}")
print("  (БРУТО = преди 0.02$ приплъзване, но изходът пак е от вярната страна на спреда)")
print()

# ═══════════════ 4 · ОТКЪДЕ ИДВАТ СТАРИТЕ +4.64$ ═══════════════
print("=" * 104)
print("4 · МОЖЕ ЛИ ДА ВЪЗПРОИЗВЕДА СТАРИТЕ +4.64$ С ДРУГ МЕТОД (дневен барер, без спред)")
print("=" * 104)
СТАРО = {"long_ma50": (470, 4.64, 62.8), "long_ma200": (186, 3.69, 61.3),
         "short_ma50": (421, 4.55, 62.7), "short_ma200": (193, 2.41, 57.0)}
H_, L_, C_ = DAY["high"].to_numpy(), DAY["low"].to_numpy(), DAY["close"].to_numpy()
ND = len(DAY)
ТПг = (7.5, 12.0, 20.0); СЛг = 20.0


def дневна_сделка(i, лонг, макс, стоп_бие):
    зн = 1.0 if лонг else -1.0
    вх = C_[i]; tp = [вх + зн * t for t in ТПг]; sl = вх - зн * СЛг
    пари = 0.0; взети = 0; бе = False
    for j in range(i + 1, min(i + 1 + макс, ND)):
        hi, lo = H_[j], L_[j]
        тек = вх if бе else sl
        уд = (lo <= тек) if лонг else (hi >= тек)
        нови = [k for k, t in enumerate(tp) if k >= взети and ((hi >= t) if лонг else (lo <= t))]
        if уд and (стоп_бие or not нови):
            return пари + (тек - вх) * зн * (3 - взети) / 3.0, взети
        for k in нови:
            пари += (tp[k] - вх) * зн / 3.0; взети = k + 1
            if k == 0: бе = True
            if k == 2: return пари, взети
        if уд and not стоп_бие:
            return пари + (тек - вх) * зн * (3 - взети) / 3.0, взети
    return пари + (C_[min(i + макс, ND - 1)] - вх) * зн * (3 - взети) / 3.0, взети


print(f"  {'събитие':13s} {'СТАРО n':>8s} {'СТАРО нето':>11s} {'СТАРО win':>10s} ‖ "
      f"{'дневен барер, ЦЕЛТА бие':>26s} ‖ {'дневен барер, СТОПЪТ бие':>26s}")
for име in СЪБ:
    посока, ma = име.split("_", 1)
    idx = P["f25"][име].index.to_numpy()
    for етик, стоп_бие in (("целта", False), ("стопа", True)):
        pass
    r_tp = [дневна_сделка(int(i), посока == "long", 21, False) for i in idx]
    r_sl = [дневна_сделка(int(i), посока == "long", 21, True) for i in idx]
    a = np.array([x[0] for x in r_tp]); b = np.array([x[0] for x in r_sl])
    sn, sv, sw = СТАРО[име]
    print(f"  {име:13s} {sn:8d} {sv:+11.2f} {sw:9.1f}% ‖ "
          f"n={len(a):4d} нето {a.mean():+7.3f} win {(a>0).mean()*100:5.1f}% ‖ "
          f"n={len(b):4d} нето {b.mean():+7.3f} win {(b>0).mean()*100:5.1f}%")
print()
print("  Ако «ЦЕЛТА бие» на дневен барер връща числа около старите → старите числа са")
print("  от ДРУГА (по-оптимистична) машина, не от друга ГЕОМЕТРИЯ.")
лог("готово")
