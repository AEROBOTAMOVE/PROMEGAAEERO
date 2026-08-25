import ast, io, sys
src = open('live_bot.py', encoding='utf-8').read()
tree = ast.parse(src)
out=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.FunctionDef, ast.AsyncFunctionDef)):
        args=[a.arg for a in n.args.args]
        defs=len(n.args.defaults)
        out.append((n.name, n.lineno, args, defs, isinstance(n,ast.AsyncFunctionDef)))
for name,ln,args,defs,isa in out:
    if '_msg' in name or 'msg' in name.lower() or 'card' in name.lower() or 'карт' in name:
        print(f"{ln}\t{'async ' if isa else ''}{name}({', '.join(args)})  defaults={defs}")
print('---TOTAL FUNCS---', len(out))
