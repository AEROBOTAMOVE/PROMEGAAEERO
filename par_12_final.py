# -*- coding: utf-8 -*-
import sys, io, json
sys.argv=["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import live_bot as lb
spot={"bid":4399.5,"ask":4400.1,"mid":4399.8,"src":"swq"}

print("=== A · ОДИТ-68 бележката НЕ стига до дневника (3 места) ===")
# сделка, при която стълбата гърми: hit има tp1, но levels няма tp1
bad={"direction":"long","entry":4400.0,"levels":{"sl":4380.0},"hit":{"tp1":True},"sym":"XAUUSD"}
n=[]
print("  директно с notes:", lb._отворена_стълба(bad, spot, n), "→ бележки:", len(n), n)
m=lb._status_msg([], "long", bad, None, spot, None, 9.0, 0.2, {}, False, "2026-08-18", {})
print("  през _status_msg (подава `notes if 'notes' in dir() else None`):")
print("   ", [x for x in m.split("\n") if "покупка" in x])
print("    → картата е без число, бележка НЯМА КЪДЕ да отиде (изразът винаги е None)")

print("\n=== Б · guard-етикетът в «КЪДЕ СМЕ» бърка посока И метал ===")
for g,очаквано in (({"long":2},"злато ПОКУПКИ"),({"s_long":2},"сребро ПОКУПКИ"),({"s_short":2},"сребро ПРОДАЖБИ")):
    m=lb._status_msg([], "long", None, None, spot, None, 9.0,0.2, g, False,"2026-08-18",{})
    ред=[x for x in m.split("\n") if "спрени днес" in x]
    print("  guard=%-16s истина=%-16s картата казва: %s"%(json.dumps(g),очаквано,ред[0] if ред else "—"))

print("\n=== В · _digest_msg брои и сребърните стопове, но БЕЗ етикет ===")
import inspect
print("  ред 1806:", [l.strip() for l in inspect.getsource(lb._digest_msg).split("\n") if "стопове" in l][:2])

print("\n=== Г · _пари: подписът е метал-осъзнат, но 1 повикване е без метал ===")
print("  _пари(-0.47) [подразбира ЗЛАТО] =", lb._пари(-0.47))
print("  _пари(-0.47,'XAGUSD')          =", lb._пари(-0.47,"XAGUSD"))
print("  (в _защо_мълчи се цитира ЗЛАТНА клетка → подразбирането е вярно)")
