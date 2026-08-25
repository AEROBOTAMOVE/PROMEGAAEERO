import sys, re
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import live_bot as lb, pandas as pd

src = open("live_bot.py", encoding="utf-8").read().splitlines()
# ИЗВЛИЧАМ ТОЧНИЯ БЛОК ОТ ЖИВИЯ ФАЙЛ (не преразказ)
нач = next(i for i,l in enumerate(src) if "БРОЯЧЪТ НА СУХИТЕ РЪНА" in l)
нач = next(i for i in range(нач, len(src)) if src[i].strip().startswith("try:"))
край = next(i for i in range(нач, len(src)) if "_сухо_карта:" in src[i])
блок = "\n".join(x[4:] if x.startswith("    ") else x for x in src[нач:край])
print("=== изпълнявам редове", нач+1, "-", край, "от live_bot.py ===")

g = {k: getattr(lb, k) for k in dir(lb)}
g.update(pd=pd)
meta = {}
карти = []
for рън in range(1, 31):
    ctx = dict(g)
    ctx.update(dict(СУХИ_МАКС=lb.СУХИ_МАКС, СУХИ_ПОВТОР_Ч=lb.СУХИ_ПОВТОР_Ч,
                    weekend=False, spot_g=None, spot_rejected_g=False,
                    meta=meta, notes=[], _сухо_карта=None,
                    now_utc=f"2026-08-19T{10+рън//12:02d}:{(рън*5)%60:02d}:00Z"))
    exec(блок, ctx)
    if ctx["_сухо_карта"]:
        карти.append((рън, ctx["_сухо_карта"]))
    if рън in (1, 23, 24, 25, 30):
        print(f"рън {рън:>2}: сухи={meta.get('сухи_ръна')} карта={'ДА' if ctx['_сухо_карта'] else 'не'} | бележка: {ctx['notes'][-1] if ctx['notes'] else '—'}")
print("\nобщо карти за 30 сухи ръна:", len(карти))
if карти:
    print("--- ТЕКСТЪТ НА КАРТАТА (рън %d) ---" % карти[0][0])
    print(карти[0][1][1])
