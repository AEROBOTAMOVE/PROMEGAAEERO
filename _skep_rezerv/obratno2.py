import json, pathlib, shutil, subprocess, os
HERE=pathlib.Path(__file__).parent
PY=r"C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
def сцена(таг, печат, сега):
    d=HERE/таг
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(HERE.parent/"live", d/"live")
    bp=d/"live"/"macro_backup.json"; b=json.loads(bp.read_text(encoding="utf-8"))
    for k in b: b[k]["utc"]=печат
    bp.write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
    print("#"*78); print(f"# {таг}: печат {печат} · сега {сега}")
    r=subprocess.run([PY,str(HERE/"run1.py"),"lb_nov.py",f"{таг}/live",сега],cwd=str(HERE),
        capture_output=True,text=True,encoding="utf-8",
        env={**os.environ,"PYTHONUTF8":"1","PYTHONIOENCODING":"utf-8"})
    print(r.stdout); print("STDERR:", (r.stderr.strip()[-200:] or "(празен)"))
сцена("F_13dni", "2026-08-08T12:00", "2026-08-21T12:00")   # 13 дни — под ръба
сцена("G_15dni", "2026-08-06T12:00", "2026-08-21T12:00")   # 15 дни — над ръба
сцена("H_3meseca", "2026-05-01T12:00", "2026-08-21T12:00") # 3.5 месеца
