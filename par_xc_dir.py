import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
sys.argv=["x"]
import live_bot as lb
# доказваме: в _digest_msg/_pulse_msg/_status_msg `notes` НЕ е локално име
import inspect,ast
src=inspect.getsource(lb)
t=ast.parse(src)
for f in ast.walk(t):
    if isinstance(f,ast.FunctionDef) and f.name in("_digest_msg","_pulse_msg","_status_msg"):
        имена=set()
        for n in ast.walk(f):
            if isinstance(n,ast.Name): имена.add(n.id)
            if isinstance(n,ast.arg): имена.add(n.arg)
        приети={a.arg for a in f.args.args}
        присвоени=set()
        for n in ast.walk(f):
            if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store): присвоени.add(n.id)
        print(f.name,"· 'notes' в аргументите:", "notes" in приети, "· присвоено локално:", "notes" in присвоени)
# и живо: счупена сделка → има ли бележка?
tr={"direction":"long","entry":"БОКЛУК","levels":{},"hit":{}}
n=[]
print("с notes:",lb._отворена_стълба(tr,{"mid":4400.0},n), n)
print("без notes:",lb._отворена_стълба(tr,{"mid":4400.0}))
print("digest ред:")
import re,pathlib,tempfile,os
d=pathlib.Path(tempfile.mkdtemp())
print(re.sub(r"<[^>]+>","",lb._digest_msg(d,"2026-08-18",tr,None,{"mid":4400.0},None,{})))
