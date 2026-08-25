# -*- coding: utf-8 -*-
import sys, io, hashlib, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = pathlib.Path(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
src = (ROOT/"live_bot.py").read_bytes()
print("live_bot.py sha256 =", hashlib.sha256(src).hexdigest()[:16], " байта:", len(src))
sys.path.insert(0, str(ROOT))
import os
os.environ.setdefault("TG_TOKEN","x"); os.environ.setdefault("TG_CHAT","1")
import live_bot as L
import pandas as pd, numpy as np, inspect
print("TF_BASIS_CAP =", L.TF_BASIS_CAP, "PCT =", L.TF_BASIS_CAP_PCT, "STUCK_N =", L.TF_BASIS_STUCK_N, "CAP_S =", L.TF_BASIS_CAP_S)
srcf = inspect.getsource(L._tf_basis)
print("_tf_basis ред в файла:", inspect.getsourcelines(L._tf_basis)[1])
print("има ли '_прекъсвач' в _tf_basis:", "_прекъсвач" in srcf)
print("има ли таван по цена:", "TF_BASIS_CAP_PCT" in srcf)
