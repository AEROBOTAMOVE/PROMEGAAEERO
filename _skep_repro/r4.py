# -*- coding: utf-8 -*-
import sys, io, json, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
R = pathlib.Path(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
m = json.loads((R/"live/meta.json").read_text(encoding="utf-8"))
for k in sorted(m):
    if "basis" in k or "tf_" in k: print("  %-28s %s" % (k, m[k]))
