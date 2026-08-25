# -*- coding: utf-8 -*-
import ast, io
src=io.open("live_bot.py",encoding="utf-8").read()
t=ast.parse(src)
main=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=="main"][0]
# намери възела на ред 3855 и провери дали е в тялото на main БЕЗ обвиващ if/try
цел=None
for n in ast.walk(main):
    if getattr(n,"lineno",None)==3855 and isinstance(n,ast.Expr): цел=n
def път(корен, цел, стек=()):
    for дете in ast.iter_child_nodes(корен):
        if дете is цел: return стек+(type(корен).__name__,)
        r=път(дете, цел, стек+(type(корен).__name__,))
        if r: return r
p=път(main,цел)
print("ред 3855 (meta.json write_text) обвивки:", " > ".join(p))
# същото за реда, който вдига часовника
часовник=[n for n in ast.walk(main) if isinstance(n,ast.Assign)
          and any(isinstance(t2,ast.Subscript) and isinstance(t2.value,ast.Name) and t2.value.id=="meta"
                  and getattr(t2.slice,"value",None)=="последен_рън" for t2 in n.targets)]
for c in часовник:
    print(f"ред {c.lineno} (meta['последен_рън']=now_utc) обвивки:", " > ".join(път(main,c)))
