import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
sys.path.insert(0,'brain')
import b_сливане as SL
print("len(ТАБЛИЦА)=",len(SL.ТАБЛИЦА))
групи=sorted(set(k[0] for k in SL.ТАБЛИЦА))
print("групи по префикс:",групи,len(групи))
for k,v in SL.ТАБЛИЦА.items(): print("  ",k,v)
try:
    import b_карта as KT
    print("ГРУПИ_ИМЕ:",KT.ГРУПИ_ИМЕ)
except Exception as e: print("карта:",e)
