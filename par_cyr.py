# -*- coding: utf-8 -*-
import os, sys, subprocess
os.environ["МОЗЪК_ПРАГ"]="9"
r=subprocess.run([sys.executable,"-c","import os;print(repr(os.environ.get('МОЗЪК_ПРАГ')))"],
                 capture_output=True, text=True, encoding="utf-8", env=os.environ)
print("подпроцес вижда кирилския ключ:", r.stdout.strip(), r.stderr.strip()[:200])
