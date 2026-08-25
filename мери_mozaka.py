# -*- coding: utf-8 -*-
"""
ИЗМЕРВАНЕ · РАБОТИ ЛИ ЛОГИКАТА ОТ ИНДИКАТОРА  (втора версия, поправена)

ПЪРВАТА МИ ВЕРСИЯ ДАДЕ +686$ И 59% ПЕЧЕЛИВШИ. БЕШЕ БОКЛУК.
Причина: `brain_journal.jsonl` пази нивата на ФЮЧЪРСНА скала, а `spot` в
`live_journal.jsonl` е спот. Разлика: медиана +59.55$ (мин +50.84, макс +69.49).
Сравнявал съм ябълки с круши. Хванах го, защото входовете бяха 4445–4453, а
цената в периода не е минавала над 4414 — числото не можеше да е вярно.

ПОПРАВЕНО ТУК:
· всяко ниво се сваля с базиса, измерен В СЪЩИЯ МОМЕНТ (полето `basis`)
· броят се и НЕЗАВИСИМИТЕ наблюдения: 80 от 88 се припокриват във времето с
  предишно от същата рамка+посока, значи гледат едно и също движение

ГРАНИЦИ (важат за всяко число долу):
· пробата е на ~5 мин. Стоп и цел в един интервал = «неясен», брои се отделно.
· цената е mid, без спред. Реалният резултат е по-лош.
· входът се приема незабавно на нивото, както прави живото следене.
· 17 часа са малко. Това е ПОСОКА, не присъда.
"""
import json, io, collections, datetime as dt, statistics

ЧАСОВЕ = 4.0

б = [json.loads(l) for l in io.open("live/brain_journal.jsonl", encoding="utf-8") if l.strip()]
r = [json.loads(l) for l in io.open("live/live_journal.jsonl", encoding="utf-8") if l.strip()]
цени = sorted((dt.datetime.fromisoformat(x["run_utc"]), float(x["spot"]))
              for x in r if x.get("spot"))
базис = sorted((dt.datetime.fromisoformat(x["run_utc"]), float(x["basis"]))
               for x in r if x.get("basis") is not None)

РЕД = ("✨ ИСКРА", "👀 НАБЛЮДЕНИЕ", "🔨 ОФОРМЯ СЕ", "✅ ГОТОВ",
       "🔥 СИЛЕН", "⚡ МНОГО СИЛЕН", "💎 РЯДЪК")


def _базис_в(t):
    б_ = min(базис, key=lambda q: abs((q[0] - t).total_seconds()))
    return б_[1] if abs((б_[0] - t).total_seconds()) <= 900 else None


def развръзка(к):
    try:
        т0 = dt.datetime.fromisoformat(к["utc"])
        изм = _базис_в(т0)
        if изм is None:
            return None
        вх = float(к["вход"]) - изм
        ст = float(к["стоп"]) - изм
        це = float(к["цел"]) - изм
    except Exception:
        return None
    лонг = str(к.get("посока", "")).upper() in ("LONG", "ЛОНГ")
    сл = [(t, p) for t, p in цени if t > т0 and (t - т0).total_seconds() <= ЧАСОВЕ * 3600]
    if not сл:
        return None
    for t, p in сл:
        уд_ст = (p <= ст) if лонг else (p >= ст)
        уд_це = (p >= це) if лонг else (p <= це)
        if уд_ст and уд_це:
            return ("неясен", 0.0, (t - т0).total_seconds() / 60, лонг)
        if уд_ст:
            return ("стоп", -abs(вх - ст), (t - т0).total_seconds() / 60, лонг)
        if уд_це:
            return ("цел", +abs(це - вх), (t - т0).total_seconds() / 60, лонг)
    if (сл[-1][0] - т0).total_seconds() < ЧАСОВЕ * 3600 * 0.8:
        return None
    п = (сл[-1][1] - вх) if лонг else (вх - сл[-1][1])
    return ("изтекло", п, (сл[-1][0] - т0).total_seconds() / 60, лонг)


рез = [(к, d) for к, d in ((к, развръзка(к)) for к in б) if d]
ясни = [(к, d) for к, d in рез if d[0] != "неясен"]

# ── независимите: по едно наблюдение на рамка+посока, без припокриване ────
незав = []
зает = collections.defaultdict(lambda: dt.datetime.min)
for к, d in sorted(ясни, key=lambda x: x[0]["utc"]):
    t = dt.datetime.fromisoformat(к["utc"])
    ключ = (к.get("рамка"), к.get("посока"))
    if t >= зает[ключ]:
        незав.append((к, d))
        зает[ключ] = t + dt.timedelta(minutes=d[2])


def отчет(име, г):
    if not г:
        print(f"  {име}: няма"); return
    п = sum(d[1] for _, d in г)
    w = sum(1 for _, d in г if d[1] > 0)
    print(f"  {име:24s} {len(г):4d} · {w}/{len(г)} = {w/len(г)*100:3.0f}% печеливши · "
          f"средно {п/len(г):+7.2f}$ · общо {п:+9.2f}$")


print("=" * 78)
print(f"ЛОГИКАТА ОТ ИНДИКАТОРА · {len(ясни)} развръзки от {len(б)} кандидата")
print("=" * 78)
print("  изходи: " + " · ".join(f"{k} {v}" for k, v in
                                collections.Counter(d[0] for _, d in рез).most_common()))
print()
отчет("ВСИЧКИ (припокриващи)", ясни)
отчет("НЕЗАВИСИМИ", незав)
print("\n  ⚠️ «всички» брои едно движение по няколко пъти. Тежи «независими».")

print("\n" + "=" * 78)
print("ПО СТЕПЕН · по-силното по-добро ли е (само НЕЗАВИСИМИ)")
print("=" * 78)
for с in РЕД:
    отчет(с, [(к, d) for к, d in незав if к.get("степен") == с])

print("\n" + "=" * 78)
print("ПО РАМКА (независими)")
print("=" * 78)
for f in ("1мин", "5м", "15м"):
    г = [(к, d) for к, d in незав if к.get("рамка") == f]
    отчет(f, г)
    if г:
        изм = [_базис_в(dt.datetime.fromisoformat(к["utc"])) or 0 for к, _ in г]
        ст = [abs(float(к["вход"]) - float(к["стоп"])) for к, _ in г]
        print(f"      среден стоп {statistics.mean(ст):5.2f}$")

print("\n" + "=" * 78)
print("ПО ПОСОКА (независими) · пазарът се качи +12.55$ в периода")
print("=" * 78)
отчет("ЛОНГ", [(к, d) for к, d in незав if d[3]])
отчет("КЪСО", [(к, d) for к, d in незав if not d[3]])

print("\n" + "=" * 78)
print("ФИЛТРИТЕ НА БОТА ПОМАГАТ ЛИ (независими)")
print("=" * 78)
отчет("ПРАТЕНИ от бота", [(к, d) for к, d in незав if к.get("праща")])
отчет("непратени", [(к, d) for к, d in незав if not к.get("праща")])
