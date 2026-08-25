# -*- coding: utf-8 -*-
"""О7/О10 (тестове) · П47 не позволява версията пак да заседне."""
import io, ast

p = "selftest.py"
s = io.open(p, encoding="utf-8", newline="").read()
assert "П47" not in s, "П47 вече съществува"

БЛОК = '''# ═══ П47 · ВЕРСИЯТА НЕ БИВА ДА ЗАСЕДНЕ (О10) ═════════════════════════════
# 🔴 НАМЕРЕНО ДНЕС: VERSION стоеше "v9.4", докато бяха качени v9.5, v9.6, v9.7
# и v9.8. Всеки ред в live_journal.jsonl от четирите качвания твърдеше грешна
# версия — а дневникът е ЕДИНСТВЕНИЯТ начин отвън да се види какво работи.
# Този тест пада, ако VERSION не се среща в темата на последния commit.
import subprocess as _sp47
_в47 = lb.VERSION
ck("П47 версията изглежда като версия", _в47.startswith("v") and _в47[1].isdigit())
try:
    _тема47 = _sp47.run(["git", "log", "-1", "--pretty=%s"], capture_output=True,
                        text=True, encoding="utf-8", timeout=20).stdout.strip()
except Exception:
    _тема47 = ""
if _тема47:
    ck(f"П47 VERSION ({_в47}) се среща в последния commit: {_тема47[:44]}",
       _в47 in _тема47)
else:
    # без git (напр. разпакетиран архив) тестът не бива да мълчи ТИХО
    ck("П47 няма git — проверката за версия е ПРОПУСНАТА, не минала", True)
    print("    ⚠️ П47: няма git, проверката за версия не е правена")
ck("П47 версията влиза във всеки ред на дневника", '"v": VERSION' in
   open("live_bot.py", encoding="utf-8").read())
_я47 = open(".github/workflows/aero-bot.yml", encoding="utf-8").read()
ck("П47 версията се печата в лога на Actions", "- name: версия" in _я47)

# ═══ О7 · АЛАРМАТА СТРЕЛЯ ВЕДНЪЖ НА ЕПИЗОД ═══════════════════════════════
# Дотук: щом веднъж се навъртят 5 падания, всеки следващ рън също вижда 5-6 и
# алармата излиза на всеки 5 минути до края на епизода.
ck("О7 алармата гледа и ПРЕДХОДНИТЕ 6 ръна", "PREV=$(echo" in _я47)
ck("О7 стреля само на прехода", '[ "${PREV:-0}" -lt 5 ]' in _я47)
ck("О7 брои от 12, не от 6", "per_page=12" in _я47)
# истинската логика, изпълнена тук:
def _ал47(поредица):
    ф = sum(1 for x in поредица[:6] if x == "f")
    п = sum(1 for x in поредица[6:12] if x == "f")
    return ф >= 5 and п < 5
ck("О7 нормално → мълчи", not _ал47("ssssssssssss"))
ck("О7 едно мигване → мълчи", not _ал47("fsssssssssss"))
ck("О7 епизодът ЗАПОЧВА → аларма", _ал47("fffffsssssss"))
ck("О7 епизодът ПРОДЪЛЖАВА → мълчи (без спам)", not _ал47("fffffffffffs"))
ck("О7 епизодът свършва → мълчи", not _ал47("ssffffffffff"))

# ═══ О10 · concurrency ═══════════════════════════════════════════════════
for _ф47 in ("aero-bot", "audit", "tests"):
    _т47 = open(f".github/workflows/{_ф47}.yml", encoding="utf-8").read()
    ck(f"О10 {_ф47}.yml има concurrency", "concurrency:" in _т47)
ck("О10 коментарът за крона не лъже за зимата",
   "зима" in open(".github/workflows/audit.yml", encoding="utf-8").read())

'''

_к = "# ═══ П26 · СТОПЪТ НА КАРТАТА СЪВПАДА С НИВАТА"
assert s.count(_к) == 1
io.open(p, "wb").write(s.replace(_к, БЛОК + _к).encode("utf-8"))
ast.parse(io.open(p, encoding="utf-8").read())
print("П47 добавен")
