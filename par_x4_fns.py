import ast,io,sys
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
src=open('live_bot.py',encoding='utf-8').read()
t=ast.parse(src)
for n in ast.walk(t):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
        args=[a.arg for a in n.args.args]
        print(f"{n.lineno:5d} {n.name}({', '.join(args)})")
