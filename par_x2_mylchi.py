import sys, json, io
sys.argv=["x"]
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import live_bot as lb
ст=json.load(open('backtest_stats.json',encoding='utf-8'))
import inspect
print(inspect.signature(lb._защо_мълчи))
for пос in ("long","short",None):
    for д,л in ((0.015,-0.07),(-0.015,0.07)):
        print("--- dir=",пос," д=",д," л=",л)
        r=lb._защо_мълчи({"долар":д,"лихви":л},{"long":3,"short":2},стат=ст,new_dir=пос) if 'стат' in inspect.signature(lb._защо_мълчи).parameters else None
        print("\n".join(r))
