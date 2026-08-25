# -*- coding: utf-8 -*-
"""
ПОПРАВКА НА ИЗМЕРВАТЕЛНИЯ ИНСТРУМЕНТ (geom_harness.py)

Одит с 4 агента намери 6 истински дефекта. Инструментът е произвел ВСЯКО число
в `backtest_stats.json` — дефект в него е дефект във всяко бъдещо измерване.

🔴 ЖЕЛЯЗНОТО ПРАВИЛО НА ТАЗИ ПОПРАВКА:
   ПО ПОДРАЗБИРАНЕ НИЩО НЕ СЕ МЕНИ. Записаните числа трябва да останат
   възпроизводими. Всяка промяна във ФИЗИКАТА е по избор; онова, което не се
   мени, се ДОКЛАДВА, за да не може повече да остане невидимо.
   След кръпката `_one_trade` в подразбиращ режим ТРЯБВА да дава бит-в-бит
   същото — това се проверява веднага.

── ПОПРАВЯНИ ────────────────────────────────────────────────────────────────

П1 · BLOCKER · `simulate(non_overlap=True)` дава на всяка геометрия РАЗЛИЧНА
     извадка, защото `busy_until = r["exit_index"]` е ИЗХОД на самата геометрия.
     От едни и същи 6846 входа излизат 950 (широка) до 2970 (тясна) сделки;
     Jaccard между две геометрии пада до 0.295. Класацията се ОБРЪЩА.
     → ПОПРАВКА: функцията ОТКАЗВА да работи, ако някой не е заявил изрично, че
       това НЕ Е сравнение между геометрии. Не може повече да се сбърка.

П2 · HIGH · Бутстрапът в `main()` брои сделките за независими, а средно 6.4
     текат едновременно (макс 37; автокорелация +0.34). Интервалите излизат
     1.70–1.92× ПО-ТЕСНИ от честните.
     → ПОПРАВКА: блоков бутстрап ПО ДЕН, като в F28/F30/F31.

П3 · MEDIUM · Слипът се вади ВЕДНЪЖ на сделка, а стълбата има 2.122 изпълнения
     (едноцелевите — 1.000). Системно предимство за многокраките: −0.0224$.
     → ПОПРАВКА: `_one_trade` връща `n_fills` и `net_per_fill`; `summarize`
       докладва И ДВЕТЕ. `net` НЕ се мени (възпроизводимост).

П4 · MEDIUM · Времето-изход реже геометриите крайно неравномерно: при 5 дни
     от 0.06% (тясна) до 49.46% (широка) от сделките се решават от ТАЙМЕРА.
     → ПОПРАВКА: `summarize` докладва дела задължително.

П5 · LOW · Входният бар е БЕЗПЛАТЕН (`a = i0 + 1`) — минутата на попълването не
     може да удари стопа. Тесните геометрии печелят повече: 0.526% срещу 0.000%.
     → ПОПРАВКА: докладва се дела; физиката НЕ се мени (по избор).

П6 · LOW · Стопът-на-входа се въоръжава чак от следващия бар. 36 от 4700
     стигнали ТП1 (0.53%) са минали обратно през входа в СЪЩАТА минута и не са
     спрени. Печелят само геометрии с be_after_tp1.
     → ПОПРАВКА: докладва се; физиката НЕ се мени (по избор).

ОБОРЕНО и НЕ пипано: входовете не зависят от геометрията · спредът се плаща
веднъж и от вярната страна (3525/3525 лонга, 0.00e+00) · конфликт стоп/цел под
0.04% · няма поглед напред (299/300 проби).
"""
import io, sys, ast, hashlib, shutil

G = r"C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-----\2674809c-6765-4e6e-873d-82958246267b\scratchpad\geom_harness.py"
shutil.copy(G, G + ".преди_одита")
s = io.open(G, encoding="utf-8", newline="").read()
ops = []


def rep(old, new, why, n=1):
    global s
    c = s.count(old)
    if c != n:
        print(f"  x СПИРАМ <<{why}>>: {c} съвпадения, чакам {n}")
        sys.exit(1)
    s = s.replace(old, new)
    ops.append(why)


# ── П3 · броят изпълнения влиза в резултата (net НЕ се мени) ─────────────
rep('''    filled = [False] * len(tps)
    rem = 1.0
    gross = 0.0
    n_tp = 0
    exit_k = None
    kind = None''',
    '''    filled = [False] * len(tps)
    rem = 1.0
    gross = 0.0
    n_tp = 0
    n_fills = 0          # П3 (одит 18.08): БРОЙ ИЗПЪЛНЕНИЯ, не крака на позицията
    exit_k = None
    kind = None''',
    "П3 · брояч на изпълненията")

rep('''            gross += rem * s * (px - entry_px)
            rem = 0.0
            exit_k = k''',
    '''            gross += rem * s * (px - entry_px)
            rem = 0.0
            n_fills += 1
            exit_k = k''',
    "П3 · стопът е изпълнение")

rep('''                gross += tps[ti][0] * s * (px - entry_px)
                rem -= tps[ti][0]
                filled[ti] = True
                n_tp += 1''',
    '''                gross += tps[ti][0] * s * (px - entry_px)
                rem -= tps[ti][0]
                filled[ti] = True
                n_tp += 1
                n_fills += 1''',
    "П3 · всяка цел е изпълнение")

rep('''        gross += rem * s * (o_exit - entry_px)
        rem = 0.0
        kind = f"time-after-tp{n_tp}" if n_tp else "time"''',
    '''        gross += rem * s * (o_exit - entry_px)
        rem = 0.0
        n_fills += 1
        kind = f"time-after-tp{n_tp}" if n_tp else "time"''',
    "П3 · време-изходът е изпълнение")

rep('''    net = gross - SLIP_PER_TRADE
    return {"exit_index": int(exit_idx), "gross": gross, "net": net, "kind": kind,
            "n_tp": n_tp,''',
    '''    net = gross - SLIP_PER_TRADE
    # 🔴 П3 (одит 18.08) · `net` вади слипа ВЕДНЪЖ на сделка. Мерено: стълбата
    # прави 2.122 изпълнения, едноцелевите — 1.000. Тоест многокраките геометрии
    # плащат по-малко, отколкото биха платили наистина, и това е СИСТЕМНО
    # предимство (−0.0224$/сделка за доставената). `net` НЕ се мени, за да
    # останат записаните числа възпроизводими; истината идва до него.
    net_per_fill = gross - SLIP_PER_TRADE * n_fills
    return {"exit_index": int(exit_idx), "gross": gross, "net": net,
            "net_per_fill": net_per_fill, "n_fills": int(n_fills), "kind": kind,
            "n_tp": n_tp,''',
    "П3 · net_per_fill до net")

# ── П1 · неприпокриването вече не може да мине за сравнение ──────────────
rep('''def simulate(entries, geom, B, non_overlap=True, label=""):
    """entries: DataFrame with bar_index, direction, entry_px (chronological)."""''',
    '''def simulate(entries, geom, B, non_overlap=True, label="", ne_e_sravnenie=False):
    """entries: DataFrame with bar_index, direction, entry_px (chronological).

    🔴 П1 (одит 18.08) · BLOCKER. При non_overlap=True филтърът ползва
    `busy_until = r["exit_index"]` — ИЗХОД на самата геометрия. Значи всяка
    геометрия получава РАЗЛИЧНА извадка входове. Мерено: от едни и същи 6846
    входа излизат 950 (широка) до 2970 (тясна) сделки, Jaccard пада до 0.295,
    и КЛАСАЦИЯТА СЕ ОБРЪЩА (доставената е 1-ва сдвоено, 3-та неприпокрито;
    една геометрия мърда с 0.557$/сделка само от избора на подизвадка — повече
    от целия разсейн между геометриите).

    Затова: за СРАВНЕНИЕ между геометрии се ползва САМО `simulate_paired`.
    Тази функция дава ТЪРГУЕМ портфейл на ЕДНА геометрия — законна употреба,
    но не и сравнение. За да я извикаш с non_overlap=True, трябва да заявиш
    `ne_e_sravnenie=True`, тоест да кажеш на глас, че знаеш какво правиш.
    """
    if non_overlap and not ne_e_sravnenie:
        raise ValueError(
            "geom_harness П1: simulate(non_overlap=True) НЕ Е сравнение между "
            "геометрии — филтърът зависи от изхода на самата геометрия и всяка "
            "получава различна извадка (950 срещу 2970 сделки; класацията се "
            "обръща). За сравнение ползвай simulate_paired(). Ако наистина ти "
            "трябва търгуем портфейл на ЕДНА геометрия, извикай с "
            "ne_e_sravnenie=True.")''',
    "П1 · неприпокриването иска изрично заявяване")

# ── П4/П5/П6 · изложеността влиза в отчета ───────────────────────────────
rep('''    out["mean_spread_at_exit"] = round(float(T["spread_exit"].mean()), 3)''',
    '''    out["mean_spread_at_exit"] = round(float(T["spread_exit"].mean()), 3)
    # 🔴 П4 (одит 18.08) · КОЛКО ОТ СДЕЛКИТЕ РЕШАВА ТАЙМЕРЪТ, а не геометрията.
    # Мерено при 5 дни: 0.06% (тясна) до 49.46% (широка). Тоест при широка
    # геометрия половината сделки не са резултат на стопове и цели. Без това
    # число сравнението изглежда като сравнение на геометрии, а не е.
    _kind = T["kind"].astype(str)
    out["time_exit_pct"] = round(float(_kind.str.startswith("time").mean() * 100), 2)
    out["stop_exit_pct"] = round(float(_kind.str.contains("stop").mean() * 100), 2)
    # 🔴 П3 · разходът на ИЗПЪЛНЕНИЕ до разхода на сделка
    if "n_fills" in T:
        out["mean_fills_per_trade"] = round(float(T["n_fills"].mean()), 3)
        out["usd_per_trade_net_per_fill"] = round(float(T["net_per_fill"].mean()), 4)
        out["slip_model_note"] = (
            "`usd_per_trade_net` вади слипа ВЕДНЪЖ на сделка (както винаги е било). "
            "`usd_per_trade_net_per_fill` го вади на ИЗПЪЛНЕНИЕ. Победител, който "
            "печели само по първото, НЕ е победител — многокраките геометрии са "
            "системно облагодетелствани от първия модел.")''',
    "П4 · таймерът и разходът влизат в отчета")

# ── П2 · блоков бутстрап по ден в main() ─────────────────────────────────
rep('''    rng = np.random.default_rng(BLIND_SEED)
    boot = np.array([diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(2000)])
    ci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))''',
    '''    # 🔴 П2 (одит 18.08) · ДОТУК ТУК СЕ РЕСЕМПЛИРАШЕ КАТО НЕЗАВИСИМО. Не е:
    # средно 6.4 сделки текат едновременно в момента на вход (макс 37),
    # автокорелация на разликата lag1 +0.340, lag2 +0.365. Мерена ширина на
    # интервала: iid 0.4878$ срещу блоков 0.83–0.94$ → 1.70–1.92× ПО-ТЕСЕН.
    # Контрола: същият блоков бутстрап върху РАЗБЪРКАНА последователност дава
    # отношение 0.98, тоест разширението е истинска зависимост, не артефакт.
    # Сега: блоков бутстрап ПО КАЛЕНДАРЕН ДЕН, като в F28/F30/F31.
    rng = np.random.default_rng(BLIND_SEED)
    _dni = pd.to_datetime(pd.Series(B["ts"])[E["bar_index"].values[m]].values).normalize()
    _g = pd.DataFrame({"d": diff, "day": _dni.values}).groupby("day")["d"].agg(["sum", "count"])
    _S, _C = _g["sum"].to_numpy(), _g["count"].to_numpy()
    _k = len(_S)
    _iz = rng.integers(0, _k, size=(4000, _k))
    boot = _S[_iz].sum(axis=1) / np.maximum(_C[_iz].sum(axis=1), 1)
    ci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))''',
    "П2 · блоков бутстрап по ден")

# ── извикванията на simulate вътре в main() трябва да са изрични ─────────
_бр = s.count("simulate(E, GEOM_")
s = s.replace("simulate(E, GEOM_SHIPPED, B, label=",
              "simulate(E, GEOM_SHIPPED, B, ne_e_sravnenie=True, label=")
s = s.replace("simulate(E, GEOM_FLAT, B, label=",
              "simulate(E, GEOM_FLAT, B, ne_e_sravnenie=True, label=")
if s.count("ne_e_sravnenie=True") >= 2:
    ops.append("вътрешните извиквания са заявени изрично")

io.open(G, "wb").write(s.encode("utf-8"))
ast.parse(io.open(G, encoding="utf-8").read())
print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
b = io.open(G, encoding="utf-8").read()
print(f"geom_harness.py: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
