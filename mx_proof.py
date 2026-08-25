# -*- coding: utf-8 -*-
import sys, io, json, pathlib, tempfile
sys.argv = ["x"]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import live_bot as lb

d = pathlib.Path(tempfile.mkdtemp(prefix="mx_"))
f = d / "brain_track.json"; j = d / "brain_result.jsonl"
NOW = "2026-08-21T11:20:00+00:00"

нов = {"лонг": True, "рамка": "15м", "степен": "⚡ МНОГО СИЛЕН", "точки": 14,
       "залог": {"вход": 4358.00, "стоп": 4348.00, "цел": 4372.00, "цел2": 4386.00}}
print(">>> отваряне"); print(lb._мозък_следене(f, j, 4358.0, NOW, нов=нов, бар=(4358.5, 4357.5)))
print(">>> удря ЦЕЛ1 (4372)")
for tag, t in lb._мозък_следене(f, j, 4372.0, NOW, бар=(4372.5, 4371.0)): print(tag); print(t)
print(">>> после удря СТОПА (4348)")
for tag, t in lb._мозък_следене(f, j, 4348.0, NOW, бар=(4360.0, 4347.5)): print(tag); print(t)
print(">>> КАКВО Е ЗАПИСАНО В ДНЕВНИКА:")
for ред in j.read_text(encoding="utf-8").splitlines():
    z = json.loads(ред)
    print({k: z[k] for k in ("вход","цел1","цел1_взета","изход","цена_изход","част1","част2","резултат") if k in z})
