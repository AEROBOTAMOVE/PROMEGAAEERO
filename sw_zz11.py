# -*- coding: utf-8 -*-
import sys; sys.path.insert(0,'.')
from brain import chart_brain as CB
import inspect
print('ПАУЗА_БАРОВЕ=',CB.ПАУЗА_БАРОВЕ,' ПАУЗА_МИНУТИ=',CB.ПАУЗА_МИНУТИ)
for рамка in ('1мин','5м','15м'):
    мб=CB.МИНУТИ.get(рамка,15)
    нужни=max(CB.ПАУЗА_БАРОВЕ, -(-CB.ПАУЗА_МИНУТИ//max(мб,1)))
    print(f'  {рамка:5s}: {нужни} бара = {нужни*мб} мин заглушаване')
src=inspect.getsource(CB.сканирай)
for l in src.splitlines():
    if 'ако_по_силна' in l: print('ИЗХОД ЗА ПО-СИЛНА КАРТА:', l.strip())
