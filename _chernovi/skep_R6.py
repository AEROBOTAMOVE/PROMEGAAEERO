# -*- coding: utf-8 -*-
import sys, io, subprocess, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
log = subprocess.run(['git','log','--format=%H %s','-30','--','live_bot.py'],
                     capture_output=True).stdout.decode('utf-8','replace').splitlines()
for L in log:
    h, _, subj = L.partition(' ')
    b = subprocess.run(['git','show',f'{h}:live_bot.py'], capture_output=True).stdout
    if not b: continue
    s = b.decode('utf-8','replace')
    sha = hashlib.sha256(b).hexdigest()[:8]
    ред = next((i+1 for i,l in enumerate(s.splitlines()) if l.startswith('def _reentry_ban')), None)
    има_дата = 'ден=None' in s
    маркер = '  ⟵⟵ 68bf672b !!' if sha == '68bf672b' else ''
    print(f"{sha}  def@{ред}  дата_фикс={'ДА' if има_дата else 'НЕ'}  {subj[:52]}{маркер}")
# работното дърво
b = open('live_bot.py','rb').read()
ред = next((i+1 for i,l in enumerate(b.decode('utf-8').splitlines()) if l.startswith('def _reentry_ban')), None)
print(f"{hashlib.sha256(b).hexdigest()[:8]}  def@{ред}  дата_фикс={'ДА' if b'\xd0\xb4\xd0\xb5\xd0\xbd=None' in b else 'НЕ'}  ⟵ РАБОТНО ДЪРВО (сега)")
