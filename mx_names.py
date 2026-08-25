import ast, io
src = io.open("live_bot.py", encoding="utf-8").read()
t = ast.parse(src)
want = ["_бр","_ппз","_очаквай","КОФА_ДУМИ","ДНИ_МАКС","ВЪЗРАСТ_ВХОД","РЕД_ДУМА","_зона_текст","_възраст_нето","_пари","_пипс","_разст","_съгласни","_sofia","_fmt","MIN_N","PIP","РЪБ_Ч","ИМЕ_МАКРО","_сила"]
found={}
for n in ast.walk(t):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
        found.setdefault(n.name,n.lineno)
    if isinstance(n,ast.Assign):
        for tg in n.targets:
            if isinstance(tg,ast.Name): found.setdefault(tg.id,n.lineno)
for w in want:
    print(f"{w:16s} {found.get(w,'-- НЯМА --')}")
