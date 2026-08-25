# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/_chernovi")
import harness as H

H.patch()
H.CFG.update(gold_end="2026-08-19", intra_end="2026-08-19 12:00", gold_px=4600.0, spot_mid=4600.0)
out = H.fresh("_chernovi/sand0")
log = H.run(out)
print(log[-2500:])
print("=== ПОСЛЕДЕН РЕД В ДНЕВНИКА ===")
r = H.last_journal(out)
for k in ("run_utc","date","bar","spot","basis","tf_basis","status","notes"):
    print(" ", k, "=", r.get(k))
print("=== meta.json ===")
print(json.dumps(json.load(open(out/"meta.json", encoding="utf-8")), ensure_ascii=False, indent=1))
