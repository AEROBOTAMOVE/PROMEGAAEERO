# -*- coding: utf-8 -*-
import sys, io, json, importlib.util
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.argv = ["live_bot.py"]
spec = importlib.util.spec_from_file_location("lb", "live_bot.py")
lb = importlib.util.module_from_spec(spec); spec.loader.exec_module(lb)

rows = [json.loads(l) for l in open('live/live_journal.jsonl', encoding='utf-8') if l.strip()]
r = rows[-1]
b = r['board']
board = [(lbl, v[0], v[1], v[2], "") for lbl, v in b.items()]
rank = {"premium":3,"strong":2,"medium":1,"weak":0}
actionable = [x for x in board if x[1] != "wait" and x[3] != "weak"]
best = max(board, key=lambda x: (rank[x[3]], x[2]))
new_dir = best[1]
price_user = r['spot']

print("ЖИВИ ЧИСЛА от последния рън", r['run_utc'], "версия", r['v'])
print("  дъска:", {k: v for k, v in list(b.items())[:3]}, "...")
print("  best =", best, "| new_dir =", new_dir, "| actionable =", len(actionable))
print("  spot =", price_user)
print()

# 1) ГЕЙТЪТ на новия блок с ЖИВИТЕ стойности
should_sig, weekend, trade = False, False, None
gate = bool(actionable) and bool(new_dir) and (not should_sig) and (not weekend) and (trade is None)
print("ГЕЙТ `actionable and new_dir and not should_sig and not weekend and trade is None`")
print("   ->", gate, "  (тоест блокът СЕ ИЗПЪЛНЯВА при мълчание)")
print()

# 2) реалната причина от живия sent_log
причина = "сетъпът е на 105ч, правилото пуска до 12ч"
обяснение = "мерено: след този таван пределният вход не плаща"
msg = lb._спряна_msg(new_dir, best, price_user, причина, обяснение,
                     lb.pd.Timestamp(r['run_utc']), board)
print("ИЗХОД НА _спряна_msg (ИЗПЪЛНЕН, не прочетен):")
print("-"*60)
print(msg)
print("-"*60)
