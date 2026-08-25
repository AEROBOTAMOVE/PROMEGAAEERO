# -*- coding: utf-8 -*-
import json, collections
r = json.load(open("sw_z_probe.json", encoding="utf-8"))
N = len(r)
print("моменти:", N)

# 1 · главен прозорец срещу водеща на 7-те хоризонта
разл = sum(1 for x in r if x["главен"] != x["водеща"])
print(f"\n[1] главен['състояние'] != съгласие['водеща']: {разл}/{N} = {разл/N:.1%}")
c = collections.Counter((x["главен"], x["водеща"]) for x in r if x["главен"] != x["водеща"])
for k, v in c.most_common(6):
    print("    главен=%-11s водеща=%-11s %d" % (k[0], k[1], v))

# 2 · Z1 / Z2 / Z2b за ДВЕТЕ посоки, точно както ги смята _брои
редове = []
for x in r:
    for лонг in (True, False):
        искана = "ДИСКАУНТ" if лонг else "ПРЕМИУМ"
        вс = (x["водеща"] == искана)
        z1 = (x["посока"] == искана)
        z2 = вс and x["мнозинство"] >= 5
        z2b = вс and x["единодушно"]
        z3 = x["изм_долу"] if лонг else x["изм_горе"]
        редове.append((z1, z2, z2b, z3))
M = len(редове)
p = lambda f: sum(1 for q in редове if f(q))
print(f"\n[2] посока-моменти (2 на бар): {M}")
print(f"    Z1 пали                : {p(lambda q:q[0])}/{M} = {p(lambda q:q[0])/M:.1%}")
print(f"    Z2 пали                : {p(lambda q:q[1])}/{M} = {p(lambda q:q[1])/M:.1%}")
print(f"    Z2b пали               : {p(lambda q:q[2])}/{M} = {p(lambda q:q[2])/M:.1%}")
print(f"    Z3 пали                : {p(lambda q:q[3])}/{M} = {p(lambda q:q[3])/M:.1%}")
n1 = p(lambda q:q[0])
print(f"\n    Z1 без Z2  (само 1 т.) : {p(lambda q:q[0] and not q[1])}/{n1} = {p(lambda q:q[0] and not q[1])/n1:.1%} от Z1")
print(f"    Z1+Z2 без Z2b (2 т.)   : {p(lambda q:q[0] and q[1] and not q[2])}/{n1} = {p(lambda q:q[0] and q[1] and not q[2])/n1:.1%} от Z1")
print(f"    Z1+Z2+Z2b (3 т.)       : {p(lambda q:q[2])}/{n1} = {p(lambda q:q[2])/n1:.1%} от Z1")

# 3 · разпределение на точките в група З (тегла 1, таван 4)
разпр = collections.Counter(sum(q) for q in редове)
print("\n[3] точки в група З (без таван — таванът е 4, макс тук е 4):")
for k in sorted(разпр):
    print(f"    {k} точки: {разпр[k]:5d}  {разпр[k]/M:6.1%}")
ср = sum(sum(q) for q in редове)/M
print(f"    средно: {ср:.3f} точки")

# 4 · нарушава ли се таванът някога
print(f"\n[4] случаи със сбор в З > ТАВАН_ГРУПА['З']=4: {sum(1 for q in редове if sum(q)>4)}")

# 5 · «алтернативният» Z1 = позицията в ГЛАВНИЯ прозорец
разл2 = 0
for x in r:
    for лонг in (True, False):
        искана = "ДИСКАУНТ" if лонг else "ПРЕМИУМ"
        if (x["посока"] == искана) != (x["главен"] == искана):
            разл2 += 1
print(f"[5] Z1(водеща) != Z1(главен прозорец): {разл2}/{M} = {разл2/M:.1%}")
