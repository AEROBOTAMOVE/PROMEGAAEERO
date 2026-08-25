# -*- coding: utf-8 -*-
import sys; sys.argv=["x"]
import live_bot as lb
print("WEEKEND_MSGS слотове:", {k:len(v) for k,v in lb.WEEKEND_MSGS.items()})
print("SHIELD_ET:", lb.SHIELD_ET, "EXIT_TAGS:", lb.EXIT_TAGS)
print("TFS:", [t[0] for t in lb.TFS])
print("MACRO_LBL:", lb.MACRO_LBL)
print("CQ_CLUSTERS:", lb.CQ_CLUSTERS)
print("ZONE_W:", lb.ZONE_W, "МАЛЪК_РАЗМЕР_W:", lb.МАЛЪК_РАЗМЕР_W)
print("REOFFER:", lb.REOFFER_H, lb.REOFFER_MAX_AGE_H, lb.STANDING_H, lb.REOFFER_LO, lb.REOFFER_HI)
print("MIN_N:", lb.MIN_N, "NEAR_HIGH_DD20:", lb.NEAR_HIGH_DD20, "POISON:", lb.POISON_HARD_FAILS)
print("BASIS_ALPHA:", lb.BASIS_ALPHA, "TF_BASIS_ALPHA:", lb.TF_BASIS_ALPHA, "TF_BASIS_CAP:", lb.TF_BASIS_CAP)
print("SPOT_MAX_AGE:", lb.SPOT_MAX_AGE, "CLOCK_SKEW:", lb.CLOCK_SKEW, "СКЮ_ДОПУСК:", lb.СКЮ_ДОПУСК)
print("ЛИХВИ_ИЗТОЧНИК:", lb.ЛИХВИ_ИЗТОЧНИК, "CB:", type(lb.CB).__name__)
print("CHART_BRAIN_ON:", lb.CHART_BRAIN_ON, "МОЗЪК_ЖИВА_ЦЕНА:", lb.МОЗЪК_ЖИВА_ЦЕНА,
      "МОЗЪК_СЛЕДЕНЕ:", lb.МОЗЪК_СЛЕДЕНЕ, "СТАТ_ЗАДЪЛЖИТЕЛНА:", lb.СТАТ_ЗАДЪЛЖИТЕЛНА)
print("СПАЛ_МИН:", lb.СПАЛ_МИН, "СТОЯЩ_МАКС_Ч:", lb.СТОЯЩ_МАКС_Ч, "СТАР_МАКРО_Ч:", lb.СТАР_МАКРО_Ч)
print("ЛИХВИ_ЗАСТОЙ_ДНИ:", lb.ЛИХВИ_ЗАСТОЙ_ДНИ, "ИЗБЛИК_Х:", lb.ИЗБЛИК_Х,
      "АРХИВ_МЕСЕЦИ:", lb.АРХИВ_МЕСЕЦИ, "ОПАШКА_ТАВАН:", lb.ОПАШКА_ТАВАН)
