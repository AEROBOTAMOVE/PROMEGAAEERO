# -*- coding: utf-8 -*-
import sys, io, inspect
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.argv = ['live_bot.py']
import live_bot
f = live_bot._reentry_ban
print("ИСТИНСКИ импорт на live_bot ·", live_bot.__file__)
print("сигнатура:", inspect.signature(f))
meta = {}
f(meta, 'long', 2, why='2 стопа днес в тази посока — спирам до утре', set_it=True, ден='2026-08-20')
print("запис        :", meta)
print("21.08 date=20:", f(meta, 'long', 2, ден='2026-08-20'))
print("21.08 date=21:", f(meta, 'long', 2, ден='2026-08-21'))
print("meta след    :", meta)
