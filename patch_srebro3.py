# -*- coding: utf-8 -*-
"""
F24в · ДВЕ НЕЩА, КОИТО ТЕСТЪТ ОТКРИ

1 · `KeyError: 'net'` — записах клетките само със `_сурово`, а `net` се появява
    чак след `_сребро_разход`. Значи ВСЕКИ, който чете сребърно `net` преди
    корекцията (selftest, одит-роботът, човек с jq), гърми. Файлът трябва да е
    самостоятелен: сега носи и `net`/`lo`/`hi`, пресметнати при подразбирането
    0.03$, а ботът ги ПРЕСМЯТА при живия спред. Кръгът се затваря и без бота.

2 · `ck("О7 среброто НЕ е пипано", ...["fresh"]["net"] == 0.111)` — тест, който
    пази точно числото, което днес се оказа невъзпроизводимо (n=556 срещу
    преизмерени n=1204). ОБРЪЩА СЕ, не се трие: сега пази, че старото число е
    МАХНАТО от решаващия път и е запазено под `_старо` за проверка.
"""
import io, json, ast

# ── 1 · файлът става самостоятелен ───────────────────────────────────────
p = "backtest_stats.json"
st = json.load(io.open(p, encoding="utf-8"))
sv = st["silver"]
ПОДР = 0.03
бр = 0
for d in ("long", "short"):
    for име, а in (sv.get(d) or {}).items():
        if not isinstance(а, dict):
            continue
        сур = а.get("_сурово")
        if not isinstance(сур, dict):
            continue
        for к in ("net", "lo", "hi"):
            if сур.get(к) is not None:
                а[к] = round(float(сур[к]) - ПОДР, 4)
        еп = а.get("_епохи")
        if isinstance(еп, dict):
            з = [float(v) - ПОДР for v in еп.values() if v is not None]
            а["_епохи_съгласни"] = (len(з) < 2 or all(x > 0 for x in з) or all(x < 0 for x in з))
        бр += 1
sv["_подразбиран_спред"] = ПОДР
sv["_как_се_чете"] = ("`net`/`lo`/`hi` тук са СЛЕД разход 0.03$/oz. Суровите (без разход) "
                      "са в `_сурово`. Ботът ги пресмята наново при живия `СРЕБРО_СПРЕД`, "
                      "включително `_епохи_съгласни` — разходът мени присъдата, затова е "
                      "ВЪТРЕ в сметката, не преди нея.")
json.dump(st, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"1 · {бр} сребърни клетки вече носят живи net/lo/hi във файла")

# ── 2 · обръщане на теста ────────────────────────────────────────────────
p2 = "selftest.py"
s = io.open(p2, encoding="utf-8", newline="").read()
СТАРО = 'ck("О7 среброто НЕ е пипано", _bs["silver"]["long"]["fresh"]["net"] == 0.111)'
assert s.count(СТАРО) == 1, f"{s.count(СТАРО)} съвпадения"

НОВО = '''# 🔴 F24 (18.08) · ОБЪРНАТ. Пазеше `silver.long.fresh.net == 0.111` — числото,
# по което ботът ОТВАРЯШЕ сребърни лонгове. Днес се оказа невъзпроизводимо:
# преизмерено на 12858 сделки дава +0.033$ (3.4× по-малко), а съседната клетка
# `stale` беше n=556 срещу преизмерени n=1204. Нито едното няма записан метод
# или интервал. Тестът вече пази ОБРАТНОТО: старото число е махнато от
# решаващия път и е запазено под `_старо` за проверка.
_с24 = _bs["silver"]
ck("F24 старото сребърно число НЕ е вече на решаващия път",
   abs(float(_с24["long"]["fresh"]["net"]) - 0.111) > 0.01)
ck("F24 но е ЗАПАЗЕНО под `_старо` (не е изтрито)",
   abs(float(((_с24.get("_старо") or {}).get("стойности") or {})
             .get("long", {}).get("fresh", {}).get("net", 0)) - 0.111) < 1e-9)
ck("F24 всяка сребърна клетка носи СУРОВО и ЕПОХИ",
   all(isinstance(а.get("_сурово"), dict) and isinstance(а.get("_епохи"), dict)
       for d in ("long", "short") for им, а in _с24[d].items()
       if им in ("day1", "fresh", "mixed", "stale", "ultra")))
ck("F24 живото `net` е СУРОВО минус подразбирания спред",
   all(abs(round(а["_сурово"]["net"] - _с24["_подразбиран_спред"], 4) - а["net"]) < 1e-6
       for d in ("long", "short") for им, а in _с24[d].items()
       if им in ("day1", "fresh", "mixed", "stale", "ultra")))
ck("F24 КЛАСОВИТЕ клетки (premium/weak) са НЕПИПНАТИ",
   _с24["long"].get("premium", {}).get("n") == 926
   and _с24["short"].get("weak", {}).get("n") == 2504)
# 🔴 И ДВЕТЕ ПОСОКИ, в един процес: спирачката трябва да МЕРИ, не да е закована.
_ст24 = _cp.deepcopy(_bs)
lb.СРЕБРО_СПРЕД = 0.03
lb._сребро_разход(_ст24, None)
_отк24 = [lb._advice_entry(d, n, _ст24, False, False, 0, sym="XAGUSD")[1]
          for d in ("long", "short") for n in (0, 1, 2, 5)]
_ев24 = _cp.deepcopy(_bs)
lb.СРЕБРО_СПРЕД = 0.0
lb._сребро_разход(_ев24, None)
_жив24 = [lb._advice_entry(d, n, _ев24, False, False, 0, sym="XAGUSD")[1]
          for d in ("long", "short") for n in (0, 1, 2, 5)]
lb.СРЕБРО_СПРЕД = 0.03
ck("F24 при спред 0.03$ среброто НЕ дава нито един вход", not any(_отк24))
ck("F24 при спред 0.00$ клетките ОЖИВЯВАТ (значи мери, не е заковано)",
   any(_жив24))
ck("F24 сребърният отказ казва ПРИЧИНАТА, не «изчакай»",
   "няма измерен ръб" in lb._advice_entry("long", 1, _ст24, False, False, 0,
                                          sym="XAGUSD")[0])
ck("F24 ЗЛАТОТО не се влияе от сребърния спред",
   [lb._advice_entry(d, n, _ст24, False, False, 0, sym="XAUUSD")[1]
    for d in ("long", "short") for n in (0, 1, 2, 5)]
   == [lb._advice_entry(d, n, _ев24, False, False, 0, sym="XAUUSD")[1]
       for d in ("long", "short") for n in (0, 1, 2, 5)])
ck("F24 `_noise` брои разминаващи се епохи за шум",
   lb._noise({"lo": 0.1, "hi": 0.9, "_епохи_съгласни": False})
   and not lb._noise({"lo": 0.1, "hi": 0.9, "_епохи_съгласни": True})
   and not lb._noise({"lo": 0.1, "hi": 0.9}))'''

s = s.replace(СТАРО, НОВО)
if "import copy as _cp" not in s:
    s = s.replace("import live_bot as lb", "import live_bot as lb\nimport copy as _cp", 1)
    assert "import copy as _cp" in s, "не намерих къде да вкарам copy"
io.open(p2, "wb").write(s.encode("utf-8"))
ast.parse(io.open(p2, encoding="utf-8").read())
print("2 · тестът е ОБЪРНАТ + 10 нови проверки (в двете посоки)")
