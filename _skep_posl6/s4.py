import sys, pathlib, tempfile, json
sys.path.insert(0, r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
import live_bot as lb
d = pathlib.Path(tempfile.mkdtemp())
карта = lb._сухо_msg(24, "фийдът за живата цена мълчи", None, "2026-08-19T14:00:00Z")
st = []
tags = lb._outbox_flush(d, [("сухо", карта)], st, dry=True)
print("пратени тагове (dry):", tags, "| статуси:", st)
print("останало в пощата:", [json.loads(l)["tag"] for l in (d/"outbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()] if (d/"outbox.jsonl").exists() else "няма файл")
