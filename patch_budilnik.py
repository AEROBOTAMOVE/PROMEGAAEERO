# -*- coding: utf-8 -*-
"""
ОДИТ-51 · ВЗАИМЕН БУДИЛНИК — ЖИВ ЛИ Е ЕДИНИЯТ, ЖИВ Е И ДРУГИЯТ

ДОСЕГА ВРЪЗКАТА Е ЕДНОПОСОЧНА: ботът буди одит-робота (шест от седемте му крона
стоят на кръгъл час — точно когато GitHub изхвърля разписания). Обратното го
няма. Значи спре ли ботът, спира и единственото нещо, което би забелязало, че
е спрял. Мерено на живо: дупка от 447 минути на 06.08, която НИКОЙ не видя.

Сега одит-роботът връща жеста: намери ли, че ботът не е бягал над
БОТ_ЗАСТОЙ_МИН, го буди. Двата се държат взаимно и трябва да умрат ЕДНОВРЕМЕННО,
за да замлъкне системата.

Прагът е 25 мин — пет пъти нормалния интервал (5 мин), значи не стреля на
обикновено закъснение на GitHub cron-а (мерено: медиана 65 мин закъснение при
разписаните, но външният часовник дава реални 5 мин).

`continue-on-error` — будилникът НИКОГА не бива да вали одита, както и обратното.
"""
import io, sys, hashlib

ops = []


def rep(p, old, new, why, n=1):
    s = io.open(p, encoding="utf-8", newline="").read()
    c = s.count(old)
    if c != n:
        print(f"  x СПИРАМ «{why}»: {c} съвпадения, чакам {n}\n    {old[:130]!r}")
        sys.exit(1)
    io.open(p, "wb").write(s.replace(old, new).encode("utf-8"))
    ops.append(why)


AY = ".github/workflows/audit.yml"

# одитът трябва да може да пише в Actions, за да дispatch-ва
rep(AY, '''permissions:
  contents: read''',
    '''permissions:
  contents: read
  actions: write            # ОДИТ-51: одитът връща жеста и буди бота''',
    "правата на одита")

rep(AY, '''      - name: log failure                               # ОДИТ-21: БЕЗ съобщение в Телеграм''',
    '''      # 🔴 ОДИТ-51 · ВЗАИМЕН БУДИЛНИК. Дотук ботът будеше одита, но не обратното —
      # значи спре ли ботът, спира и единственото нещо, което би забелязало.
      # Мерено на живо: дупка от 447 минути на 06.08, която НИКОЙ не видя.
      # Прагът 25 мин е пет пъти нормалния интервал → не стреля на дребно закъснение.
      - name: wake the bot
        if: always()
        continue-on-error: true          # будилникът НИКОГА не вали одита
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          LAST=$(curl -s -H "Authorization: Bearer $GH_TOKEN" \\
            "https://api.github.com/repos/${GITHUB_REPOSITORY}/actions/workflows/aero-bot.yml/runs?per_page=1" \\
            | grep -o '"created_at": *"[^"]*"' | head -1 | sed 's/.*"\\([^"]*\\)"$/\\1/')
          if [ -z "$LAST" ]; then echo "няма история на бота — не будя"; exit 0; fi
          AGE=$(( ( $(date -u +%s) - $(date -u -d "$LAST" +%s) ) / 60 ))
          echo "последен рън на бота: $LAST (преди ${AGE} мин)"
          # пазарът затворен ли е → мълчи (същият прозорец като в бота)
          DOW=$(date -u +%u); HH=$(date -u +%H)
          if [ "$DOW" = "6" ] || { [ "$DOW" = "5" ] && [ "$HH" -ge 21 ]; } \\
             || { [ "$DOW" = "7" ] && [ "$HH" -lt 21 ]; }; then
            echo "пазарът е затворен — не будя"; exit 0
          fi
          if [ "$AGE" -lt 25 ]; then echo "бягал е преди ${AGE} мин — не го будя"; exit 0; fi
          echo "🔔 ботът мълчи от ${AGE} мин — будя го"
          curl -s -X POST -H "Authorization: Bearer $GH_TOKEN" \\
            -H "Accept: application/vnd.github+json" \\
            "https://api.github.com/repos/${GITHUB_REPOSITORY}/actions/workflows/aero-bot.yml/dispatches" \\
            -d '{"ref":"main"}' -w "HTTP %{http_code}\\n"
      - name: log failure                               # ОДИТ-21: БЕЗ съобщение в Телеграм''',
    "одитът буди бота")

print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
b = io.open(AY, encoding="utf-8").read()
print(f"{AY}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
