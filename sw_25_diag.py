# -*- coding: utf-8 -*-
import sys, numpy as np, pandas as pd
sys.argv=["x"]; import live_bot as lb
sys.stdout.reconfigure(encoding='utf-8')
CB = lb.CB
n=400
idx=pd.date_range("2026-08-01", periods=n, freq="15min")
rng=np.random.default_rng(7)
c=2400+np.cumsum(rng.normal(0,1.5,n))
df=pd.DataFrame({"Open":c,"High":c+2,"Low":c-2,"Close":c,"Volume":1000.0},index=idx)
# счупваме един блок — b_зони гърми

_ор=CB.B4.f_зони
CB.B4.f_зони=lambda d,**k: (_ for _ in ()).throw(ValueError("тестов гърмеж"))
setups,diag=CB.сканирай({"15м":df}, сега=pd.Timestamp("2026-08-05"),
                        състояние={}, работни=("15м",), праг=9, върни_диагностика=True)
CB.B4.f_зони=_ор
print("сетъпи:",len(setups))
print("грешки:",diag["грешки"])
# ИЗПЪЛНЯВАМЕ реалния текст на live_bot (редовете с бележката)
src=open("live_bot.py",encoding="utf-8").read().splitlines()
блок="\n".join(src[3627:3642])
print("--- изпълняван текст от live_bot.py 3628-3642 ---")
print(блок)
notes=[]
g={"notes":notes,"_диаг":diag,"len":len,"sorted":sorted,"str":str,"list":list,"type":type,"Exception":Exception}
exec("\n".join(l[12:] for l in блок.splitlines()), g)
print("--- notes ---"); [print(" ",x) for x in notes]
