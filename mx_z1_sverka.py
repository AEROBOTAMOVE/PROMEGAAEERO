# -*- coding: utf-8 -*-
"""СВЕРКА: новите карти минават ли П25 и стил.py (с вдигнат таван)."""
import sys, re, importlib.util
sys.stdout.reconfigure(encoding="utf-8"); sys.argv = ["x"]
import mx_z1_nov as N
import live_bot as lb

сп = importlib.util.spec_from_file_location("стил", "стил.py")
ст = importlib.util.module_from_spec(сп); сп.loader.exec_module(ст)

# точните проверки на П25 (преписани от selftest.py:4834-4969)
_ЖАРГОН25 = ((r"\bкофа\b",), (r"\bстрийк\b",), (r"\bбазис\b",), (r"\bсегмент\b|\bклетка\b",),
             (r"\bУЛТРА\b",), (r"\bпремиум\b",), (r"\bflip\b|\bранг\b",),
             (r"\bday1\b|\bmixed\b|\bstale\b|\bfresh\b",), (r"n=\d",),
             (r"95%\s*[:(]|доверителн",), (r"vol_rank|adv_ok|should_sig|_meta",), (r"\bTP\d\b",))
_РЕЧНИК25 = set("🟢🔴⏸👁👀🎯🛑💰💵📏📈📉✅🏆⚠📌📅☀🌤🌙🥇🥈🤖🔥✨🔨⚡💎🧠😴🧪♻🌡💪👍🪶🍃")
_ЦИФРИ25 = ("1️⃣", "2️⃣", "3️⃣")
_ЕМО25 = re.compile("[\U0001F300-\U0001FAFF]|[☀-➿]|[⏩-⏺]|ℹ")
_ПУНКТ25 = set("─→·−≈×✓✗▰▱✔✖")
_ДЕЙСТВИЕ25 = ("влез", "премести", "дръж", "чакам", "не влизам", "нищо", "затвор", "следя",
               "прибран", "почивай", "остава", "остават", "спи", "не отварям", "не се прави",
               "само знак", "не съм влизал", "пиша щом", "купи", "продай", "вход")

now = "2026-08-21T11:20:00"
sg = {"mid": 4365.20, "src": "twelve"}; ss = {"mid": 65.150, "src": "twelve"}
tr = {"direction": "long", "entry": 4358.00, "sym": "XAUUSD", "opened": "2026-08-19T09:00:00",
      "levels": {"tp1": 4365.50, "tp2": 4370.00, "tp3": 4378.00, "sl": 4358.00},
      "hit": {"tp1": True, "tp2": True}}
brd = [("H1", "long", 3, "A")] * 7
кавга = {"долар": 0.0031, "лихви": -0.02}; едно = {"долар": 0.0031, "лихви": 0.02}
import pathlib, tempfile, json
tmp = pathlib.Path(tempfile.mkdtemp(prefix="mxz1s_"))
with (tmp / "live_journal.jsonl").open("w", encoding="utf-8") as fh:
    for h in range(3, 19):
        fh.write(json.dumps({"date": "2026-08-21", "run_utc": f"2026-08-21T{h:02d}:07:00"}) + "\n")
with (tmp / "sent_log.jsonl").open("w", encoding="utf-8") as fh:
    for t in ("signal", "exit:tp1", "exit:tp2"):
        fh.write(json.dumps({"utc": "2026-08-21T09:00:00", "tag": t, "text": "x"}) + "\n")

К = {
 "КЪДЕ СМЕ пълна": N.нов_status(brd, "long", tr, None, sg, ss,
                                {"long": 2, "short": 0, "s_long": 0, "s_short": 0}, True, now, N.stats),
 "КЪДЕ СМЕ празна": N.нов_status([], None, None, None, sg, ss, {}, False, now, N.stats),
 "КЪДЕ СМЕ сребърен пазач": N.нов_status([], None, None, None, sg, ss,
                                {"long": 0, "short": 0, "s_long": 2, "s_short": 0}, False, now, N.stats),
 "КЪДЕ СМЕ без цена": N.нов_status(brd, "long", tr, None, None, None, {}, False, now, N.stats),
 "ПУЛС 09 кавга": N.нов_pulse("09", brd, "long", None, None, sg, ss, False, кавга, {"long": 3}, N.stats, "2026-08-21T06:00:00"),
 "ПУЛС 09 шорт кавга": N.нов_pulse("09", brd, "short", None, None, sg, ss, False, кавга, {"short": 2}, N.stats, "2026-08-21T06:00:00"),
 "ПУЛС 14 подредено": N.нов_pulse("14", brd, "long", tr, None, sg, ss, False, едно, {"long": 3}, N.stats, "2026-08-21T11:00:00"),
 "ПУЛС 22 нощта": N.нов_pulse("22", brd, "long", tr, None, sg, ss, False, едно, {"long": 3}, N.stats, "2026-08-21T19:00:00"),
 "ПУЛС мъртво макро": N.нов_pulse("09", brd, None, None, None, sg, ss, False, {}, {}, N.stats, "2026-08-21T06:00:00"),
 "РАВНОСМЕТКА сделка": N.нов_digest(tmp, "2026-08-21", tr, None, sg, ss, {"long": 2}, "2026-08-21T18:05:00"),
 "РАВНОСМЕТКА петък": N.нов_digest(tmp, "2026-08-21", None, None, sg, ss, {}, "2026-08-21T18:05:00", weekly_part=True),
 "БОТЪТ СПА делник": N.нов_спал(lb._търговски_минути("2026-08-21T06:13:00", "2026-08-21T09:20:00"),
                                "2026-08-21T06:13:00", "2026-08-21T09:20:00", True),
 "БОТЪТ СПА през затваряне": N.нов_спал(lb._търговски_минути("2026-08-21T19:00:00", "2026-08-22T02:00:00"),
                                "2026-08-21T19:00:00", "2026-08-22T02:00:00", False),
 "УИКЕНД събота": N.нов_weekend("сутрин", "2026-08-22", "2026-08-22T07:15:00"),
 "УИКЕНД неделя вечер": N.нов_weekend("вечер", "2026-08-23", "2026-08-23T18:00:00"),
}

лоши = 0
макс_р = макс_з = 0
for име, т in К.items():
    ч = ст.чист(т)
    р = [x for x in ч.split("\n") if x.strip()]
    макс_р = max(макс_р, len(р)); макс_з = max(макс_з, len(ч))
    f = []
    if len(р) > 15: f.append(f"над 15 реда ({len(р)})")
    if len(ч) > 1100: f.append(f"над 1100 знака ({len(ч)})")
    п = р[0]
    if not _ЕМО25.match(п.strip()): f.append("първи ред не почва с емоджи")
    if not re.search(r"\d{1,2}:\d{2}", п): f.append("първи ред без час")
    if len(п) > 70: f.append(f"първи ред {len(п)} знака (таван 70)")
    for (изр,) in _ЖАРГОН25:
        m = re.search(изр, ч)
        if m: f.append(f"жаргон «{m.group(0)}»")
    чужди = sorted({z for z in _ЕМО25.findall(ч) if z not in _РЕЧНИК25 and z not in _ПУНКТ25})
    if чужди: f.append(f"емоджи извън речника {чужди}")
    дв = [m.group(0) for m in re.finditer("(?:[\U0001F300-\U0001FAFF☀-➿⏩-⏺]️?\\s?){2,}", ч)
          if not any(c in m.group(0) for c in _ЦИФРИ25)]
    if дв: f.append(f"две емоджита едно до друго {дв[:1]}")
    if not any(d in ч.lower() for d in _ДЕЙСТВИЕ25): f.append("не казва какво да правя")
    for x in ст.провери(име, т, макс_редове=15):
        if x[0] not in ("дълга",) and "не е в речника" not in x[1]:
            f.append(f"стил {x}")
    if f:
        лоши += 1
        print(f"🔸 {име}: {f}")
    else:
        print(f"   {име}: ✓")
print()
print(f"══ {len(К)-лоши}/{len(К)} чисти · най-дълга {макс_р} реда · {макс_з} знака ══")
print()
print("ЕДИНСТВЕНОТО НОВО ЕМОДЖИ, което трябва да влезе в двата речника:")
всички = set()
for т in К.values():
    всички |= {z for z in _ЕМО25.findall(ст.чист(т))}
print("  ", sorted(всички - _РЕЧНИК25 - _ПУНКТ25))
print("  ↳ (U+21B3) хваща ли се от някой проверчик:",
      bool(_ЕМО25.search("↳")), bool(ст.ЕМОДЖИ.search("↳")))
print()
print("ЗАГЛАВИЯТА (първи редове) — уникални ли са:")
пър = [ст.чист(т).split("\n")[0].split(" · ")[0] for т in К.values()]
for x in sorted(set(пър)):
    print("   ", x)

print()
print("### ВСЯКА НОВА КАРТА ИМА ЛИ РЕД С 👉 (заповедта)")
for име, т in К.items():
    има = any(r.strip().startswith("👉") for r in ст.чист(т).split("\n"))
    print(("   OK  " if има else "   НЯМА"), име)
print()
print("### ЛЪЖЛИВОТО ЗЕЛЕНО НА П25 «казва какво да правя»")
_з = "😴 НЕ СЪМ ГЛЕДАЛ ПАЗАРА 2ч · борсата беше затворена"
print("   текст без никакво действие:", _з)
print("   П25 го пуска:", any(d in _з.lower() for d in _ДЕЙСТВИЕ25),
      "· заради", [d for d in _ДЕЙСТВИЕ25 if d in _з.lower()])
_з2 = "👉 ПРОВЕРИ при брокера какво е станало с отворената сделка"
print("   истинска заповед:", _з2)
print("   П25 я пуска:", any(d in _з2.lower() for d in _ДЕЙСТВИЕ25))
