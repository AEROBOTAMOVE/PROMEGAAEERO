# -*- coding: utf-8 -*-
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
s = json.load(open('backtest_stats.json', encoding='utf-8'))
print('top keys:', list(s.keys()))
fr = s['fresh']
for d in ('long', 'short'):
    print('---', d)
    for k, v in fr[d].items():
        print('   ', k, v)
