# -*- coding: utf-8 -*-
"""Колко точна е моята бар→спот конверсия? Ако грешката е ±1$, «дълбочина 0.55$»
не доказва нищо. Мери се РЕЗИДУАЛЪТ: (Close на бара − базис) срещу живия спот."""
import sys, io, json, os
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd, numpy as np
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sw_ob41.py"),
          encoding="utf-8").read().split("def scal(")[0])

# резидуал: за всеки рън вземи бара, който ГО СЪДЪРЖА, и сравни Close−базис със спота
res = []
for ts, r in S.iterrows():
    b_ts = ts.floor("5min")
    if b_ts in B.index and not pd.isna(B.loc[b_ts, "Close"]) and not pd.isna(bas.get(b_ts, np.nan)):
        res.append(float(B.loc[b_ts, "Close"]) - float(bas.loc[b_ts]) - float(r["pu"]))
res = pd.Series(res)
print("\nРЕЗИДУАЛ (бар−базис) − спот, %d двойки:" % len(res))
print("  медиана %+.2f  стд %.2f  |резидуал| p50 %.2f  p90 %.2f  p99 %.2f  макс %.2f"
      % (res.median(), res.std(), res.abs().median(), res.abs().quantile(.9),
         res.abs().quantile(.99), res.abs().max()))
print("  дял |резидуал| > 0.55$: %.1f%%   > 0.85$: %.1f%%"
      % (100 * (res.abs() > 0.55).mean(), 100 * (res.abs() > 0.85).mean()))

# приближение отблизо на №8 и №9
for rec, лаб in [(R[7], "№8 14.08 long"), (R[8], "№9 17.08 long")]:
    t0 = pd.Timestamp(rec["отворен"]); t1 = pd.Timestamp(rec["затворен"])
    print("\n--- %s  вход %.2f стоп %.2f цел2 %.2f  (записан изход %s %+.2f) ---"
          % (лаб, rec["вход"], rec["стоп"], rec["цел2"], rec["изход"], rec["резултат"]))
    sub = B.loc[(B.index > t0) & (B.index <= min(t1, t0 + pd.Timedelta(hours=3)))]
    lo_spot = sub["Low"] - bas.reindex(sub.index)
    к = lo_spot.idxmin()
    print("  най-ниският спот-Low по барове: %.2f в %s (стоп %.2f → под стопа с %.2f$)"
          % (lo_spot.min(), к, rec["стоп"], rec["стоп"] - lo_spot.min()))
    print("  базис в този миг: %.2f  (базис ±0.5ч: мин %.2f макс %.2f)"
          % (bas.loc[к], bas.loc[(bas.index >= к - pd.Timedelta(minutes=30)) &
                                 (bas.index <= к + pd.Timedelta(minutes=30))].min(),
             bas.loc[(bas.index >= к - pd.Timedelta(minutes=30)) &
                     (bas.index <= к + pd.Timedelta(minutes=30))].max()))
    ок = S.loc[(S.index >= к - pd.Timedelta(minutes=20)) & (S.index <= к + pd.Timedelta(minutes=20))]
    print("  ЖИВИТЕ спот-проби на бота около този миг (стоп %.2f):" % rec["стоп"])
    for ts, r in ок.iterrows():
        bt = ts.floor("5min")
        bl = (float(B.loc[bt, "Low"]) - float(bas.loc[bt])) if bt in B.index else float("nan")
        print("     %s  спот %.2f   (спот-Low на бара му: %.2f)  %s"
              % (ts, r["pu"], bl, "⬅ ПОД СТОПА по бар" if bl <= rec["стоп"] else ""))
