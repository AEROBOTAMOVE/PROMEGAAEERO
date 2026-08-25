import sys
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
src = open("live_bot.py", encoding="utf-8").read().splitlines()
i = next(k for k,l in enumerate(src) if "raw_g is None and not weekend" in l)
блок = "\n".join(x[4:] for x in src[i:i+5])
print("=== редове", i+1, "-", i+5, "===\n"+блок+"\n")
for име, сл in (("мъртва мрежа", [('swq','URLError'),('paxg-bin','URLError'),('paxg-cb','URLError'),('paxg-kr','URLError')]),
                ("сменена схема", [('swq','KeyError'),('paxg-bin','HTTPError'),('paxg-cb','URLError'),('paxg-kr','KeyError')])):
    ctx = {"raw_g": None, "weekend": False, "_cme_pause": lambda x: False,
           "now_utc": "2026-08-19T14:00:00Z", "_сл_g": сл, "notes": []}
    exec(блок, ctx)
    print(f"{име:14s} → бележка: {ctx['notes']}")
ctx = {"raw_g": None, "weekend": False, "_cme_pause": lambda x: True,
       "now_utc": "2026-08-19T21:00:00Z", "_сл_g": [('swq','URLError')], "notes": []}
exec(блок, ctx)
print(f"{'CME пауза':14s} → бележка: {ctx['notes']}  (правилно мълчи)")
