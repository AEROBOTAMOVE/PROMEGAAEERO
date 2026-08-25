import sys, re, html, json
from pathlib import Path
sys.argv=["x"]; БАЗА=Path(__file__).resolve().parent; sys.path.insert(0,str(БАЗА))
import огледало as og
def чист(t): return re.sub(r"<[^>]+>","",html.unescape(str(t)))
print(json.dumps(og.st.get("ma_bounce"), ensure_ascii=False, indent=1)[:1200])
for d in ("long","short"):
    for m in (og.st.get("ma_bounce",{}).get(d,{}) or {}):
        mb = og.st["ma_bounce"][d][m]
        print("="*60); print(f"### MA-АЛАРМА {d}/{m}")
        print(чист(og.lb._ma_alert_msg(d, m, 4365.2, mb, og.mac)))
