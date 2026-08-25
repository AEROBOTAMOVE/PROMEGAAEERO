# -*- coding: utf-8 -*-
import sys, io, json, pathlib
sys.argv=["x"]; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
st = json.loads(open("backtest_stats.json", encoding="utf-8").read())
print("ТОП КЛЮЧОВЕ:", sorted(st.keys()))
mb = st.get("ma_bounce", {})
for d in ("long","short"):
    for m in ("ma50","ma200"):
        print(f"ma_bounce {d}/{m}:", {k: mb[d][m].get(k) for k in ("net","n","lo","hi","шум","win")})
print("хоризонт:", mb.get("_хоризонт_дни"), mb.get("_хоризонт_на_бота_дни"))
print("метод:", str(mb.get("_метод"))[:200])
meta = st.get("_meta", {})
print("_meta ключове:", sorted(meta.keys()))
for k in ("тишина_мерена","НЕпреизмерено","кое_чете_ботът"):
    print(k, "->", json.dumps(meta.get(k), ensure_ascii=False)[:400])
# има ли нещо за пазача/макро щита
s = json.dumps(st, ensure_ascii=False)
for w in ("guard","пазач","щит","shield","cq","събитие","реентри","reentry","ре-влизане","пауза"):
    print(f"търсене «{w}»:", s.count(w))
