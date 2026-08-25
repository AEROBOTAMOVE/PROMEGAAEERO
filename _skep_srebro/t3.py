import sys, os, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, D)
import live_bot as lb

meta = {"basis_s": 0.031, "basis_s_bar": 69.505, "last_spot_s": 69.451}
notes = []
print("ЗАЩИТА? Симулация: 30 ръна, спотът СКАЧА с 5$ (санитито със сигурност реже).")
print("Въпрос: замръзва ли базисът (шаблонът «злато»), или се самопоправя?")
s_bar = 69.505
for i in range(30):
    spot_mid = 74.5              # скочило сребро, разминава 5$ от бар-базис
    raw = {"bid": spot_mid-0.02, "ask": spot_mid+0.02, "mid": spot_mid, "src": "swq"}
    jump = abs(raw["mid"] - meta["last_spot_s"])
    meta["last_spot_s"] = raw["mid"]
    b = lb._basis_update(meta, "basis_s", raw, s_bar, notes,
                         cap=lb._basis_cap(s_bar, "XAGUSD"), now_utc="2026-08-21T18:00",
                         скок=lb._roll_jump(s_bar, "XAGUSD"))
    tol = max(0.30, lb.SPOT_TOL_PCT*abs(s_bar))
    sp = lb._spot_sane(raw, s_bar - b, tol, bar_rng=0.15, spot_jump=jump)
    if i in (0,1,2,3,5,9,29):
        print(f"  рън {i+1:2}: базис={b:+.3f}  реф={s_bar-b:.3f}  спот={spot_mid}  санити={'ПУСКА' if sp else 'РЕЖЕ'}")
print("бележки:", notes[:4])
print()
print("Сравнение — ЗЛАТНИЯТ дефект (фиксиран таван 40$) върху СЪЩАТА симулация:")
meta2 = {"basis_g": 25.5, "basis_g_bar": 4600.0}
n2 = []
for i in range(30):
    raw = {"bid": 4591.0, "ask": 4592.0, "mid": 4591.5, "src": "swq"}
    b = lb._basis_update(meta2, "basis_g", raw, 4639.24, n2, cap=40.0, now_utc="2026-08-21T18:00")
    if i in (0, 29):
        print(f"  рън {i+1:2}: базис={b:+.3f} (истинският е 47.74) → санити реже завинаги")
