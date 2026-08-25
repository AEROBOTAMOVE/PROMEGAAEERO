import sys,io,re,pathlib,tempfile
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8'); sys.argv=["x"]
import live_bot as lb
tr={"direction":"long","entry":4358.0,"levels":{},"hit":{"tp1":True}}   # липсват нива
n=[]
print("_отворена_стълба с notes:",lb._отворена_стълба(tr,{"mid":4400.0},n),"| бележки:",n)
d=pathlib.Path(tempfile.mkdtemp())
print("--- равносметка:")
print(re.sub(r"<[^>]+>","",lb._digest_msg(d,"2026-08-18",tr,None,{"mid":4400.0},None,{})))
print("--- пулс:")
print(re.sub(r"<[^>]+>","",lb._pulse_msg("14",[],None,None,"",False,tr,None,{"mid":4400.0},None,{},False,False)))
