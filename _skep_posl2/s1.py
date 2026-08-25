# -*- coding: utf-8 -*-
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, BASE); os.chdir(BASE)
import live_bot as lb
import pandas as pd

import subprocess
print("HEAD =", subprocess.run(["git","rev-parse","--short","HEAD"],capture_output=True,text=True).stdout.strip())

СТАР = 25.515
ИСТИНА = 4647.2 - 4591.465
print(f"замразен={СТАР} истински={ИСТИНА:.3f} скок={ИСТИНА-СТАР:+.2f}$")

idx = pd.date_range("2026-08-21T10:00", periods=12, freq="5min")
bars = pd.DataFrame({"Open":[4647.2]*12,"High":[4648.0]*12,"Low":[4646.4]*12,"Close":[4647.2]*12}, index=idx)

def сделка(вход, посока="long"):
    if посока=="long":
        lv={"sl":round(вход-10,2),"tp1":round(вход+5,2),"tp2":round(вход+10,2),"tp3":round(вход+15,2)}
    else:
        lv={"sl":round(вход+10,2),"tp1":round(вход-5,2),"tp2":round(вход-10,2),"tp3":round(вход-15,2)}
    return {"direction":посока,"entry":round(вход,2),"opened":"2026-08-21T09:55",
            "checked":"2026-08-21T09:59","ledger":"spot","v2":True,"levels":lv,
            "hit":{},"status":"open","tier":"premium","date":"2026-08-21"}

def пусни(t, basis, скок, spot):
    t2, ev = lb.track_trade(dict(t), bars, basis, spot["mid"], "2026-08-21T11:00",
                            spot=spot, скок_базис=скок)
    return [(e[0], e[1], e[3]) for e in ev]

print()
print("### 1 · ТОЧНО фикстурата на находката (вход = бар − ЗАМРАЗЕН базис = %.2f)" % (4647.2-СТАР))
t = сделка(4647.2-СТАР)
spot_стар = {"mid":4647.2-СТАР,"bid":4647.0-СТАР,"ask":4647.4-СТАР}
spot_нов  = {"mid":4647.2-ИСТИНА,"bid":4647.0-ИСТИНА,"ask":4647.4-ИСТИНА}
print("  A· базис не мърда, скок_базис=False :", пусни(t, СТАР, False, spot_стар) or "НЯМА")
print("  B· базис ре-анкерван, скок_базис=False (както твърди находката):", пусни(t, ИСТИНА, False, spot_нов) or "НЯМА")
print("  B'· СЪЩОТО, но както го вика ЖИВИЯТ код: скок_базис=True :", пусни(t, ИСТИНА, True, spot_нов) or "НЯМА")
ts = сделка(4647.2-СТАР, "short")
print("  C· шорт, скок_базис=False :", пусни(ts, ИСТИНА, False, spot_нов) or "НЯМА")
print("  C'· шорт, скок_базис=True :", пусни(ts, ИСТИНА, True, spot_нов) or "НЯМА")
