# -*- coding: utf-8 -*-
# ПРЕДИ пускане: git show ff5d328a:live_bot.py > <dep>/_skep_lb137.py  (нужно е да е в КОРЕНА, заради brain/)
"""СКЕПТИК/ПОСЛЕДИЦА: възпроизвеждам твърдението за 401/403 САМ, на две версии."""
import sys, io, json, os, shutil, importlib.util
from pathlib import Path

DEP = Path(r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep")
HERE = DEP / "_skep_posl_token"
sys.path.insert(0, str(DEP))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

import urllib.error, urllib.request

def patch(mod, code, desc):
    """урlopen на МОДУЛА да гърми с даден HTTP код и тяло от Телеграм."""
    body = json.dumps({"ok": False, "error_code": code, "description": desc}).encode()
    def fake(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, code, desc, {}, io.BytesIO(body))
    mod.urllib.request.urlopen = fake

def scenario(tag, modpath, modname, code, desc, runs=5):
    print("=" * 72)
    print(f"{tag}   HTTP {code} «{desc}»")
    m = load(modname, modpath)
    print(f"  VERSION={m.VERSION}  POISON_HARD_FAILS={m.POISON_HARD_FAILS}")
    os.environ["TELEGRAM_TOKEN"] = "111:AAA_невалиден"
    os.environ["TELEGRAM_CHAT_ID"] = "-1003827523037"
    patch(m, code, desc)

    out = HERE / f"live_{tag}"
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)

    KARTA = "<b>ЛОНГ 4639</b> вход сега · ТП1 4646.5 · СТОП 4619"
    # едно голо пращане
    print(f"  едно _send_raw → {m._send_raw(KARTA)!r}")

    for i in range(1, runs + 1):
        st = []
        new = [("signal", KARTA)] if i == 1 else []
        exc = None
        try:
            m._outbox_flush(out, new, st, dry=False)
        except SystemExit as e:
            exc = f"SystemExit({str(e)[:90]}…)"
        except Exception as e:
            exc = f"{type(e).__name__}: {e}"
        ob = out / "outbox.jsonl"
        n = len([l for l in ob.read_text(encoding="utf-8").splitlines() if l.strip()]) if ob.exists() else 0
        hf = ""
        if n:
            d = json.loads(ob.read_text(encoding="utf-8").splitlines()[0])
            hf = f" hard_fails={d.get('hard_fails',0)}"
        print(f"  рън {i}: статуси={st}")
        print(f"          останали в пощата={n}{hf}   изключение={exc}")
    return m

MOD137 = str(DEP / "_skep_lb137.py")
MOD141 = str(DEP / "live_bot.py")

scenario("v137_401", MOD137, "lb137a", 401, "Unauthorized")
scenario("v141_401", MOD141, "lb141a", 401, "Unauthorized")
scenario("v141_403", MOD141, "lb141b", 403, "Forbidden: bot was kicked from the supergroup chat")
