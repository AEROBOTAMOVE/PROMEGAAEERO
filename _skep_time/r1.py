# -*- coding: utf-8 -*-
import sys, io, os, json, hashlib, pathlib, tempfile, importlib.util
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
BASE = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
os.chdir(BASE); sys.path.insert(0, BASE)

def зареди(път, име):
    spec = importlib.util.spec_from_file_location(име, път)
    m = importlib.util.module_from_spec(spec); sys.modules[име] = m
    spec.loader.exec_module(m); return m

def сцена(lb, етикет, отворен, сега, цена, стоп, цел1, цел2, руна=500):
    d = pathlib.Path(tempfile.mkdtemp()); f = d/"brain_track.json"; j = d/"brain_result.jsonl"
    f.write_text(json.dumps({"посока":"long","рамка":"15м","степен":"🔥","точки":14,
        "отворен":отворен,"вход":4600.0,"стоп":стоп,"цел1":цел1,"цел2":цел2,
        "цел1_взета":False}, ensure_ascii=False), encoding="utf-8")
    нов = {"лонг":True,"рамка":"5м","степен":"🔥","точки":15,
           "залог":{"вход":4610.0,"стоп":4605.0,"цел":4620.0,"цел2":4630.0}}
    карти=[]
    for i in range(руна):
        карти += lb._мозък_следене(f, j, цена, сега, нов=нов, бар=((цена+2.0, цена-2.0) if цена else None))
    има = f.exists()
    т = json.loads(f.read_text(encoding="utf-8")) if има else None
    прието = (т is not None and т.get("рамка")=="5м")
    print(f"  [{етикет}] файл={'ДЪРЖИ' if има else 'трит'} · рамка={т.get('рамка') if т else '-'} "
          f"· ново прието={'ДА' if прието else 'НЕ'} · карти={len(карти)} "
          f"· дневник={j.read_text(encoding='utf-8').count(chr(10)) if j.exists() else 0} реда")
    if карти: print("      първа карта:", карти[0][0])
    return прието

for път, име in (("live_bot.py","lb_now"), ("_skep_time/lb_pre.py","lb_pre")):
    raw = open(път,"rb").read()
    print("="*70)
    print(f"{път}  sha1={hashlib.sha1(raw).hexdigest()[:8]}  байта={len(raw)}")
    lb = зареди(път, име)
    блок = raw.decode("utf-8")
    блок = блок[блок.index("def _мозък_следене"):блок.index("def _мозък_изход_msg")]
    print("  има ли изход по време в кода:", "brain-exit:време" in блок)
    # 1) сцената на другия агент: 17 месеца, цена между нивата
    сцена(lb,"17 месеца, цена 4650 между 4500/4800","2026-01-01T00:00","2027-06-01T12:00",4650.0,4500.0,4700.0,4800.0)
    # 2) 4 часа (пресен) — не бива да изтича
    сцена(lb,"4 часа","2026-08-21T08:00","2026-08-21T12:00",4650.0,4500.0,4700.0,4800.0)
    # 3) живата геометрия ±5$ — цена стои на входа
    сцена(lb,"живи нива ±5$, 17 месеца","2026-01-01T00:00","2027-06-01T12:00",4600.0,4594.4,4606.6,None)
