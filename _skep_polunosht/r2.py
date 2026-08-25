import sys, json, os
D=r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0,D)
import live_bot as B

print("1) sushtestvuva li daily_context.json v repo root?", os.path.exists(D+"/daily_context.json"))
notes=[]
print("2) _daily_ctx('daily_context.json', ...) ->", B._daily_ctx(D+"/daily_context.json","2026-08-21",notes), "| notes:",notes)
print("3) _event_shield(None, now) ->", B._event_shield(None,"2026-08-20T21:05"))

# --- realniyat jurnal: kolko puti shield e bil True i obyasnyava li go US-prozoreca ---
tot=0; sh=0; sh_us=0; sh_ne_us=0; primeri=[]
with open(D+"/live/live_journal.jsonl",encoding="utf-8") as f:
    for ln in f:
        try: r=json.loads(ln)
        except Exception: continue
        if "shield" not in r: continue
        tot+=1
        if r.get("shield"):
            sh+=1
            u=r.get("run_utc") or r.get("utc")
            if u and B._in_shield(str(u)[:16]): sh_us+=1
            else:
                sh_ne_us+=1
                if len(primeri)<5: primeri.append(u)
print(f"4) zapisi s pole 'shield': {tot} | shield=True: {sh} | ot tyah obyasneni ot US-prozoreca: {sh_us} | NEobyasneni: {sh_ne_us}")
print("   primeri neobyasneni:",primeri)
