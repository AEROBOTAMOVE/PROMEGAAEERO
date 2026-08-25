import json, sys
from pathlib import Path
st = json.load(open(Path(__file__).resolve().parent / "backtest_stats.json", encoding="utf-8"))
def w(k, d):
    if isinstance(d, dict) and "net" in d:
        print(f"{k}: win={d.get('win')} net={d.get('net')} n={d.get('n')} ci={d.get('ci')}")
        return
    if isinstance(d, dict):
        for kk, vv in d.items(): w(k + "/" + str(kk), vv)
for k, v in st.items():
    if k == "_meta": continue
    w(k, v)
print("--- _meta keys:", list(st.get("_meta", {}).keys()))
print("тишина:", json.dumps(st["_meta"].get("тишина_мерена"), ensure_ascii=False))
for kk in ("зони", "зона", "zones"):
    if kk in st.get("_meta", {}): print(kk, json.dumps(st["_meta"][kk], ensure_ascii=False)[:800])
