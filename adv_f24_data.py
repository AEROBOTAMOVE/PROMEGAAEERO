# -*- coding: utf-8 -*-
"""adv · КАЧЕСТВОТО НА СРЕБЪРНАТА ЛЕНТА ПО ГОДИНИ — и дали «епохите» са артефакт от данните"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

D = "C:/Users/User/Downloads/ЛОЦО/f6_data"
d = pd.read_csv(f"{D}/silver_yahoo_full.csv")
c = [x for x in d.columns if x.lower() in ("date", "datetime")][0]
d[c] = pd.to_datetime(d[c], errors="coerce")
d = d.dropna(subset=[c]).set_index(c).sort_index()
print("КОЛОНИ:", list(d.columns))
s = d[["Open", "High", "Low", "Close"]].apply(pd.to_numeric, errors="coerce").dropna()
vol = pd.to_numeric(d.get("Volume"), errors="coerce").reindex(s.index) if "Volume" in d.columns else None

s["rng"] = s["High"] - s["Low"]
s["нулев"] = s["rng"] == 0
s["близо0"] = s["rng"] < 0.02
s["c_извън"] = (s["Close"] > s["High"]) | (s["Close"] < s["Low"])
s["truerng"] = np.maximum(s["High"], s["Close"].shift(1)) - np.minimum(s["Low"], s["Close"].shift(1))
s["год"] = s.index.year

print("=" * 100)
print("КАЧЕСТВО НА ДНЕВНИТЕ БАРОВЕ ПО ГОДИНИ")
print("=" * 100)
print(f"  {'год':>5s} {'дни':>5s} {'H==L':>7s} {'H-L<0.02':>9s} {'C извън HL':>11s} "
      f"{'медиана H-L':>12s} {'медиана |ΔC|':>13s} {'цена':>8s} {'H-L/цена%':>10s} {'обем=0':>7s}")
for y, g in s.groupby("год"):
    dc_ = g["Close"].diff().abs().median()
    v0 = int((vol.reindex(g.index) == 0).sum()) if vol is not None else -1
    print(f"  {y:5d} {len(g):5d} {g['нулев'].mean()*100:6.1f}% {g['близо0'].mean()*100:8.1f}% "
          f"{g['c_извън'].sum():11d} {g['rng'].median():12.4f} {dc_:13.4f} "
          f"{g['Close'].median():8.2f} {g['rng'].median()/g['Close'].median()*100:9.2f}% {v0:7d}")

print()
print("=" * 100)
print("КЛЮЧОВОТО: истинската дневна подвижност срещу ЗАПИСАНИЯ диапазон")
print("=" * 100)
print("  Ако барът е истински, H-L трябва да е ПО-ГОЛЯМО от |затваряне-затваряне|.")
print(f"  дни, в които H-L < |ΔClose| (физически невъзможно за истински бар): "
      f"{int((s['rng'] < s['Close'].diff().abs()).sum()):,} от {len(s):,} = "
      f"{(s['rng'] < s['Close'].diff().abs()).mean()*100:.1f}%")
пред = s[s.index < "2013-01-01"]; след = s[s.index >= "2013-01-01"]
for им, g in (("2000-2012", пред), ("2013-2026", след)):
    лош = (g["rng"] < g["Close"].diff().abs())
    print(f"    {им}: {лош.mean()*100:5.1f}% лоши барове · H==L {g['нулев'].mean()*100:5.1f}% · "
          f"медиана H-L {g['rng'].median():.4f}$ · медиана |ΔC| {g['Close'].diff().abs().median():.4f}$")
print()
print("  → ако лошите барове са в РАЗЛИЧЕН дял в двете епохи, «смяната на знака» може да е")
print("    свойство на ДАННИТЕ, а не на пазара.")
