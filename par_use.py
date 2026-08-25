# -*- coding: utf-8 -*-
import ast, io
src = io.open("live_bot.py", encoding="utf-8").read()
tree = ast.parse(src)
names = ["VERSION","PIP","SL_PIPS","SL_D","TPS","S_TPS","S_SL","TFS","MACRO_LBL","BASIS_ALPHA",
"ROLLOVER_JUMP","ROLLOVER_JUMP_S","SHIELD_ET","CHART_BRAIN_ON","МОЗЪК_ЖИВА_ЦЕНА","МОЗЪК_ПРАГ",
"МОЗЪК_РАМКИ","МОЗЪК_ПРАГ_РАМКА","МОЗЪК_ТАВАН","МОЗЪК_РАЗРЕД_МИН","МОЗЪК_СЛЕДЕНЕ","МАЛЪК_РАЗМЕР_W",
"РЕОФЕР_КЛАС","РАВЕНСТВО_БЪРЗА","СПАЛ_МИН","СТАТ_ЗАДЪЛЖИТЕЛНА","СТОЯЩ_МАКС_Ч","СРЕБРО_MIXED",
"СРЕБРО_СПРЕД","СРЕБРО_ВХОД","СТАР_МАКРО_Ч","ЛИХВИ_ЗАСТОЙ_ДНИ","ИЗБЛИК_Х","АРХИВ_МЕСЕЦИ","ОПАШКА_ТАВАН",
"МОЗЪК_РАНГ_ВХОД","МОЗЪК_МИН_RR","CB","ЛИХВИ_ИЗТОЧНИК","SPOT_MAX_AGE","CLOCK_SKEW","СКЮ_ДОПУСК",
"TF_BASIS_ALPHA","TF_BASIS_CAP","MIN_N","NEAR_HIGH_DD20","REOFFER_H","REOFFER_MAX_AGE_H","STANDING_H",
"REOFFER_LO","REOFFER_HI","ZONE_W","KV_URL","CQ_CLUSTERS","CQ_ZONE_HIST","POISON_HARD_FAILS","EXIT_TAGS","WEEKEND_MSGS"]
cnt = {n:[] for n in names}
for node in ast.walk(tree):
    if isinstance(node, ast.Name) and node.id in cnt and isinstance(node.ctx, ast.Load):
        cnt[node.id].append(node.lineno)
for n in names:
    print("%-22s uses=%-3d lines=%s" % (n, len(cnt[n]), cnt[n][:14]))
