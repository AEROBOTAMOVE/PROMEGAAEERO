# -*- coding: utf-8 -*-
"""№37: пулсът показва ли ГОЛАТА разлика на реда с прибраните трети?"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8'); sys.argv=["x"]
import live_bot as lb

# сделка: вход 4000, ТП1 и ТП2 ВЕЧЕ прибрани, стопът е върнат на входа,
# живата цена се е върнала точно на входа → ГОЛАТА разлика = 0.00$
tr = {"direction":"long","entry":4000.0,"sym":"XAUUSD",
      "levels": lb._levels(4000.0,"long"),
      "hit": {"tp1": True, "tp2": True}, "status":"open"}
spot = {"mid":4000.0,"bid":3999.9,"ask":4000.1}
print("нива:", tr["levels"])
голо = (spot["mid"]-tr["entry"])*1
print("ГОЛА разлика (изход−вход) =", round(голо,2))
print("_отворена_стълба ->", lb._отворена_стълба(tr, spot))

board=[("1ден","long",5,"medium","СРЕДЕН")]
txt = lb._pulse_msg("09", board, board[-1], "long","x",False, tr, None,
                    spot, None, {"долар":True,"лихви":True}, False, False,
                    macro_raw={"долар":0.0145,"лихви":0.07}, streaks={"long":3})
plain = re.sub(r"<[^>]+>","",txt)
print("---- ПУЛС ----"); print(plain)
ред = [r for r in plain.splitlines() if "държим от" in r][0]
print("---- РЕДЪТ ----"); print(ред)
print("показва ли +0.00$ (голото)?", "+0.00$" in ред)
m = re.search(r"([+-]\d+\.\d\d)\$", ред)
print("числото на картата:", m.group(1) if m else None)
