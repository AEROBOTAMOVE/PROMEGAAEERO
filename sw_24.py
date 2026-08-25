import sys, importlib.util
sys.stdout.reconfigure(encoding='utf-8')
def mod(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
KT=mod("brain/b_карта.py","kt"); SL=mod("brain/b_сливане.py","sl")
# ЦЕЛ НЯМА: V2_цел_наблизо=False, само троен допир в група В
у={к:False for к in SL.ТАБЛИЦА}
у["A1_повод_свип"]=True; у["V1_троен_допир"]=True; у["E1_съгласна"]=True
карта={"всички_условия":у}
print("ЗАЩО (цел НЯМА):", repr(KT._защо(карта, SL.ТАБЛИЦА)))
print("има ли думата «цел» в реда?", "цел" in KT._защо(карта, SL.ТАБЛИЦА))
print("ЧОВЕШКИ['В'] =", repr(KT.ЧОВЕШКИ["В"]))
# и обратното: с цел
у2=dict(у); у2["V2_цел_наблизо"]=True
print("ЗАЩО (цел ИМА):", repr(KT._защо({"всички_условия":у2}, SL.ТАБЛИЦА)))
print("някъде в модула останало ли е «цел наблизо» като човешко име?",
      [v for v in KT.ЧОВЕШКИ.values() if "цел" in v])
