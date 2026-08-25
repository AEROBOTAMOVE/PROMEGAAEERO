import io, hashlib

p = "live_bot.py"
src = io.open(p, encoding="utf-8", newline="").read()
assert "_cell_name" not in src, "кръпката вече е вътре — не дублирай"
before = hashlib.sha256(src.encode("utf-8")).hexdigest()
assert before.startswith("e0c0a0dae88a"), f"НЕ Е живата основа: {before[:14]}"

# ── 1 · ЕДНО име на кофата, ползвано и от дневника ────────────────────────
anchor = "def _noise(seg):"
helper = '''def _cell_name(streak_n):
    """ОДИТ-15: ИМЕТО на кофата, с която `_advice_entry` съди — за да може решението
    да се ЗАПИШЕ в дневника. Дотук гейтът беше единственото важно решение на бота
    БЕЗ трайна следа: `macro` и `board` се пишат (ОДИТ-5), присъдата — не. Затова
    «защо отказа този шорт на 23.07» се четеше по археология в текста на картите,
    а картите отпреди v6.0 дори не носят причината.
    Пази се синхронно с `_advice_entry` чрез ИЗПЪЛНЯВАН тест (П18), не чрез греп."""
    if streak_n == 1:
        return "day1"
    if 2 <= streak_n <= 3:
        return "fresh"
    if streak_n == 0:
        return "mixed"
    return "stale"


'''
assert src.count(anchor) == 1, "котвата _noise не е уникална"
src = src.replace(anchor, helper + anchor, 1)

# ── 2 · записът в дневника ────────────────────────────────────────────────
old = '                             "macro": macro, "macro_raw": macro_health,'
new = ('                             "macro": macro, "macro_raw": macro_health,\n'
       '                             # \U0001f534 ОДИТ-15: присъдата на ГЕЙТА — най-важното решение на бота.\n'
       '                             # Без нея форуърд-тестът е неизмерим: «защо отказа» се\n'
       '                             # реконструира по текста на картите, а старите карти дори\n'
       '                             # не носят причината. САМО ЗАПИС — решението НЕ се променя.\n'
       '                             "gate": ({"dir": new_dir, "streak": streak_n,\n'
       '                                       "cell": _cell_name(streak_n), "ok": bool(_adv_ok),\n'
       '                                       "why": advice_txt} if new_dir else None),')
assert src.count(old) == 1, "котвата на журнала не е уникална"
src = src.replace(old, new, 1)

io.open(p, "wb").write(src.encode("utf-8"))
after = hashlib.sha256(src.encode("utf-8")).hexdigest()
print(f"live_bot.py: {len(src.split(chr(10)))} реда · {before[:14]} → {after[:14]}")
