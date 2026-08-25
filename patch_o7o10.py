# -*- coding: utf-8 -*-
"""
ГЕНЕРАЛЕН ПЛАН · О7 + О10  +  ЕДНА НАХОДКА ПО ПЪТЯ

🔴 НАХОДКАТА · VERSION = "v9.4", А КАЧЕНИ СА v9.5, v9.6, v9.7, v9.8
   Константата не е местена нито веднъж днес. Всеки ред в live_journal.jsonl
   от последните четири качвания твърди «v9.4». Тоест дневникът — единственият
   начин отвън да се види коя версия работи — лъже.
   Точно това О10 иска с «версия-щемпел в лога (защита срещу 14.07)».
   ПОПРАВКА: вдигната на v9.8 + тест, който пада, ако VERSION не се среща в
   темата на последния commit. Забравя ли се пак — селфтестът гърми ПРЕДИ
   качване, защото е бариера в workflow-а.

О7 · КРАШ-АЛАРМАТА СПАМИ
   `if: failure()` + «5 от последните 6 са паднали» → щом веднъж се навърти,
   ВСЕКИ следващ рън също вижда 5-6 падания и алармата стреля на всеки 5 мин.
   ПОПРАВКА: стреля само на ПРЕХОДА — 5+ от последните 6 паднали И под 5 от
   предходните 6. Един сигнал на епизод, без да се пази състояние.

О10 · WORKFLOW ДРЕБНИ
   · audit.yml и tests.yml нямат `concurrency` → два едновременни ръна дават
     дублиран отчет. Добавена група с cancel-in-progress.
   · одит-кронът дрейфа: коментарите твърдят София-часове, а cron-ът е UTC —
     зиме всеки слот идва час по-рано. Коментарите вече казват И двете.
   · версията се печата в началото на лога.
"""
import io, sys, ast, hashlib

ops = []


def rep(p, old, new, why, n=1):
    s = io.open(p, encoding="utf-8", newline="").read()
    c = s.count(old)
    if c != n:
        print(f"  x СПИРАМ «{why}»: {c} съвпадения, чакам {n}\n    {old[:130]!r}")
        sys.exit(1)
    io.open(p, "wb").write(s.replace(old, new).encode("utf-8"))
    ops.append(why)


# ═══ находката · версията ════════════════════════════════════════════════
rep("live_bot.py", 'VERSION = "v9.4"',
    '''# 🔴 ВДИГАЙ Я ПРИ ВСЯКО КАЧВАНЕ. Беше заседнала на "v9.4", докато бяха качени
# v9.5–v9.8 — всеки ред в дневника твърдеше грешна версия, а дневникът е
# единственият начин отвън да се види какво работи. П47 пада, ако VERSION не се
# среща в темата на последния commit.
VERSION = "v9.8"''',
    "версията е вдигната")

# ═══ О7 · алармата стреля веднъж на епизод ═══════════════════════════════
rep(".github/workflows/aero-bot.yml",
    '''          FAILS=$(curl -s -H "Authorization: Bearer ${{ github.token }}" \\
            "https://api.github.com/repos/${GITHUB_REPOSITORY}/actions/workflows/aero-bot.yml/runs?status=completed&per_page=6" \\
            | grep -o '"conclusion":"[a-z]*"' | head -6 | grep -c 'failure' || true)
          if [ "${FAILS:-0}" -ge 5 ]; then''',
    '''          # О7 · СТРЕЛЯ САМО НА ПРЕХОДА, не при всеки рън.
          # Дотук: щом веднъж се навъртят 5 падания, ВСЕКИ следващ рън също вижда
          # 5-6 и алармата излиза на всеки 5 минути до края на епизода.
          # Сега: 5+ от ПОСЛЕДНИТЕ 6 паднали И под 5 от ПРЕДХОДНИТЕ 6 → един
          # сигнал на епизод, без да се пази състояние никъде.
          CONCL=$(curl -s -H "Authorization: Bearer ${{ github.token }}" \\
            "https://api.github.com/repos/${GITHUB_REPOSITORY}/actions/workflows/aero-bot.yml/runs?status=completed&per_page=12" \\
            | grep -o '"conclusion":"[a-z]*"')
          FAILS=$(echo "$CONCL" | head -6 | grep -c 'failure' || true)
          PREV=$(echo "$CONCL" | sed -n '7,12p' | grep -c 'failure' || true)
          echo "падания: последни 6 = ${FAILS:-0} · предходни 6 = ${PREV:-0}"
          if [ "${FAILS:-0}" -ge 5 ] && [ "${PREV:-0}" -lt 5 ]; then''',
    "О7 · аларма веднъж на епизод")

# ═══ О10 · версия в лога ═════════════════════════════════════════════════
rep(".github/workflows/aero-bot.yml",
    '''      - name: selftest gate                             # W1: счупен код НЕ праща сигнали''',
    '''      - name: версия                                    # О10: коя версия работи — да се вижда в лога
        run: |
          python -c "import re,io;print('AERO', re.search(r'VERSION = \\"([^\\"]+)\\"', io.open('live_bot.py',encoding='utf-8').read()).group(1))"
          git log --oneline -1
      - name: selftest gate                             # W1: счупен код НЕ праща сигнали''',
    "О10 · версия в лога")

# ═══ О10 · concurrency ═══════════════════════════════════════════════════
rep(".github/workflows/audit.yml", '''  workflow_dispatch:
permissions:''',
    '''  workflow_dispatch:
# О10 · без това два едновременни ръна дават ДУБЛИРАН отчет в чата.
concurrency:
  group: aero-audit
  cancel-in-progress: false
permissions:''',
    "О10 · concurrency за одита")

rep(".github/workflows/tests.yml", '''  workflow_dispatch:
jobs:''',
    '''  workflow_dispatch:
# О10 · няколко бързи качвания едно след друго вдигаха успоредни тестове.
concurrency:
  group: aero-tests-${{ github.ref }}
  cancel-in-progress: true
jobs:''',
    "О10 · concurrency за тестовете")

# ═══ О10 · честни коментари за крона ═════════════════════════════════════
rep(".github/workflows/audit.yml",
    """    - cron: '0 2 * * 1-5'     # 05:00 София — по време на Азия""",
    """    # 🔴 О10 · CRON Е ВИНАГИ UTC. Часовете долу са ЛЯТНО софийско (UTC+3);
    # зиме (UTC+2) всеки слот идва ЧАС ПО-РАНО. GitHub няма часова зона в cron,
    # затова е неизбежно — но коментарът вече не лъже.
    - cron: '0 2 * * 1-5'     # 05:00 лято / 04:00 зима София — Азия""",
    "О10 · честен коментар за крона")

print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
ast.parse(io.open("live_bot.py", encoding="utf-8").read())
for f in ("live_bot.py", ".github/workflows/aero-bot.yml",
          ".github/workflows/audit.yml", ".github/workflows/tests.yml"):
    b = io.open(f, encoding="utf-8").read()
    print(f"  {f}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
