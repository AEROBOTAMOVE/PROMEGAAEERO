# -*- coding: utf-8 -*-
"""Стегнато измерване. Индексът на yfinance е НАЧАЛОТО на бара → Close-ът е на
началото+5мин. Строим фючърсна крива по това време, интерполираме до момента на
всеки рън и смятаме базиса ТАМ. После мерим остатъчната грешка честно."""
import sys, io, json, os
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd, numpy as np
D = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(D, "sw_ob41.py"), encoding="utf-8").read().split("def scal(")[0])

F = pd.Series(B["Close"].values, index=B.index + pd.Timedelta(minutes=5)).dropna()
S2 = S[~S.index.duplicated(keep="last")]
# чисти проби: жив спот, небайат бар
чисти = S2[(S2["stale"] != True)].dropna(subset=["pu"])
common = F.reindex(F.index.union(чисти.index)).interpolate(method="time").reindex(чисти.index)
bser = (common - чисти["pu"]).dropna()
# махаме мигове, в които няма фючърсна котировка наблизо (уикенд/пауза)
близо = pd.Series(bser.index, index=bser.index).apply(
    lambda t: (F.index[np.searchsorted(F.index, t).clip(0, len(F.index) - 1)] - t).total_seconds())
bser = bser[близо.abs() <= 360]
print("\nбазис по точно изравнени двойки: n=%d медиана %.2f  стд %.2f" % (len(bser), bser.median(), bser.std()))

BS = bser.rolling("60min").median()
BAS3 = BS.reindex(BS.index.union(B.index)).interpolate(method="time").reindex(B.index)
res = (common - BAS3.reindex(common.index).interpolate() - чисти["pu"].reindex(common.index)).dropna()
res = res[res.index.isin(bser.index)]
print("РЕЗИДУАЛ (грешка на превода бар→спот), n=%d:" % len(res))
for q in (.5, .75, .9, .95, .99):
    print("   |грешка| p%-3d = %.2f$" % (q * 100, res.abs().quantile(q)))
ГР = res.abs().quantile(.95)

def barw(rec, BASX, поле="стоп"):
    зн = 1 if rec["посока"] == "long" else -1
    t0, t1 = pd.Timestamp(rec["отворен"]), pd.Timestamp(rec["затворен"])
    ц1 = False; макс = -9e9
    for ts, r in B.loc[(B.index > t0) & (B.index <= t1)].iterrows():
        bb = float(BASX.loc[ts])
        hi = float(r["High"]) - bb; lo = float(r["Low"]) - bb
        if pd.isna(hi) or pd.isna(lo):
            continue
        d = (rec["стоп"] - lo) if зн == 1 else (hi - rec["стоп"])
        макс = max(макс, d)
        if d >= 0:
            return ("стоп", ts, d)
        if rec.get("цел2") is not None and ((hi >= rec["цел2"]) if зн == 1 else (lo <= rec["цел2"])):
            return ("цел2", ts, макс)
        if not ц1 and ((hi >= rec["цел1"]) if зн == 1 else (lo <= rec["цел1"])):
            ц1 = True
    return (None, None, макс)

print("\nпраг «истинско пробиване» = p95 на грешката = %.2f$\n" % ГР)
print("%-3s %-5s %-17s %-6s %9s | %-6s %-17s %9s %s" %
      ("№", "пос", "отворен", "запис", "резултат", "по бар", "кога", "проникв.", "присъда"))
жив = сив = 0
for i, rec in enumerate(R, 1):
    k, ts, d = barw(rec, BAS3)
    ин = ""
    if k != rec["изход"]:
        if d >= ГР:
            ин = "⚠⚠ РЕАЛНА РАЗЛИКА"; жив += 1
        else:
            ин = "~ в шума (%.2f < %.2f)" % (d, ГР); сив += 1
    print("%-3d %-5s %-17s %-6s %+9.2f | %-6s %-17s %+9.2f %s"
          % (i, rec["посока"], rec["отворен"], rec["изход"], rec["резултат"],
             str(k), str(ts)[:16], d, ин))
print("\nРАЗЛИКИ НАД ГРЕШКАТА: %d/%d      разлики в шума: %d/%d" % (жив, len(R), сив, len(R)))

# --- колко се движи цената МЕЖДУ две проби (това е целият прозорец на дефекта) ---
пр = чисти["pu"]
раз = []
for a, b in zip(пр.index[:-1], пр.index[1:]):
    if (b - a).total_seconds() > 20 * 60:
        continue
    w = B.loc[(B.index >= a.floor("5min")) & (B.index <= b)]
    if w.empty:
        continue
    bb = BAS3.reindex(w.index)
    lo = (w["Low"] - bb).min(); hi = (w["High"] - bb).max()
    p0, p1 = пр.loc[a], пр.loc[b]
    раз.append((min(p0, p1) - lo, hi - max(p0, p1)))
раз = pd.DataFrame(раз, columns=["надолу", "нагоре"]).dropna()
print("\nСКРИТА ЕКСКУРЗИЯ между две съседни проби (n=%d), $ отвъд по-лошата проба:" % len(раз))
for q in (.5, .9, .99):
    print("   надолу p%-3d %.2f$   нагоре p%-3d %.2f$"
          % (q * 100, раз["надолу"].quantile(q), q * 100, раз["нагоре"].quantile(q)))
print("   дял с екскурзия > 1.00$ (над грешката): надолу %.1f%%  нагоре %.1f%%"
      % (100 * (раз["надолу"] > 1).mean(), 100 * (раз["нагоре"] > 1).mean()))
