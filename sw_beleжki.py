import sys,io,json,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding="utf-8")
c=collections.Counter(); n=0
for ln in open('live/live_journal.jsonl',encoding='utf-8'):
    try: r=json.loads(ln)
    except: continue
    n+=1
    for x in (r.get('notes') or []):
        s=str(x)
        if 'ОБЕМИ' in s: c['ОБЕМИ ще мълчи']+=1
        if 'прескочена' in s: c['прескочена']+=1
        if 'мозък' in s.lower() or '🧠' in s: c['мозък-бележка']+=1
        if 'ГЪРМИ' in s: c['ГЪРМИ']+=1
print('редове в live_journal:',n)
print(dict(c))
