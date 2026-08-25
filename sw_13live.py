import sys, json, collections
sys.stdout.reconfigure(encoding='utf-8')
rows=[json.loads(l) for l in open('live/sent_log.jsonl',encoding='utf-8') if l.strip()]
print("записи:", len(rows), rows[0]['utc'], rows[-1]['utc'])
bym=collections.OrderedDict()
for r in rows: bym.setdefault(r['utc'],[]).append(r['tag'])
def is_exit(t): return t.split(':')[0] in ('exit','s-exit','shadow','s-shadow','мозък-изход','brain-exit')
def is_sig(t): return t.split(':')[0] in ('signal','s-signal','brain')
bad=0; tot=0
for utc,tags in bym.items():
    ex=[i for i,t in enumerate(tags) if is_exit(t)]
    sg=[i for i,t in enumerate(tags) if is_sig(t)]
    if ex and sg:
        tot+=1
        if min(sg)<max(ex):
            bad+=1
            if bad<=8: print("НАРУШЕН РЕД", utc, tags)
print(f"минути с изход+вход: {tot}; вход преди изход: {bad}")
print("всички тагове:", sorted({t.split(':')[0] for r in rows for t in [r['tag']]}))
