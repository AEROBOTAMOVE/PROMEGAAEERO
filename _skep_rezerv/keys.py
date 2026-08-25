import json
b=json.load(open(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep/live/macro_backup.json", encoding="utf-8"))
for k,v in b.items():
    print(repr(k), v.get("utc"), len(v.get("csv","")))
