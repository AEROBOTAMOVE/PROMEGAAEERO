import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
D = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-----/2674809c-6765-4e6e-873d-82958246267b/scratchpad/dep"
sys.path.insert(0, D)
import live_bot as lb
meta = {"basis_s": 0.031, "basis_s_bar": 69.505, "last_spot_s": 69.451}
notes=[]; s_bar=69.505
for i in range(1, 41):
    raw={"bid":74.48,"ask":74.52,"mid":74.5,"src":"swq"}
    jump=abs(74.5-meta["last_spot_s"]); meta["last_spot_s"]=74.5
    b=lb._basis_update(meta,"basis_s",raw,s_bar,notes,cap=lb._basis_cap(s_bar,"XAGUSD"),
                       now_utc="2026-08-21T18:00",скок=lb._roll_jump(s_bar,"XAGUSD"))
    sp=lb._spot_sane(raw, s_bar-b, max(0.30, lb.SPOT_TOL_PCT*abs(s_bar)), bar_rng=0.15, spot_jump=jump)
    if sp is not None:
        print(f"САМОВЪЗСТАНОВЯВАНЕ на рън {i}: базис={b:+.3f}, санити ПУСКА")
        print("  отключваща бележка:", [n for n in notes if "🔓" in n or "закот" in n][-1:])
        break
else:
    print("НЕ се възстанови за 40 ръна")
print("BASIS_STUCK_N =", getattr(lb,"BASIS_STUCK_N",None), "· РЕЗЕРВА_ОТКОТВИ =", getattr(lb,"РЕЗЕРВА_ОТКОТВИ",None))
print("_basis_cap(69.505,'XAGUSD') =", lb._basis_cap(69.505,"XAGUSD"))
