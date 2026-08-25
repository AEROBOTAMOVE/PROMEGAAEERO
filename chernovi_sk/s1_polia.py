import json
ks={}; n=0
with open('live/live_journal.jsonl',encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        try: r=json.loads(line)
        except Exception: continue
        n+=1
        for k in r: ks[k]=ks.get(k,0)+1
print('redove:',n)
for k,v in sorted(ks.items(),key=lambda x:-x[1])[:45]: print(f'{v:7d}  {k}')
