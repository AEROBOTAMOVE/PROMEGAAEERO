import json, pathlib, shutil, subprocess, sys
HERE = pathlib.Path(__file__).parent
PY = r"C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
def сцена(таг, печат, сега):
    d = HERE / taгdir if False else HERE / таг
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(HERE.parent / "live", d / "live")
    bp = d / "live" / "macro_backup.json"
    b = json.loads(bp.read_text(encoding="utf-8"))
    for k in b: b[k]["utc"] = печат
    bp.write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
    print("#"*78); print(f"# {таг}: печат {печат} · сега {сега}")
    r = subprocess.run([PY, str(HERE/"run1.py"), "lb_nov.py", f"{таг}/live", сега],
                       cwd=str(HERE), capture_output=True, text=True, encoding="utf-8",
                       env={**__import__("os").environ, "PYTHONUTF8":"1","PYTHONIOENCODING":"utf-8"})
    print(r.stdout); print("STDERR:", r.stderr.strip()[-300:] if r.stderr.strip() else "(празен)")
# 1) НАИСТИНА застоял резерв в ОТВОРЕН пазар (сряда→сряда след 8 дни) — трябва да се ОТХВЪРЛИ
сцена("C_star_zhiv", "2026-08-11T12:00", "2026-08-19T12:00")
# 2) Застой 40 ТЪРГОВСКИ часа (понеделник обед → сряда сутрин) — трябва да се ОТХВЪРЛИ
сцена("D_40ch", "2026-08-17T12:00", "2026-08-19T08:00")
# 3) Застой 20 търговски часа — трябва да МИНЕ
сцена("E_20ch", "2026-08-18T12:00", "2026-08-19T08:00")
