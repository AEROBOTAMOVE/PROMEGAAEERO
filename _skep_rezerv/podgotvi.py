import json, shutil, pathlib, re
BASE = pathlib.Path(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
HERE = BASE / "_skep_rezerv"
src = (BASE / "live_bot.py").read_text(encoding="utf-8")
# А · НОВИЯТ (както е в момента в live_bot.py)
(HERE / "lb_nov.py").write_text(src, encoding="utf-8")
# Б · СТАРИЯТ (връщам ЕДИН ред към стенно броене — точно както твърди находката)
star = src.replace("if _въз_т <= СТАР_МАКРО_Ч and _рез.get(\"csv\"):",
                   "if _въз <= СТАР_МАКРО_Ч and _рез.get(\"csv\"):")
assert star != src, "редът не е намерен!"
(HERE / "lb_star.py").write_text(star, encoding="utf-8")
print("разлика в един ред:", sum(1 for a,b in zip(src.splitlines(), star.splitlines()) if a!=b))
for tag in ("A_nov", "B_star"):
    d = HERE / tag
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(BASE / "live", d / "live")
    bp = d / "live" / "macro_backup.json"
    b = json.loads(bp.read_text(encoding="utf-8"))
    for k in b: b[k]["utc"] = "2026-08-14T20:56"     # ПЕТЪЧНИЯТ печат, мерен от журнала
    bp.write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
    print(tag, "готово; печати:", {k: v["utc"] for k, v in b.items()})
