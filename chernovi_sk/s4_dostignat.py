import json, ast, io

src = io.open('live_bot.py', encoding='utf-8').read()
lines = src.splitlines()
i_guard = next(i for i, l in enumerate(lines) if 'СУХИТЕ РЪНА' in l)
i_jrnl = next(i for i, l in enumerate(lines)
              if i > i_guard and '"run_ended": run_ended' in l)
print('blok-pazach zapochva na red', i_guard + 1)
print('zapisyt v dnevnika e na red', i_jrnl + 1, '-> SLED pazacha:', i_jrnl > i_guard)

# ima li RETURN v main() mezhdu spot-a i pazacha, koyto bi prepusnal bloka?
tree = ast.parse(src)
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
rets = [n.lineno for n in ast.walk(main) if isinstance(n, ast.Return)]
print('return-i v main():', rets)
print('ot tyah mezhdu red 3400 i pazacha:', [r for r in rets if 3400 < r < i_guard + 1])

# DOKAZATELSTVO ot realnite danni: dostigali li sa suhite ryna do zapisa?
runs = []
for line in io.open('live/live_journal.jsonl', encoding='utf-8'):
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except Exception:
        continue
    if r.get('weekend') or 'spot' not in r:
        continue
    runs.append(r)
runs.sort(key=lambda r: r['run_utc'])
avar = [r for r in runs if '2026-08-19T13:16' <= r['run_utc'] <= '2026-08-20T14:56']
suhi = [r for r in avar if r.get('spot') is None]
print()
print('ryna v prozoreca na avariyata:', len(avar), '| ot tyah suhi:', len(suhi))
print('suhi ryna s run_ended (t.e. stignali do reda SLED pazacha):',
      sum(1 for r in suhi if r.get('run_ended')))
print('suhi ryna BEZ run_ended:', sum(1 for r in suhi if not r.get('run_ended')))
