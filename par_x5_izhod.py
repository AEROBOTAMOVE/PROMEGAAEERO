import sys,json,io,re
sys.argv=["x"]; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import live_bot as lb
strip=lambda s: re.sub(r"<[^>]+>","",s)
base={"direction":"long","entry":4358.00,"opened":"2026-08-11T09:00",
      "levels":{"tp1":4365.50,"tp2":4370.00,"tp3":4378.00,"sl":4338.00},"hit":{},"sym":"XAUUSD"}
def тест(име,tr,kind,px,gap=False):
    print("### "+име)
    print("РЕАЛНА:"); print(strip(lb._exit_msg(kind,tr,px,"2026-08-18T10:00","бар",gap)))
    print("СЯНКА:");  print(strip(lb._shadow_exit_msg(kind,tr,px,"2026-08-18T10:00","бар",gap)))
    print()
import copy
t=copy.deepcopy(base); тест("ТП1",t,"tp1",4365.50)
t=copy.deepcopy(base); t["hit"]={"tp1":True}; t["levels"]["sl"]=4358.00
тест("СТОП на входа след ТП1",t,"sl",4358.00)
t2=copy.deepcopy(base); t2["hit"]={"tp1":True,"tp2":True}; t2["levels"]["sl"]=4358.00
тест("СТОП на входа след ТП1+ТП2",t2,"sl",4358.00)
t3=copy.deepcopy(base); тест("СТОП чист",t3,"sl",4338.00,gap=True)
t4=copy.deepcopy(base); t4["hit"]={"tp1":True,"tp2":True}; тест("ТП3",t4,"tp3",4378.00)
t5=copy.deepcopy(base); t5["hit"]={"tp1":True}; тест("ТП2",t5,"tp2",4370.00)
t6=copy.deepcopy(base); t6["hit"]={"tp1":True}; t6["levels"]["sl"]=4358.0
тест("ВРЕМЕ след ТП1",t6,"time",4360.00)
