# -*- coding: utf-8 -*-
import sys, json, tempfile, shutil
from pathlib import Path
sys.argv=["x"]; import live_bot as lb
o=lb._send_raw

def flush(msgs, new, send="SENT (200)"):
    d=Path(tempfile.mkdtemp())
    (d/"outbox.jsonl").write_text("\n".join(json.dumps(m,ensure_ascii=False) for m in msgs),encoding="utf-8")
    st=[]; lb._send_raw=lambda t: send
    lb._outbox_flush(d,list(new),st); lb._send_raw=o
    rem=[json.loads(l)["tag"] for l in (d/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    shutil.rmtree(d,ignore_errors=True); return st,rem

OLD={"tag":"signal","text":"🟢 ВХОД ДЪЛЪГ 4100","first_ts":"2026-08-19T05:00:00","attempts":1,"hard_fails":1}

print("N+1б  щит пали, НЯМА нова signal карта:")
st,rem=flush([OLD],[("status","борсата диша")]); print("   statuses:",st,"| поща:",rem)

print("\nN+1б' щит пали, НО ОДИТ-26 картата «спряна:long» излиза заедно със status:")
st,rem=flush([OLD],[("спряна:long","👀 виждам сетъп, но US-щит — не предлагам вход"),("status","x")])
print("   statuses:",st,"| поща:",rem)

print("\nконтрола · СЪЩАТА карта, но таг exit:sl (изходна):")
st,rem=flush([dict(OLD,tag="exit:sl")],[("status","x")]); print("   statuses:",st,"| поща:",rem)

print("\nконтрола · таг standing (стоящ сетъп, също «вход»-подобна):")
st,rem=flush([dict(OLD,tag="standing")],[("status","x")]); print("   statuses:",st,"| поща:",rem)
