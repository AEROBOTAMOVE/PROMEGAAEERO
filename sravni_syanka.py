# -*- coding: utf-8 -*-
"""
AERO ВЕРОЯТНОСТ · сравнението на сянката (PLAN_SYANKA.md §6).

    python sravni_syanka.py --live <репото на бота>/live [--ot 2026-10-23] [--do 2026-11-06] [--json изход.json]
    python sravni_syanka.py --proba          ← пробата на самото сравнение (синтетични файлове с известен отговор)

Чете live/veroyatnost_sianka.jsonl (редовете «vhod», «karta», «fon» на сянката) и live/closed_trades.jsonl
(затворените златни сделки по закона ТП123: "pips" = най-високата стигната цел или −130/0/ходът, "best")
и ги съединява по (opened, direction) — `pending_trade["opened"]` е същият низ и в двата файла.

Казва за всяко състояние при входа: сделки, дни, средно пипса ПО ЗАКОНА и НА ПОЗИЦИЯТА, дял ТП1, дял стоп,
базата на модела (случаен вход по закона при същия спред, двата начина на броене на бота) и ръба над нея.
После разликата «останалите − ЧИСТО» с интервал от блоков бутстрап по ден и ПРЕДВАРИТЕЛНО ЗАПИСАНОТО
правило (записано на 22.10, преди първия ред на сянката):
    гейтът за състояние S се включва САМО ако
      (а) S има ≥ 20 сделки в ≥ 5 различни дни;
      (б) S е по-лошо от ЧИСТО по закона: едностранното p от разбъркване на етикетите ВЪТРЕ в деня минава
          Холм (α = 0,05 за трите S); бутстрапът по ден е само интервалът в отчета;
      (в) и на позицията точковата разлика е със същия знак (S по-лошо);
      (г) S заема ≤ 50 % от пазарното време (редовете «fon») — иначе гейтът ще изяде бота и решава собственикът.
    Не мине ли — сянката продължава още 2 седмици; след 6 седмици без (б) състоянието е «без ефект» и гейтът
    за него остава 0 (без нови мерения).
Без наклон моделът казва, че състоянието НЕ мени очакването по закона при T = ∞ (то зависи само от спреда);
значи сравнението мери точно това, което моделът не вижда: гапове, обрат, време, разширен спред.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
import tempfile

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

TUK = os.path.dirname(os.path.abspath(__file__))
PIP = 0.10
SASTOYANIYA = ("ВЗРИВ", "СКЪПО", "МЪРТВО")
MIN_N, MIN_DNI, ALFA, MAX_FON = 20, 5, 0.05, 0.50
B_BUTSTRAP, R_PERM, SEME = 10000, 10000, 20261023


def _av():
    spec = importlib.util.spec_from_file_location("aero_veroyatnost", os.path.join(TUK, "aero_veroyatnost.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


AV = _av()


def _chete(pat):
    """Редовете на jsonl → (списък, брой нечетими). Липсващ файл → ([], 0)."""
    if not os.path.exists(pat):
        return [], 0
    redove, losh = [], 0
    with open(pat, encoding="utf-8") as fh:
        for ln in fh:
            if not ln.strip():
                continue
            try:
                redove.append(json.loads(ln))
            except Exception:
                losh += 1
    return redove, losh


def _baza(s):
    """Случаен вход по закона при спред s (пипса), T = ∞: (броене по бар = s/2, броене по жива цена)."""
    if s is None or not (0 <= s < 130):
        return None, None
    L = AV.ladder(50, 100, 130, 130, s=s / 2.0, sigma=10.0)
    c = L["c_zakon"]                                    # E[закон | ТП1] = 86,538 (не зависи от s)
    p_ziva = (130 - s / 2.0) / (50 + s + 130 - s / 2.0)  # целта по bid (+X+s), стопът по средата (−(Y−s/2))
    return L["E_zakon"], p_ziva * c - 130 * (1 - p_ziva)


def _p_tp1_model(s):
    if s is None:
        return None, None
    return (130 - s / 2.0) / 180.0, (130 - s / 2.0) / (180.0 + s / 2.0)


def sabiraj(live, ot=None, do=None):
    """Съединява сянката и затворените → речник с всичко за отчета."""
    sianka, losh_s = _chete(os.path.join(live, "veroyatnost_sianka.jsonl"))
    zatv, losh_z = _chete(os.path.join(live, "closed_trades.jsonl"))
    v_ok = lambda d: (ot is None or d >= ot) and (do is None or d <= do)
    vhod = {}
    for r in sianka:
        if r.get("ev") == "vhod" and r.get("opened") and r.get("dir"):
            if v_ok(str(r["opened"])[:10]):
                vhod[(str(r["opened"])[:16], r["dir"])] = r
    sdelki, bez_sianka = [], 0
    vidyani = set()
    for z in zatv:
        if "start" in z or z.get("pips") is None or not z.get("opened"):
            continue
        k = (str(z["opened"])[:16], z.get("direction"))
        if not v_ok(k[0][:10]):
            continue
        r = vhod.get(k)
        if r is None:
            bez_sianka += 1
            continue
        if k in vidyani:                                 # затворена веднъж — броим веднъж
            continue
        vidyani.add(k)
        zn = 1.0 if z.get("direction") == "long" else -1.0
        try:
            poz = round((float(z["exit"]) - float(z["entry"])) * zn / PIP, 1)
        except Exception:
            poz = None
        sdelki.append({"den": k[0][:10], "st": r.get("sastoyanie") or "БЕЗ_ДАННИ", "zakon": float(z["pips"]),
                       "poz": poz, "best": int(z.get("best") or 0), "s": r.get("s"), "staro": r.get("staro")})
    otvoreni = len(set(vhod) - vidyani)
    fon = [r for r in sianka if r.get("ev") == "fon" and v_ok(str(r.get("utc", ""))[:10])]
    karti = [r for r in sianka if r.get("ev") == "karta" and v_ok(str(r.get("utc", ""))[:10])]
    return {"sdelki": sdelki, "bez_sianka": bez_sianka, "otvoreni": otvoreni, "fon": fon, "karti": karti,
            "losh": losh_s + losh_z, "n_sianka": len(sianka)}


def _grupa(sd):
    if not sd:
        return {"n": 0, "dni": 0}
    z = np.array([x["zakon"] for x in sd])
    pz = np.array([x["poz"] for x in sd if x["poz"] is not None])
    bazi = [_baza(x["s"]) for x in sd]
    b_bar = [b[0] for b in bazi if b[0] is not None]
    b_ziva = [b[1] for b in bazi if b[1] is not None]
    resheni = [x for x in sd if x["best"] >= 1 or x["zakon"] <= -129.5]
    p_mod = [_p_tp1_model(x["s"]) for x in resheni if x["s"] is not None]
    return {"n": len(sd), "dni": len({x["den"] for x in sd}),
            "zakon": float(z.mean()), "poz": float(pz.mean()) if pz.size else None,
            "tp1": float(np.mean([x["best"] >= 1 for x in sd])), "stop": float(np.mean(z <= -129.5)),
            "baza_bar": float(np.mean(b_bar)) if b_bar else None, "baza_ziva": float(np.mean(b_ziva)) if b_ziva else None,
            "rab_bar": float(z.mean() - np.mean(b_bar)) if b_bar else None,
            "n_resheni": len(resheni),
            "p_tp1_parvo": float(np.mean([x["best"] >= 1 for x in resheni])) if resheni else None,
            "p_model": (float(np.mean([p[0] for p in p_mod])), float(np.mean([p[1] for p in p_mod])))
            if p_mod else None}


def butstrap_razlika(A, Bg, pole="zakon", B=B_BUTSTRAP, seme=SEME):
    """Разликата mean(A) − mean(B) с блоков бутстрап по ден (денят се тегли цял, с всичките си сделки).
    → (точкова, долна 2,5 %, горна 97,5 %, едностранно p = P*(разлика ≥ 0), брой ползвани тегления)."""
    A = [x for x in A if x.get(pole) is not None]
    Bg = [x for x in Bg if x.get(pole) is not None]
    if not A or not Bg:
        return None
    dni = sorted({x["den"] for x in A} | {x["den"] for x in Bg})
    idx = {d: i for i, d in enumerate(dni)}
    sA, nA, sB, nB = (np.zeros(len(dni)) for _ in range(4))
    for x in A:
        sA[idx[x["den"]]] += x[pole]; nA[idx[x["den"]]] += 1
    for x in Bg:
        sB[idx[x["den"]]] += x[pole]; nB[idx[x["den"]]] += 1
    tochk = sA.sum() / nA.sum() - sB.sum() / nB.sum()
    rng = np.random.default_rng(seme)
    t = rng.integers(0, len(dni), size=(B, len(dni)))
    cA, cB = nA[t].sum(1), nB[t].sum(1)
    ok = (cA > 0) & (cB > 0)
    r = sA[t].sum(1)[ok] / cA[ok] - sB[t].sum(1)[ok] / cB[ok]
    if r.size == 0:
        return None
    return float(tochk), float(np.quantile(r, 0.025)), float(np.quantile(r, 0.975)), \
        float((np.sum(r >= 0) + 1) / (r.size + 1)), int(r.size)


def permutacii_p(A, Bg, pole="zakon", R=R_PERM, seme=SEME):
    """Едностранното p, че A е по-лошо от B: етикетите се разбъркват ВЪТРЕ в деня (денят пази своя пазар).
    Точен тест при нулата «състоянието не мени резултата в същия ден»; бутстрапът по 8–10 дни е
    твърде смел (мерено 22.10: 11,5 % фалшиво «ВКЛЮЧИ» при номинални 5 % — PLAN_SYANKA.md §6).
    → (точкова разлика mean(A) − mean(B), p = P(разлика_перм ≤ наблюдаваната))."""
    A = [x for x in A if x.get(pole) is not None]
    Bg = [x for x in Bg if x.get(pole) is not None]
    if not A or not Bg:
        return None
    nA, nB = len(A), len(Bg)
    tochk = float(np.mean([x[pole] for x in A]) - np.mean([x[pole] for x in Bg]))
    rng = np.random.default_rng(seme)
    obshto = sum(x[pole] for x in A) + sum(x[pole] for x in Bg)
    sumA = np.zeros(R)
    for den in sorted({x["den"] for x in A} | {x["den"] for x in Bg}):
        v = np.array([x[pole] for x in A if x["den"] == den] + [x[pole] for x in Bg if x["den"] == den])
        k = sum(1 for x in A if x["den"] == den)
        if k == 0:
            continue
        if k == v.size:
            sumA += v.sum()
            continue
        izb = np.argsort(rng.random((R, v.size)), axis=1)[:, :k]
        sumA += v[izb].sum(axis=1)
    r = sumA / nA - (obshto - sumA) / nB
    return tochk, float((np.sum(r <= tochk + 1e-12) + 1) / (R + 1))


def otsadi(d):
    """Правилото (PLAN_SYANKA.md §6) → речник с числата и решението за всяко състояние."""
    sd = d["sdelki"]
    chisto = [x for x in sd if x["st"] == "ЧИСТО"]
    ostanali = [x for x in sd if x["st"] in SASTOYANIYA]
    grupi = {st: _grupa([x for x in sd if x["st"] == st]) for st in ("ЧИСТО",) + SASTOYANIYA + ("БЕЗ_ДАННИ",)}
    grupi["НЕ_ЧИСТО"] = _grupa(ostanali)
    glavna = {"zakon": butstrap_razlika(ostanali, chisto, "zakon"), "poz": butstrap_razlika(ostanali, chisto, "poz"),
              "perm_zakon": permutacii_p(ostanali, chisto, "zakon"), "perm_poz": permutacii_p(ostanali, chisto, "poz")}
    fon_svezh = [r for r in d["fon"] if r.get("staro") is False]
    dyal_fon = {st: (float(np.mean([r.get("sastoyanie") == st for r in fon_svezh])) if fon_svezh else None)
                for st in ("ЧИСТО",) + SASTOYANIYA}
    po_st = {}
    for st in SASTOYANIYA:
        g = grupi[st]
        S = [x for x in sd if x["st"] == st]
        bz = butstrap_razlika(S, chisto, "zakon")          # само за отчета (интервалът)
        bp = butstrap_razlika(S, chisto, "poz")
        pz = permutacii_p(S, chisto, "zakon")              # решението
        po_st[st] = {"a": g["n"] >= MIN_N and g["dni"] >= MIN_DNI, "zakon": bz, "poz": bp, "perm": pz,
                     "p": pz[1] if pz else 1.0, "fon": dyal_fon.get(st)}
    # Холм: едностранните p по ред; праг α/(3 − i)
    red = sorted(SASTOYANIYA, key=lambda st: po_st[st]["p"])
    spri = False
    for i, st in enumerate(red):
        prag = ALFA / (len(SASTOYANIYA) - i)
        b_ok = (not spri) and po_st[st]["p"] <= prag and po_st[st]["perm"] is not None and po_st[st]["perm"][0] < 0
        if not b_ok:
            spri = True
        po_st[st]["b"] = b_ok
        po_st[st]["holm_prag"] = prag
    for st in SASTOYANIYA:
        x = po_st[st]
        x["v"] = bool(x["poz"] is not None and x["poz"][0] < 0)
        x["g"] = x["fon"] is None or x["fon"] <= MAX_FON
        if x["a"] and x["b"] and x["v"] and x["g"]:
            x["reshenie"] = "ВКЛЮЧИ ГЕЙТА за %s (ВЕРОЯТНОСТ_ГЕЙТ=1, ВЕРОЯТНОСТ_ГЕЙТ_СЪСТОЯНИЯ съдържа %s)" % (st, st)
        elif x["a"] and x["b"] and x["v"]:
            x["reshenie"] = "по-лошо, но заема %.0f%% от времето → решава собственикът" % (100 * x["fon"])
        elif not x["a"]:
            x["reshenie"] = "малко данни (%d сделки, %d дни; нужни %d и %d) → сянката продължава" % (
                grupi[st]["n"], grupi[st]["dni"], MIN_N, MIN_DNI)
        else:
            x["reshenie"] = "без доказана разлика → сянката продължава (след 6 седмици: «без ефект», гейтът 0)"
    vsichki = [x for x in sd if x["s"] is not None and (x["best"] >= 1 or x["zakon"] <= -129.5)]
    kal = None
    if vsichki:
        k = sum(x["best"] >= 1 for x in vsichki)
        n = len(vsichki)
        pm = [_p_tp1_model(x["s"]) for x in vsichki]
        p_bar, p_ziva = float(np.mean([p[0] for p in pm])), float(np.mean([p[1] for p in pm]))
        z_bar = (k - n * p_bar) / math.sqrt(n * p_bar * (1 - p_bar))
        kal = {"n": n, "tp1_parvo": k / n, "model_bar": p_bar, "model_ziva": p_ziva, "z_sreshtu_bar": z_bar}
    karti = {st: sum(1 for r in d["karti"] if r.get("sastoyanie") == st) for st in ("ЧИСТО",) + SASTOYANIYA}
    karti["bi_spryal"] = sum(1 for r in d["karti"] if r.get("bi_spryal"))
    return {"grupi": grupi, "glavna": glavna, "po_st": po_st, "dyal_fon": dyal_fon, "n_fon": len(fon_svezh),
            "kalibraciya": kal, "karti": karti, "bez_sianka": d["bez_sianka"], "otvoreni": d["otvoreni"],
            "losh": d["losh"]}


def _f(x, f="%+.1f"):
    return "—" if x is None else (f % x)


def otchet(o):
    print("AERO ВЕРОЯТНОСТ · сянката · сравнението (правилото е от 22.10, преди данните)\n")
    print("  %-10s %5s %4s %9s %9s %6s %6s %9s %9s %8s" % ("състояние", "сд.", "дни", "закон", "позиция", "ТП1",
                                                          "стоп", "база бар", "база жив", "ръб бар"))
    for st, g in o["grupi"].items():
        if not g["n"]:
            print("  %-10s %5d" % (st, 0))
            continue
        print("  %-10s %5d %4d %9s %9s %5.0f%% %5.0f%% %9s %9s %8s" % (
            st, g["n"], g["dni"], _f(g["zakon"]), _f(g["poz"]), 100 * g["tp1"], 100 * g["stop"],
            _f(g["baza_bar"]), _f(g["baza_ziva"]), _f(g["rab_bar"])))
    gz, gp = o["glavna"]["zakon"], o["glavna"]["poz"]
    if gz:
        print("\n  НЕ_ЧИСТО − ЧИСТО по закона: %+.1f пипса [%+.1f; %+.1f] (бутстрап по ден, %d тегления) · "
              "p (разбъркване в деня) = %.4f" % (gz[0], gz[1], gz[2], gz[4], o["glavna"]["perm_zakon"][1]))
    if gp:
        print("  НЕ_ЧИСТО − ЧИСТО на позицията: %+.1f пипса [%+.1f; %+.1f] · p (разбъркване в деня) = %.4f"
              % (gp[0], gp[1], gp[2], o["glavna"]["perm_poz"][1]))
    print("\n  пазарното време (редове «fon», свежи: %d): %s" % (
        o["n_fon"], " · ".join("%s %s" % (k, "—" if v is None else "%.0f%%" % (100 * v))
                               for k, v in o["dyal_fon"].items())))
    print("  картите без вход: %s · гейтът би спрял %d" % (
        " · ".join("%s %d" % (k, v) for k, v in o["karti"].items() if k != "bi_spryal"), o["karti"]["bi_spryal"]))
    k = o["kalibraciya"]
    if k:
        print("  ТП1 преди стопа (решените %d): %.1f%% · моделът без наклон %.1f%% (бар) / %.1f%% (жива) · z = %+.2f"
              % (k["n"], 100 * k["tp1_parvo"], 100 * k["model_bar"], 100 * k["model_ziva"], k["z_sreshtu_bar"]))
    print("  без ред в сянката: %d затворени · още отворени: %d · нечетими редове: %d"
          % (o["bez_sianka"], o["otvoreni"], o["losh"]))
    print("\n  РЕШЕНИЕТО (а ≥%d сд./%d дни · б Холм α=%.2f · в позицията същия знак · г ≤%.0f%% от времето):"
          % (MIN_N, MIN_DNI, ALFA, 100 * MAX_FON))
    for st, x in o["po_st"].items():
        print("   %-7s а=%s б=%s (p=%.3f, праг %.4f) в=%s г=%s → %s" % (
            st, "да" if x["a"] else "не", "да" if x["b"] else "не", x["p"], x["holm_prag"],
            "да" if x["v"] else "не", "да" if x["g"] else "не", x["reshenie"]))


# ══════════════════════════════════════════════════════════════════════
# Пробата на самото сравнение
# ══════════════════════════════════════════════════════════════════════
def _sint(papka, q_po_st, n_po_st, dni=8, seme=1, fon_po_st=None):
    """Пише синтетични live/ файлове: сделки по закона с P(ТП1) = q за всяко състояние.
    При ТП1: +130 с 0,3846 · +100 с 0,1154 · +50 с 0,5 (T = ∞ от SPEC §4); иначе −130."""
    rng = np.random.default_rng(seme)
    sianka = []
    zatv = [{"start": "2026-10-23T00:00", "v": "proba"}]
    i = 0
    for st, n in n_po_st.items():
        for _ in range(n):
            den = 23 + (i % dni)                         # 23.10 … 23 + dni − 1 (dni ≤ 9 → в октомври)
            m = 420 + 7 * (i // dni)                     # (ден, минута) е различно за всяко i
            i += 1
            opened = "2026-10-%02dT%02d:%02d" % (den, m // 60, m % 60)
            d = "long" if rng.random() < 0.5 else "short"
            e = 4130.0 + rng.normal(0, 20)
            if rng.random() < q_po_st[st]:
                u = rng.random()
                zak, best, poz = (130.0, 3, 130.0) if u < 0.3846 else ((100.0, 2, 0.0) if u < 0.5 else (50.0, 1, 0.0))
            else:
                zak, best, poz = -130.0, 0, -130.0
            zn = 1 if d == "long" else -1
            sianka.append({"v": 1, "ev": "vhod", "utc": opened, "dir": d, "opened": opened, "entry": round(e, 2),
                           "sastoyanie": st, "s": 5.04, "staro": False})
            zatv.append({"utc": opened, "kind": "x", "direction": d, "entry": round(e, 2),
                         "exit": round(e + zn * poz * PIP, 2), "opened": opened, "mode": "tp123", "best": best,
                         "pips": zak})
    # сделка без ред в сянката (преди нея) и ред без затворена сделка (още отворена)
    zatv.append({"utc": "2026-10-22T10:00", "direction": "long", "entry": 4100.0, "exit": 4113.0,
                 "opened": "2026-10-22T09:00", "mode": "tp123", "best": 3, "pips": 130.0})
    sianka.append({"v": 1, "ev": "vhod", "utc": "2026-11-05T10:00", "dir": "long", "opened": "2026-11-05T10:00",
                   "entry": 4140.0, "sastoyanie": "ЧИСТО", "s": 5.04, "staro": False})
    for st, k in (fon_po_st or {"ЧИСТО": 60, "МЪРТВО": 30, "ВЗРИВ": 5, "СКЪПО": 5}).items():
        sianka += [{"v": 1, "ev": "fon", "utc": "2026-10-24T10:00", "sastoyanie": st, "staro": False}] * k
    sianka.append({"v": 1, "ev": "fon", "utc": "2026-10-24T11:00", "sastoyanie": "МЪРТВО", "staro": True})
    with open(os.path.join(papka, "veroyatnost_sianka.jsonl"), "w", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in sianka))
        fh.write("{счупен ред\n")
    with open(os.path.join(papka, "closed_trades.jsonl"), "w", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in zatv))


def proba():
    zle = []

    def ck(ime, usl, pod=""):
        print(("  ✓ " if usl else "  ✗ ") + ime + (" " + pod if (pod and not usl) else ""))
        if not usl:
            zle.append(ime)

    print("ПРОБАТА НА СРАВНЕНИЕТО (синтетични файлове с известен отговор)\n")
    with tempfile.TemporaryDirectory() as p:
        _sint(p, {"ЧИСТО": 0.70, "МЪРТВО": 0.30, "ВЗРИВ": 0.70, "СКЪПО": 0.70},
              {"ЧИСТО": 40, "МЪРТВО": 30, "ВЗРИВ": 6, "СКЪПО": 25})
        d = sabiraj(p)
        o = otsadi(d)
        otchet(o)
        print()
        ck("съединяването: 101 сделки, 1 без сянка, 1 отворена, 1 нечетим ред",
           len(d["sdelki"]) == 101 and d["bez_sianka"] == 1 and d["otvoreni"] == 1 and d["losh"] == 1,
           "%d %d %d %d" % (len(d["sdelki"]), d["bez_sianka"], d["otvoreni"], d["losh"]))
        ck("позицията от изхода: +130 → +130, +50 → 0, −130 → −130",
           sorted({x["poz"] for x in d["sdelki"]}) == [-130.0, 0.0, 130.0])
        ck("МЪРТВО (P(ТП1) 0,30 срещу 0,70) → ВКЛЮЧИ", o["po_st"]["МЪРТВО"]["reshenie"].startswith("ВКЛЮЧИ"),
           o["po_st"]["МЪРТВО"]["reshenie"])
        ck("ВЗРИВ (6 сделки) → малко данни", o["po_st"]["ВЗРИВ"]["reshenie"].startswith("малко"))
        ck("СКЪПО (същото P като ЧИСТО) → не се включва", not o["po_st"]["СКЪПО"]["reshenie"].startswith("ВКЛЮЧИ"))
        ck("времето: «fon» брои само свежите (МЪРТВО 30 от 100)", abs(o["dyal_fon"]["МЪРТВО"] - 0.30) < 1e-12)
        ck("базата при s = 5,04: бар +23,36 · жива +21,24",
           abs(o["grupi"]["ЧИСТО"]["baza_bar"] - 23.357) < 0.01 and abs(o["grupi"]["ЧИСТО"]["baza_ziva"] - 21.24) < 0.01,
           "%r %r" % (o["grupi"]["ЧИСТО"]["baza_bar"], o["grupi"]["ЧИСТО"]["baza_ziva"]))
    with tempfile.TemporaryDirectory() as p:
        _sint(p, {"ЧИСТО": 0.70, "МЪРТВО": 0.70, "ВЗРИВ": 0.70, "СКЪПО": 0.70},
              {"ЧИСТО": 40, "МЪРТВО": 40, "ВЗРИВ": 30, "СКЪПО": 30}, seme=2)
        o = otsadi(sabiraj(p))
        ck("нулевият свят (едно P навсякъде) → нито един гейт",
           not any(x["reshenie"].startswith("ВКЛЮЧИ") for x in o["po_st"].values()),
           str({k: v["reshenie"][:20] for k, v in o["po_st"].items()}))
    nuli = 0
    for seme in range(3, 23):                              # колко често правилото лъже при нула
        with tempfile.TemporaryDirectory() as p:
            _sint(p, {"ЧИСТО": 0.70, "МЪРТВО": 0.70, "ВЗРИВ": 0.70, "СКЪПО": 0.70},
                  {"ЧИСТО": 30, "МЪРТВО": 25, "ВЗРИВ": 25, "СКЪПО": 25}, seme=seme)
            o = otsadi(sabiraj(p))
            nuli += any(x["reshenie"].startswith("ВКЛЮЧИ") for x in o["po_st"].values())
    print("  нулевият свят, 20 тегления: фалшиво «ВКЛЮЧИ» в %d" % nuli)
    ck("фалшиво «ВКЛЮЧИ» при нула ≤ 2 от 20", nuli <= 2, str(nuli))
    with tempfile.TemporaryDirectory() as p:
        o = otsadi(sabiraj(p))
        ck("празна папка → без гърмене, малко данни", all(x["reshenie"].startswith("малко")
                                                          for x in o["po_st"].values()))
    print("\nИТОГ НА ПРОБАТА: %s" % ("всичко минава" if not zle else "НЕ минават: %s" % zle))
    return 0 if not zle else 1


def main():
    ap = argparse.ArgumentParser(description="сравнението на сянката AERO ВЕРОЯТНОСТ")
    ap.add_argument("--live", help="папката live/ на бота")
    ap.add_argument("--ot", help="от дата (вкл.), ГГГГ-ММ-ДД, по opened (UTC)")
    ap.add_argument("--do", help="до дата (вкл.)")
    ap.add_argument("--json", help="пиши числата и тук")
    ap.add_argument("--proba", action="store_true", help="пробата на самото сравнение")
    a = ap.parse_args()
    if a.proba:
        return proba()
    if not a.live:
        ap.error("дай --live <папка> или --proba")
    o = otsadi(sabiraj(a.live, a.ot, a.do))
    otchet(o)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(o, fh, ensure_ascii=False, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
