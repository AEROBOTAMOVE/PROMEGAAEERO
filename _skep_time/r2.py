# -*- coding: utf-8 -*-
"""Реконструирам състоянието ПРЕДИ поправката: махам САМО блока за изход по време
от ТЕКУЩИЯ live_bot.py и пускам двете версии една до друга."""
import sys, io, os, json, hashlib, pathlib, tempfile, importlib.util
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
os.chdir(BASE); sys.path.insert(0, BASE)
src = open("live_bot.py", encoding="utf-8").read()
print("live_bot.py sha1:", hashlib.sha1(src.encode()).hexdigest()[:8])

нач = src.index('    if т is not None and цена is not None and now_utc:')
кр  = src.index('    if т is not None and цена is not None:\n        лонг')
изряз = src[нач:кр]
print("изрязани редове:", изряз.count("\n"), "· съдържа brain-exit:време:", "brain-exit:време" in изряз)
пре = src[:нач] + src[кр:]
open("_skep_time/lb_prefix.py","w",encoding="utf-8").write(пре)

def зареди(път, име):
    spec = importlib.util.spec_from_file_location(име, път)
    m = importlib.util.module_from_spec(spec); sys.modules[име]=m; spec.loader.exec_module(m); return m

def сцена(lb, етикет, отворен, сега, цена, стоп, цел1, цел2, руна=500, бар=True):
    d = pathlib.Path(tempfile.mkdtemp()); f=d/"brain_track.json"; j=d/"brain_result.jsonl"
    f.write_text(json.dumps({"посока":"long","рамка":"15м","степен":"🔥","точки":14,
        "отворен":отворен,"вход":4600.0,"стоп":стоп,"цел1":цел1,"цел2":цел2,"цел1_взета":False},
        ensure_ascii=False), encoding="utf-8")
    нов = {"лонг":True,"рамка":"5м","степен":"🔥","точки":15,
           "залог":{"вход":4610.0,"стоп":4605.0,"цел":4620.0,"цел2":4630.0}}
    к=[]
    for _ in range(руна):
        b = (цена+2.0, цена-2.0) if (бар and цена is not None) else None
        к += lb._мозък_следене(f, j, цена, сега, нов=нов, бар=b)
    т = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
    ново = (т is not None and т.get("рамка")=="5м")
    print(f"    {етикет:52s} → отворено={т.get('отворен') if т else '-'} рамка={т.get('рамка') if т else '-'} "
          f"| ново прието: {'ДА' if ново else 'НЕ'} | карти:{len(к)}")
    return ново

for път,име,етикет in (("_skep_time/lb_prefix.py","pre","БЕЗ поправка (както е бил sha 68bf672b)"),
                       ("live_bot.py","now","СЕГА (с поправката)")):
    lb = зареди(път,име)
    print("\n### "+етикет)
    сцена(lb,"17 месеца, цена 4650 между стоп4500/цел2 4800","2026-01-01T00:00","2027-06-01T12:00",4650.0,4500.0,4700.0,4800.0)
    сцена(lb,"6 дни, широки нива (пазарен уикенд+празник)","2026-08-15T00:00","2026-08-21T12:00",4650.0,4500.0,4700.0,4800.0)
    сцена(lb,"4 часа, широки нива (пресен, НЕ бива да пада)","2026-08-21T08:00","2026-08-21T12:00",4650.0,4500.0,4700.0,4800.0)
    сцена(lb,"живата геометрия ±5.6$, цена стои на входа","2026-08-19T10:00","2026-08-21T12:00",4600.0,4594.4,4606.6,None)
    сцена(lb,"ЦЕНАТА МЪЛЧИ (цена=None), 17 месеца","2026-01-01T00:00","2027-06-01T12:00",None,4500.0,4700.0,4800.0)
    сцена(lb,"без ключ 'отворен' (None), 17 месеца","2026-01-01T00:00","2027-06-01T12:00",4650.0,4500.0,4700.0,4800.0) if False else None
