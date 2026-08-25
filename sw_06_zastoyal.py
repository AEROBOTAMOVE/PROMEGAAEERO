# -*- coding: utf-8 -*-
"""Находка 6: «застоял бар (празник/тънка сесия?)» вместо дневната CME пауза."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.argv = ["x"]
import live_bot as lb

def бележка(now_utc, bar_age_min):
    _защо = ("дневната пауза на борсата" if lb._cme_pause(now_utc)
             else "празник или тънка сесия?")
    return f"застоял бар: {bar_age_min:.0f} мин стар — {_защо}"

for u in ("2026-08-19T21:30:00",   # 17:30 Ню Йорк = CME паузата
          "2026-01-15T22:30:00",   # 17:30 NY зимно време (EST)
          "2026-08-19T14:30:00"):  # обикновен час
    print(u, "| NY час =", lb._to_ny(u).hour, "| _cme_pause =", lb._cme_pause(u))
    print("   ->", бележка(u, 45))
