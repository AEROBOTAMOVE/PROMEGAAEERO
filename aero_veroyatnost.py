# -*- coding: utf-8 -*-
"""
AERO ВЕРОЯТНОСТ · близнакът за бота (сянка) · v1.0 (22.10.2026)
====================================================================
Самостоятелен модул за live_bot.py: само stdlib + numpy (pandas НЕ се внася —
DataFrame се чете по колони). Договорът: ЛОЦО/AERO_ВЕРОЯТНОСТ/SPEC.md и
test_vectors.json (53 вектора, |разлика| ≤ 1e-6). Еталонът е
aero_veroyatnost_ref.py; тук всичко е написано НАНОВО (векторно, math.erfc,
затворен брой членове), за да има два независими кода, които се сверяват
(test_twin.py: векторите + случайна сверка с еталона до 1e-9).

Принципът (мерено 22 г.): посоката НЕ се гадае — наклонът е 0 по закон.
Смята се КОЛКО и КОГА: σ от свещите, вероятностите до време T, очакването
по закона и на позицията, и присъдата ВЗРИВ / СКЪПО / МЪРТВО / ЧИСТО.
Присъдата НЕ е посока: при нулев наклон покупката и продажбата са огледални,
значи състоянието е едно за двете посоки.

Главното:
    veroyatnost(df1m, spread_pips, plan=None, now_utc=None) → речник (JSON-безопасен)
        df1m        1-минутни свещи GC=F или PAXG-USD, каквито ботът ги има (`m1`):
                    DataFrame с Open/High/Low/Close (главни или малки букви, и MultiIndex
                    на yfinance), или масив (n, 4). Индексът — наивно UTC (както `_yf`).
        spread_pips целият спред ask − bid в пипса (Swissquote elite ≈ 5,04).
        plan        законът и праговете; липсващото идва от ПЛАН (ТП 50/100/130, СЛ 130).
        now_utc     «сега» (низ ISO, datetime или pd.Timestamp, UTC) — за незавършената
                    свещ и възрастта на данните. Без него — нито едното.
    red_za_dnevnik(rez)          → плосък ред за live/veroyatnost_sianka.jsonl
    prisada_po_profili(rez, pr)  → присъдата за всеки профил на Swissquote ({име: [bid, ask]})

veroyatnost() НИКОГА не гърми (освен при strogo=True): липсват ли данни или спред —
sastoyanie «БЕЗ_ДАННИ» и причината; изключение — полето greshka.

Единици: пипс = 0,10 $; σ в пипса на √минута (средната цена); T в минути; ∞ = без таван.
"""
from __future__ import annotations

import math
import time
from datetime import datetime, timezone

import numpy as np

VERSIYA = "1.0"
BLIZNAK = "bot-1.0"
PIP = 0.10
INF = math.inf

_SQRT_PI = math.sqrt(math.pi)
_LN_EPS = math.log(1e19)        # член на Фурие под 1e-19 → край на реда
_Z_ERFC = 7.0                   # образ с d/q > 7 → erfc < 4,2e-23, изпуска се
_GRANICA_BEZKRAI = 1e-16        # P(веригата не е свършила до T) под това → T = ∞
_TAU_PREVKL = 0.5               # τ = σ²T/L²: под — образи, над — Фурие (двата са точни)
_KL = 1e-14                     # шум при изваждане на вероятности → 0

ZAKON = {"tp1": 50.0, "tp2": 100.0, "tp3": 130.0, "sl": 130.0, "be_at": None}
SASTOYANIYA = ("ВЗРИВ", "СКЪПО", "МЪРТВО", "ЧИСТО")
BEZ_DANNI = "БЕЗ_ДАННИ"

# Планът по подразбиране = законът на бота (06.10 + «ок +50» от 07.10) и праговете от SPEC §3.6
PLAN = {
    "tp1": 50.0, "tp2": 100.0, "tp3": 130.0, "sl": 130.0, "be_at": None,
    "T_mrtvo": 60.0, "T_vzriv": 5.0,
    "prag_mrtvo": 0.25, "prag_skapo": 0.12, "prag_shok": 3.0, "prag_vzriv": 0.05,
    "rab_mid": None,                       # измереният ръб по средна цена; None → net = −s
    "horizonti": (5.0, 15.0, 60.0, 240.0),  # P(ТП1)/P(стоп) до тези минути
    "T_stalba": (60.0, 240.0),              # стълбата и до тези минути (∞ винаги)
    "polu_zhivot": 30.0, "metod": "gk",     # σ: EWMA с полуживот в свещи; gk | parkinson
    "okno": 600,                            # последните N свещи (0,5^20 тегло на по-старите)
    "minuti": 1.0,                          # минути в свещ
    "max_vazrast_min": 30.0,                # последната свещ по-стара → staro = True
    "spred_rezerva": None,                  # спредът липсва → това (s_izvor «rezerva»); None → БЕЗ_ДАННИ
    "pip": PIP,
}


# ══════════════════════════════════════════════════════════════════════
# erfc
# ══════════════════════════════════════════════════════════════════════
def erfc_prenosim(x: float) -> float:
    """erfc(x) с алгоритъма, който се пренася 1:1 в Pine (SPEC §9):
    x < 3 — ред с положителни членове за erf; x ≥ 3 — верижна дроб с дълбочина 64."""
    x = float(x)
    if x != x:
        return float("nan")
    if x < 0.0:
        return 2.0 - erfc_prenosim(-x)
    if x >= 3.0:
        if x > 27.0:
            return 0.0
        f = x
        for k in range(64, 0, -1):
            f = x + 0.5 * k / f
        return math.exp(-x * x) / (_SQRT_PI * f)
    x2 = x * x
    chlen = suma = x
    for n in range(1, 201):
        chlen *= 2.0 * x2 / (2 * n + 1)
        suma += chlen
        if chlen <= 1e-17 * suma:
            break
    return 1.0 - 2.0 / _SQRT_PI * math.exp(-x2) * suma


def _erfc_v(x):
    """math.erfc върху масив (единственият път за erfc в сумите — една точка за мутационната проба)."""
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return np.zeros(x.shape)
    return np.fromiter((math.erfc(v) for v in x.ravel()), dtype=float, count=x.size).reshape(x.shape)


# ══════════════════════════════════════════════════════════════════════
# Един етап: средната цена между две поглъщащи бариери (+a горе, −b долу)
# ══════════════════════════════════════════════════════════════════════
def _proveri(a: float, b: float) -> None:
    if not (a > 0.0 and b > 0.0) or math.isinf(a) or math.isinf(b):
        raise ValueError("разстоянията до бариерите трябва да са > 0 (горе %r, долу %r)" % (a, b))


def _dve_bariery(a: float, b: float, sigma: float, T: float, metod: str | None = None):
    """(P(горе първа до T), P(долу първа до T), P(нищо до T)) — SPEC §3.2.

    Образи:  P_горе = Σ_k [erfc((a+2kL)/q) − erfc((a+2b+2kL)/q)],  q = σ√(2T), L = a+b
    Фурие:   P_горе = b/L − Σ_n 2(−1)^{n+1}/(nπ)·sin(nπb/L)·e^{−n²λ},  λ = π²σ²T/(2L²)
             P_нищо = Σ_{n нечетно} 4/(nπ)·sin(nπb/L)·e^{−n²λ}
    Броят на членовете се знае предварително (образи до d/q ≤ 7; Фурие до e^{−n²λ} ≥ 1e-19)."""
    _proveri(a, b)
    L = a + b
    if sigma <= 0.0 or T <= 0.0:
        return 0.0, 0.0, 1.0
    if math.isinf(T):
        return b / L, a / L, 0.0
    tau = sigma * sigma * T / (L * L)
    if metod is None:
        metod = "obrazi" if tau < _TAU_PREVKL else "furie"
    if metod == "obrazi":
        q = sigma * math.sqrt(2.0 * T)
        kmax = int(math.ceil(max(0.0, _Z_ERFC * q - min(a, b)) / (2.0 * L))) + 1
        k2L = 2.0 * L * np.arange(kmax + 1, dtype=float)
        gore = math.fsum(_erfc_v((a + k2L) / q)) - math.fsum(_erfc_v((a + 2.0 * b + k2L) / q))
        dolu = math.fsum(_erfc_v((b + k2L) / q)) - math.fsum(_erfc_v((b + 2.0 * a + k2L) / q))
        return gore, dolu, max(0.0, 1.0 - gore - dolu)
    if metod != "furie":
        raise ValueError("метод: obrazi | furie")
    lam = math.pi * math.pi * tau / 2.0
    nmax = int(math.floor(math.sqrt(_LN_EPS / lam)))
    if nmax < 1:
        return b / L, a / L, 0.0
    n = np.arange(1, nmax + 1, dtype=float)
    e = np.exp(-n * n * lam)
    nech = (np.arange(1, nmax + 1) % 2) == 1
    c = 2.0 / (n * math.pi) * e * np.where(nech, 1.0, -1.0)
    sb = np.sin(n * math.pi * b / L)
    sa = np.sin(n * math.pi * a / L)
    gore = b / L - math.fsum(c * sb)
    dolu = a / L - math.fsum(c * sa)
    nishto = math.fsum(4.0 / (n[nech] * math.pi) * sb[nech] * e[nech])
    return gore, dolu, nishto


# ══════════════════════════════════════════════════════════════════════
# Една сделка: цел +X, стоп −Y, спред s (SPEC §2–3.3)
# ══════════════════════════════════════════════════════════════════════
def _bariery(X: float, Y: float, s: float):
    """Покупка на ask = m0 + s/2; целта по bid ⇒ бариера +(X+s); стопът по bid ⇒ −(Y−s)."""
    X = float(X); Y = float(Y); s = float(s)
    if not (X > 0.0 and Y > 0.0):
        raise ValueError("X и Y трябва да са > 0")
    if not (0.0 <= s < Y):
        raise ValueError("спредът трябва да е 0 ≤ s < Y (s=%r, Y=%r)" % (s, Y))
    return X + s, Y - s


def p_first(X: float, Y: float, s: float = 0.0) -> float:
    """P(целта преди стопа), без таван: средната цена е мартингал ⇒ p = (Y − s)/(X + Y)."""
    a, b = _bariery(X, Y, s)
    return b / (a + b)


def p_first_within(X, Y, s, sigma, T, metod=None) -> float:
    a, b = _bariery(X, Y, s)
    return _dve_bariery(a, b, float(sigma), float(T), metod)[0]


def p_stop_within(X, Y, s, sigma, T, metod=None) -> float:
    a, b = _bariery(X, Y, s)
    return _dve_bariery(a, b, float(sigma), float(T), metod)[1]


def p_none_within(X, Y, s, sigma, T, metod=None) -> float:
    a, b = _bariery(X, Y, s)
    return _dve_bariery(a, b, float(sigma), float(T), metod)[2]


def exp_time(X, Y, s, sigma) -> float:
    """E[τ] = (X + s)(Y − s)/σ²  (m² − σ²t е мартингал)."""
    a, b = _bariery(X, Y, s)
    sigma = float(sigma)
    return INF if sigma <= 0.0 else a * b / (sigma * sigma)


def exp_time_cond(X, Y, s, sigma):
    """(E[τ | целта първа], E[τ | стопът пръв]) = ((L² − b²)/(3σ²), (L² − a²)/(3σ²))."""
    a, b = _bariery(X, Y, s)
    sigma = float(sigma)
    if sigma <= 0.0:
        return INF, INF
    L2, k = (a + b) ** 2, 3.0 * sigma * sigma
    return (L2 - b * b) / k, (L2 - a * a) / k


# ══════════════════════════════════════════════════════════════════════
# Верига от етапи: P = Σ_образи (Π знаци) · erfc((d₁+…+d_n)/q)  (SPEC §3.4)
# ══════════════════════════════════════════════════════════════════════
def _obrazi(a: float, b: float, posoka: str, Dmax: float):
    """Образите на изхода на етап: горе (a+2kL, +), (a+2b+2kL, −); долу (b+2kL, +), (b+2a+2kL, −)."""
    L = a + b
    if posoka == "gore":
        c1, c2 = a, a + 2.0 * b
    elif posoka == "dolu":
        c1, c2 = b, b + 2.0 * a
    else:
        raise ValueError("посока: gore | dolu")
    if c1 > Dmax:
        return np.zeros(0), np.zeros(0)
    k2L = 2.0 * L * np.arange(int(math.floor((Dmax - c1) / (2.0 * L))) + 1, dtype=float)
    d1 = c1 + k2L
    d2 = c2 + k2L
    d2 = d2[d2 <= Dmax]
    return np.concatenate([d1, d2]), np.concatenate([np.ones(d1.size), -np.ones(d2.size)])


def _veriga(etapi, sigma: float, T: float) -> float:
    """P(изходите на етапите са точно тези, по ред, и всичко е станало до T).
    etapi = [(a, b, "gore"|"dolu"), ...]; T = ∞ → произведението на b/L (горе) или a/L (долу)."""
    if not etapi:
        return 1.0
    p_bezkrai = 1.0
    for a, b, pos in etapi:
        _proveri(a, b)
        p_bezkrai *= (b if pos == "gore" else a) / (a + b)
    if sigma <= 0.0 or T <= 0.0:
        return 0.0
    if math.isinf(T):
        return p_bezkrai
    if len(etapi) == 1:
        a, b, pos = etapi[0]
        g, d, _ = _dve_bariery(a, b, sigma, T)
        return g if pos == "gore" else d
    n = len(etapi)
    granica = 0.0
    for a, b, _ in etapi:
        granica += 1.3 * math.exp(-(math.pi ** 2 * sigma * sigma / (2.0 * (a + b) ** 2)) * T / n)
    if granica < _GRANICA_BEZKRAI:
        return p_bezkrai
    q = sigma * math.sqrt(2.0 * T)
    Dmax = 7.0 * q
    D = np.zeros(1)
    Z = np.ones(1)
    for a, b, pos in etapi:
        d, z = _obrazi(a, b, pos, Dmax)
        D = (D[:, None] + d[None, :]).ravel()
        Z = (Z[:, None] * z[None, :]).ravel()
        ost = D <= Dmax
        D, Z = D[ost], Z[ost]
        if D.size == 0:
            return 0.0
    return math.fsum(Z * _erfc_v(D / q))


def _kl(x: float) -> float:
    return 0.0 if abs(x) < _KL else x


# ══════════════════════════════════════════════════════════════════════
# Стълбата ТП1 · ТП2 · ТП3 · СЛ по закона на бота (SPEC §3.4)
# ══════════════════════════════════════════════════════════════════════
def ladder(tp1=50.0, tp2=100.0, tp3=130.0, sl=130.0, s=5.0, sigma=10.0, T=INF, be_at=None) -> dict:
    """Разпределението на резултата на една сделка: по закона (най-високата стигната цел)
    и на позицията (изход − вход за една позиция). Етапите (за средната цена):
      E0  от входа:   горе (tp1 | be_at) + s, долу sl − s
      E0б от +be_at:  горе tp1 − be_at, долу be_at (само при be_at < tp1, старото «+40 → вход»)
      E1  от ТП1:     горе tp2 − tp1, долу tp1      E2 от ТП2: горе tp3 − tp2, долу tp2"""
    tp1, tp2, tp3, sl = float(tp1), float(tp2), float(tp3), float(sl)
    s, sigma, T = float(s), float(sigma), float(T)
    if not (0.0 < tp1 < tp2 < tp3):
        raise ValueError("нужно е 0 < tp1 < tp2 < tp3")
    if not (0.0 <= s < sl):
        raise ValueError("нужно е 0 ≤ s < sl")
    rano = be_at is not None and 0.0 < float(be_at) < tp1
    be = float(be_at) if rano else None

    E0 = (be + s, sl - s) if rano else (tp1 + s, sl - s)
    E0b = (tp1 - be, be) if rano else None
    E1 = (tp2 - tp1, tp1)
    E2 = (tp3 - tp2, tp2)
    m_tp1, m_tp2, m_tp3, m_vhod, m_stop = tp1 + s, tp2 + s, tp3 + s, s, s - sl  # нива на средата спрямо m0

    def V(*put):
        return _veriga([(e[0], e[1], p) for e, p in put], sigma, T)

    do_tp1 = [(E0, "gore"), (E0b, "gore")] if rano else [(E0, "gore")]
    p_e0g = V((E0, "gore"))
    p_stop = V((E0, "dolu"))
    p_vhod0 = V((E0, "gore"), (E0b, "dolu")) if rano else 0.0
    p_tp1 = V(*do_tp1)
    p_tp1_vhod = V(*do_tp1, (E1, "dolu"))
    p_tp2 = V(*do_tp1, (E1, "gore"))
    p_tp2_vhod = V(*do_tp1, (E1, "gore"), (E2, "dolu"))
    p_tp3 = V(*do_tp1, (E1, "gore"), (E2, "gore"))

    # недовършеното в етапа и средният ход на средата в него (спиране по избор):
    #   E[m_T; U] = старт·P(влязъл) − горе·P(горе) − долу·P(долу)
    u_e0 = _kl(1.0 - p_e0g - p_stop)
    em_e0 = -E0[0] * p_e0g - m_stop * p_stop
    if rano:
        u_e0b = _kl(p_e0g - p_tp1 - p_vhod0)
        em_e0b = (be + s) * p_e0g - m_tp1 * p_tp1 - m_vhod * p_vhod0
    else:
        u_e0b, em_e0b = 0.0, 0.0
    u_e1 = _kl(p_tp1 - p_tp2 - p_tp1_vhod)
    em_e1 = m_tp1 * p_tp1 - m_tp2 * p_tp2 - m_vhod * p_tp1_vhod
    u_e2 = _kl(p_tp2 - p_tp3 - p_tp2_vhod)
    em_e2 = m_tp2 * p_tp2 - m_tp3 * p_tp3 - m_vhod * p_tp2_vhod

    def sred(em, u):
        return (em / u - s) if u > 1e-15 else None

    izhodi = [
        {"kod": "cel3", "p": p_tp3, "zakon": tp3, "poziciya": tp3},
        {"kod": "cel2_vhod", "p": p_tp2_vhod, "zakon": tp2, "poziciya": 0.0},
        {"kod": "cel2_vreme", "p": u_e2, "zakon": tp2, "poziciya": sred(em_e2, u_e2)},
        {"kod": "cel1_vhod", "p": p_tp1_vhod, "zakon": tp1, "poziciya": 0.0},
        {"kod": "cel1_vreme", "p": u_e1, "zakon": tp1, "poziciya": sred(em_e1, u_e1)},
        {"kod": "vhod", "p": p_vhod0, "zakon": 0.0, "poziciya": 0.0},
        {"kod": "vreme_bez_risk", "p": u_e0b, "zakon": sred(em_e0b, u_e0b), "poziciya": sred(em_e0b, u_e0b)},
        {"kod": "vreme_predi_cel", "p": u_e0, "zakon": sred(em_e0, u_e0), "poziciya": sred(em_e0, u_e0)},
        {"kod": "stop", "p": p_stop, "zakon": -sl, "poziciya": -sl},
    ]
    pz = {"cel3": tp3 * p_tp3, "cel2_vhod": tp2 * p_tp2_vhod, "cel2_vreme": tp2 * u_e2,
          "cel1_vhod": tp1 * p_tp1_vhod, "cel1_vreme": tp1 * u_e1, "vhod": 0.0,
          "vreme_bez_risk": em_e0b - s * u_e0b, "vreme_predi_cel": em_e0 - s * u_e0, "stop": -sl * p_stop}
    pp = dict(pz, cel2_vhod=0.0, cel2_vreme=em_e2 - s * u_e2, cel1_vhod=0.0, cel1_vreme=em_e1 - s * u_e1)
    E_zakon = math.fsum(pz.values())
    E_poz = math.fsum(pp.values())

    usp = ("cel3", "cel2_vhod", "cel2_vreme", "cel1_vhod", "cel1_vreme", "vhod", "vreme_bez_risk")
    if p_e0g > 1e-15:
        c_zakon = math.fsum(pz[k] for k in usp) / p_e0g
        c_poz = math.fsum(pp[k] for k in usp) / p_e0g
        nuzhna_zakon, nuzhna_poz = sl / (sl + c_zakon), sl / (sl + c_poz)
    else:
        c_zakon = c_poz = nuzhna_zakon = nuzhna_poz = None
    den = p_e0g + p_stop
    uspevaemost = p_e0g / den if den > 1e-15 else None

    # времената без таван (минути): E[τ] = ab/σ², E[τ|горе] = (L²−b²)/(3σ²), E[τ|долу] = (L²−a²)/(3σ²)
    def et(e):
        return e[0] * e[1] / (sigma * sigma) if sigma > 0 else INF

    def et_g(e):
        return ((e[0] + e[1]) ** 2 - e[1] ** 2) / (3.0 * sigma * sigma) if sigma > 0 else INF

    def et_d(e):
        return ((e[0] + e[1]) ** 2 - e[0] ** 2) / (3.0 * sigma * sigma) if sigma > 0 else INF

    def q(e):
        return e[1] / (e[0] + e[1])

    opashka = et(E1) + q(E1) * et(E2)
    if rano:
        zhivot = et(E0) + q(E0) * (et(E0b) + q(E0b) * opashka)
        do_tp1_t = et_g(E0) + et_g(E0b)
    else:
        zhivot = et(E0) + q(E0) * opashka
        do_tp1_t = et_g(E0)

    return {
        "vhod": {"tp1": tp1, "tp2": tp2, "tp3": tp3, "sl": sl, "s": s, "sigma": sigma, "T": T, "be_at": be},
        "bariery_e0": {"gore": E0[0], "dolu": E0[1]},
        "p": {"tp1": p_tp1, "tp2": p_tp2, "tp3": p_tp3, "stop": p_stop, "bez_risk": p_e0g, "nishto_e0": u_e0},
        "izhodi": izhodi,
        "po_zakona": {"+%g" % tp3: p_tp3, "+%g" % tp2: p_tp2_vhod + u_e2, "+%g" % tp1: p_tp1_vhod + u_e1,
                      "0": p_vhod0, "drugo": u_e0 + u_e0b, "-%g" % sl: p_stop},
        "E_zakon": E_zakon,
        "E_poziciya": E_poz,
        "martingal_proverka": E_poz + s,
        "uspevaemost": uspevaemost,
        "nuzhna_zakon": nuzhna_zakon,
        "nuzhna_poziciya": nuzhna_poz,
        "c_zakon": c_zakon,
        "c_poziciya": c_poz,
        "vremena_bez_tavan": {"zhivot": zhivot, "do_tp1_ako_dojde": do_tp1_t, "do_stop_ako_dojde": et_d(E0),
                              "e0_izhod": et(E0)},
    }


# ══════════════════════════════════════════════════════════════════════
# σ от свещите (SPEC §3.5)
# ══════════════════════════════════════════════════════════════════════
_K_GK = 2.0 * math.log(2.0) - 1.0
_K_PARK = 1.0 / (4.0 * math.log(2.0))


def sigma_per_min(ohlc, minuti: float = 1.0, polu_zhivot: float = 30.0, metod: str = "gk",
                  pip: float = PIP) -> dict:
    """σ в пипса/√мин (EWMA) + шок + ход_z от свещи [open, high, low, close] в цена.
    По свещ (пипса²): gk ½(H−L)² − (2ln2−1)(C−O)²; parkinson (H−L)²/(4 ln2); делено на минутите.
    EWMA λ = ½^{1/полуживот}, засята със средната на първите ⌈полуживот⌉ валидни свещи.
    Прескачат се: NaN, ≤ 0, H < L, H = L (пазарът стои). H/L се разширяват до O/C. Гапът не влиза."""
    a = np.asarray(ohlc, dtype=float)
    if a.ndim != 2 or a.shape[1] != 4:
        raise ValueError("ohlc трябва да е (n, 4): open, high, low, close")
    if not (minuti > 0 and polu_zhivot > 0):
        raise ValueError("minuti и polu_zhivot > 0")
    o, h, l, c = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    with np.errstate(invalid="ignore"):
        dobar = np.isfinite(a).all(axis=1) & (a > 0).all(axis=1) & (h >= l)
        hi = np.maximum(np.maximum(h, o), c)
        lo = np.minimum(np.minimum(l, o), c)
        rng = (hi - lo) / pip
        hod = (c - o) / pip
        dobar &= rng > 0
    idx = np.flatnonzero(dobar)
    n_pr = int(a.shape[0] - idx.size)
    if idx.size == 0:
        return {"sigma": None, "sigma_predi": None, "shok": None, "hod_z": None,
                "n_polzvani": 0, "n_propusnati": n_pr, "posledna": None}
    if metod == "gk":
        v = 0.5 * rng[idx] ** 2 - _K_GK * hod[idx] ** 2
    elif metod == "parkinson":
        v = _K_PARK * rng[idx] ** 2
    else:
        raise ValueError("метод: gk | parkinson")
    v = v / float(minuti)
    lam = 0.5 ** (1.0 / float(polu_zhivot))
    k0 = min(int(math.ceil(polu_zhivot)), v.size)
    s2 = float(np.mean(v[:k0]))
    s2_predi = None
    for x in v[k0:].tolist():
        s2_predi = s2
        s2 = lam * s2 + (1.0 - lam) * x
    if s2_predi is None:                  # всичко е в засяването
        s2_predi = float(np.mean(v[:-1])) if v.size > 1 else None
    sig_p = math.sqrt(s2_predi) if s2_predi else None
    posl = int(idx[-1])
    return {"sigma": math.sqrt(s2), "sigma_predi": sig_p,
            "shok": math.sqrt(float(v[-1]) / s2_predi) if s2_predi else None,
            "hod_z": abs(float(hod[posl])) / (sig_p * math.sqrt(minuti)) if sig_p else None,
            "n_polzvani": int(idx.size), "n_propusnati": n_pr, "posledna": posl}


# ══════════════════════════════════════════════════════════════════════
# Присъдата (SPEC §3.6) — НЕ посока
# ══════════════════════════════════════════════════════════════════════
def verdict(s, sigma, X=50.0, Y=130.0, T=60.0, shok=None, prag_mrtvo=0.25, prag_skapo=0.12,
            prag_shok=3.0, T_vzriv=5.0, prag_vzriv=0.05, rab_mid=None) -> dict:
    """ВЗРИВ (шок ≥ prag_shok или P(стоп до T_vzriv) ≥ prag_vzriv) → СКЪПО (s/X > prag_skapo) →
    МЪРТВО (P(ТП1 преди стопа до T) < prag_mrtvo) → ЧИСТО. Главното е първото задействано.
    Без наклон позицията губи точно s на сделка ⇒ нужният ръб е s; net = rab_mid − s (без него −s)."""
    s, sigma = float(s), float(sigma)
    p_tp1_T = p_first_within(X, Y, s, sigma, T)
    p_stop_vz = p_stop_within(X, Y, s, sigma, T_vzriv)
    dyal = s / float(X)
    vsichki, prichini = [], []
    shok_da = shok is not None and shok >= prag_shok
    if shok_da or p_stop_vz >= prag_vzriv:
        vsichki.append("ВЗРИВ")
        if shok_da:
            prichini.append("шок %.2f ≥ %.2f" % (shok, prag_shok))
        if p_stop_vz >= prag_vzriv:
            prichini.append("стопът до %g мин: %.4f ≥ %.4f" % (T_vzriv, p_stop_vz, prag_vzriv))
    if dyal > prag_skapo:
        vsichki.append("СКЪПО")
        prichini.append("спредът е %.1f%% от ТП1 > %.1f%%" % (100 * dyal, 100 * prag_skapo))
    if p_tp1_T < prag_mrtvo:
        vsichki.append("МЪРТВО")
        prichini.append("ТП1 до %g мин: %.4f < %.4f" % (T, p_tp1_T, prag_mrtvo))
    if not vsichki:
        vsichki.append("ЧИСТО")
    net = (float(rab_mid) - s) if rab_mid is not None else -s
    return {
        "sastoyanie": next(st for st in SASTOYANIYA if st in vsichki),
        "vsichki": vsichki,
        "prichini": prichini,
        "p_tp1_do_T": p_tp1_T,
        "p_stop_do_T_vzriv": p_stop_vz,
        "p_tp1_bez_tavan": p_first(X, Y, s),
        "spred_dyal": dyal,
        "vreme_do_izhod": exp_time(X, Y, s, sigma),
        "E_poziciya_bez_naklon": -s,
        "nuzhen_rab": s,
        "net": net,
        "matematika": "за" if net > 0 else "срещу",
    }


# ══════════════════════════════════════════════════════════════════════
# Обвивката за бота
# ══════════════════════════════════════════════════════════════════════
_KOLONI = ("open", "high", "low", "close")


def _svechi(df):
    """(ohlc (n, 4), времена datetime64[s] или None, източник) от DataFrame/масив/списък."""
    if df is None:
        raise ValueError("няма свещи (None)")
    if hasattr(df, "columns"):
        po_ime = {}
        for kol in list(df.columns):
            ime = kol[0] if isinstance(kol, tuple) else kol
            ime = str(ime).strip().lower()
            if ime in _KOLONI and ime not in po_ime:
                po_ime[ime] = kol
        lipsa = [k for k in _KOLONI if k not in po_ime]
        if lipsa:
            raise ValueError("липсват колони: %s" % ", ".join(lipsa))
        ohlc = np.column_stack([np.asarray(df[po_ime[k]], dtype=float).reshape(-1) for k in _KOLONI])
        vreme = None
        idx = getattr(df, "index", None)
        # само истински индекс от времена (RangeIndex от числа НЕ се превръща в 1970-а)
        if (idx is not None and len(idx) == ohlc.shape[0] and len(idx)
                and str(getattr(idx, "dtype", "")).startswith("datetime64")):
            try:
                if getattr(idx, "tz", None) is not None:
                    idx = idx.tz_convert("UTC").tz_localize(None)
                vreme = np.asarray(idx, dtype="datetime64[s]")
            except Exception:
                vreme = None
        return ohlc, vreme, "DataFrame"
    a = np.asarray(df, dtype=float)
    if a.ndim != 2 or a.shape[1] != 4:
        raise ValueError("масивът трябва да е (n, 4): open, high, low, close")
    return a, None, "masiv"


def _kam_dt64(t):
    """«сега» → numpy datetime64[s] в UTC (низ ISO, datetime, pd.Timestamp) или None."""
    if t is None:
        return None
    if isinstance(t, datetime):
        if t.tzinfo is not None:
            t = t.astimezone(timezone.utc).replace(tzinfo=None)
        return np.datetime64(t.replace(microsecond=0), "s")
    s = str(t).strip().replace(" ", "T")
    if s.endswith("Z"):
        s = s[:-1]
    if len(s) > 19 and s[19] in "+-":
        dt = datetime.fromisoformat(s)
        return _kam_dt64(dt)
    return np.datetime64(s[:19], "s")


def _chislo(x):
    """float или None (None, NaN, inf, нечетимо)."""
    if x is None or isinstance(x, bool):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _json(x):
    """JSON-безопасно: ∞ → "inf"/"-inf", NaN → None, numpy → Python, кортежи → списъци."""
    if isinstance(x, dict):
        return {str(k): _json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json(v) for v in x]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        x = float(x)
        if math.isnan(x):
            return None
        if math.isinf(x):
            return "inf" if x > 0 else "-inf"
        return x
    return x


def _kl_T(T):
    """Ключ за хоризонт: 60.0 → "60", 7.5 → "7.5", ∞ → "inf"."""
    T = float(T)
    if math.isinf(T):
        return "inf"
    return str(int(T)) if T == int(T) else ("%g" % T)


def _stalba_kratko(L):
    return {k: L[k] for k in ("p", "po_zakona", "E_zakon", "E_poziciya", "martingal_proverka", "uspevaemost",
                              "nuzhna_zakon", "nuzhna_poziciya", "c_zakon", "c_poziciya",
                              "vremena_bez_tavan")} | {
        "izhodi": {i["kod"]: {"p": i["p"], "zakon": i["zakon"], "poziciya": i["poziciya"]} for i in L["izhodi"]}}


def veroyatnost(df1m, spread_pips, plan=None, now_utc=None, strogo: bool = False) -> dict:
    """Всички числа и присъдата за плана на бота при тези свещи и този спред.

    Връща речник (JSON-безопасен): sastoyanie (ВЗРИВ/СКЪПО/МЪРТВО/ЧИСТО/БЕЗ_ДАННИ), vsichki, prichini,
    s, s_izvor, sigma{…}, do_T{T: {tp1, stop, nishto}}, p_tp1_bez_tavan, vreme{…},
    stalba{"inf"|T: …} (s — истинското изпълнение), stalba_bot{"inf": …} (s/2 — броенето на бота
    по средна цена, SPEC §2), prisada{…}, matematika, net, greshka, ms, plan."""
    t0 = time.perf_counter()
    P = dict(PLAN)
    if plan:
        P.update({k: v for k, v in dict(plan).items() if v is not None or k in ("be_at", "rab_mid",
                                                                                 "spred_rezerva")})
    rez = {"versiya": VERSIYA, "bliznak": BLIZNAK, "sastoyanie": BEZ_DANNI, "vsichki": [BEZ_DANNI],
           "prichini": [], "s": None, "s_izvor": None, "sigma": None, "do_T": None,
           "p_tp1_bez_tavan": None, "vreme": None, "stalba": None, "stalba_bot": None, "prisada": None,
           "matematika": None, "net": None, "greshka": None,
           "plan": {k: P[k] for k in ("tp1", "tp2", "tp3", "sl", "be_at", "T_mrtvo", "T_vzriv", "prag_mrtvo",
                                      "prag_skapo", "prag_shok", "prag_vzriv", "rab_mid", "polu_zhivot",
                                      "metod", "okno")}}
    try:
        tp1, tp2, tp3, sl = (float(P[k]) for k in ("tp1", "tp2", "tp3", "sl"))
        if not (0.0 < tp1 < tp2 < tp3) or not sl > 0.0:
            raise ValueError("планът иска 0 < tp1 < tp2 < tp3 и sl > 0")
        be_at = P.get("be_at")
        minuti = float(P["minuti"])

        # ── свещите ──
        ohlc, vreme, forma = _svechi(df1m)
        sega = _kam_dt64(now_utc)
        izh = {"forma": forma, "n_svechi": int(ohlc.shape[0]), "nezavarshena_mahnata": False,
               "posledna_t": None, "vazrast_min": None, "staro": None}
        if vreme is not None and sega is not None and ohlc.shape[0]:
            krai = vreme[-1] + np.timedelta64(int(round(minuti * 60)), "s")
            if krai > sega:                         # свещта още тече → не е цяла
                ohlc, vreme = ohlc[:-1], vreme[:-1]
                izh["nezavarshena_mahnata"] = True
        okno = int(P["okno"]) if P.get("okno") else ohlc.shape[0]
        if okno > 0 and ohlc.shape[0] > okno:
            ohlc = ohlc[-okno:]
            vreme = vreme[-okno:] if vreme is not None else None
        sg = sigma_per_min(ohlc, minuti=minuti, polu_zhivot=float(P["polu_zhivot"]),
                           metod=str(P["metod"]), pip=float(P["pip"]))
        if sg["posledna"] is not None and vreme is not None:
            t_posl = vreme[sg["posledna"]]
            izh["posledna_t"] = str(t_posl)[:16]
            if sega is not None:
                vz = (sega - (t_posl + np.timedelta64(int(round(minuti * 60)), "s"))) / np.timedelta64(1, "s")
                izh["vazrast_min"] = float(vz) / 60.0
                izh["staro"] = bool(izh["vazrast_min"] > float(P["max_vazrast_min"]))
        izh.update({k: sg[k] for k in ("sigma", "sigma_predi", "shok", "hod_z", "n_polzvani", "n_propusnati")})
        izh["n_v_prozoreca"] = int(ohlc.shape[0])
        rez["sigma"] = izh

        # ── спредът ──
        s = _chislo(spread_pips)
        rez["s_izvor"] = "vhod"
        if s is None or s < 0.0:
            s = _chislo(P.get("spred_rezerva"))
            rez["s_izvor"] = "rezerva" if s is not None else None
        if s is not None:
            s = round(s, 6)                         # (ask − bid)/0,1 = 6,000000000002 не бива да е «> 12 %»
        if s is None:
            rez["prichini"].append("спредът липсва (spread_pips=%r)" % (spread_pips,))
        elif not (0.0 <= s < sl):
            rez["prichini"].append("спредът %.3f пипса е извън [0, СЛ)" % s)
            s = None
        rez["s"] = s
        sigma = sg["sigma"]
        if sigma is None or not sigma > 0.0:
            rez["prichini"].append("няма валидни свещи за σ (%d подадени, %d прескочени)"
                                   % (izh["n_v_prozoreca"], sg["n_propusnati"]))
        if s is None or sigma is None or not sigma > 0.0:
            rez["ms"] = (time.perf_counter() - t0) * 1000.0
            return _json(rez)

        # ── колко и кога ──
        a, b = _bariery(tp1, sl, s)
        rez["do_T"] = {}
        for T in P["horizonti"] or ():
            g, d, n = _dve_bariery(a, b, sigma, float(T))
            rez["do_T"][_kl_T(T)] = {"tp1": g, "stop": d, "nishto": n}
        rez["p_tp1_bez_tavan"] = p_first(tp1, sl, s)
        g_t, d_t = exp_time_cond(tp1, sl, s, sigma)
        rez["vreme"] = {"do_izhod": exp_time(tp1, sl, s, sigma), "ako_tp1": g_t, "ako_stop": d_t}

        # ── стълбата: ∞ (затворени формули) и до T; броенето на бота — с s/2 ──
        rez["stalba"] = {}
        for T in (INF,) + tuple(P["T_stalba"] or ()):
            rez["stalba"][_kl_T(T)] = _stalba_kratko(
                ladder(tp1, tp2, tp3, sl, s=s, sigma=sigma, T=float(T), be_at=be_at))
        rez["stalba_bot"] = {"inf": _stalba_kratko(ladder(tp1, tp2, tp3, sl, s=s / 2.0, sigma=sigma, T=INF,
                                                          be_at=be_at))}

        # ── присъдата ──
        pr = verdict(s, sigma, X=tp1, Y=sl, T=float(P["T_mrtvo"]), shok=sg["shok"],
                     prag_mrtvo=float(P["prag_mrtvo"]), prag_skapo=float(P["prag_skapo"]),
                     prag_shok=float(P["prag_shok"]), T_vzriv=float(P["T_vzriv"]),
                     prag_vzriv=float(P["prag_vzriv"]), rab_mid=P.get("rab_mid"))
        rez["prisada"] = pr
        rez["sastoyanie"] = pr["sastoyanie"]
        rez["vsichki"] = list(pr["vsichki"])
        rez["prichini"] = list(pr["prichini"])
        rez["matematika"] = pr["matematika"]
        rez["net"] = pr["net"]
    except Exception as e:                       # сянката не бива да гърми
        if strogo:
            raise
        rez["greshka"] = "%s: %s" % (type(e).__name__, str(e)[:200])
        rez["sastoyanie"], rez["vsichki"] = BEZ_DANNI, [BEZ_DANNI]
    rez["ms"] = (time.perf_counter() - t0) * 1000.0
    return _json(rez)


def prisada_po_profili(rez: dict, profili) -> dict | None:
    """Присъдата за всеки профил на Swissquote — {име: [bid, ask]} (форматът на `_цена_профили`
    в live_bot.py) → {име: {"s": пипса, "sastoyanie": …}}. σ и шокът са от `rez`; само присъдата
    се смята наново (евтино). Без σ или без профили → None. Профилът на сметката не се знае
    (elite 5,04 · premium 6,58 · standard 6,90), а СКЪПО зависи точно от него."""
    sg = (rez or {}).get("sigma") or {}
    sigma = _chislo(sg.get("sigma"))
    if not isinstance(profili, dict) or sigma is None or sigma <= 0.0:
        return None
    P = dict(PLAN)
    P.update({k: v for k, v in ((rez or {}).get("plan") or {}).items()})
    pip = float(P.get("pip") or PIP)
    izh = {}
    for ime in sorted(profili, key=str):
        try:
            bid, ask = (float(x) for x in profili[ime])
            s = round((ask - bid) / pip, 6)
            if not (math.isfinite(s) and 0.0 <= s < float(P["sl"])):
                continue
            pr = verdict(s, sigma, X=float(P["tp1"]), Y=float(P["sl"]), T=float(P["T_mrtvo"]),
                         shok=_chislo(sg.get("shok")), prag_mrtvo=float(P["prag_mrtvo"]),
                         prag_skapo=float(P["prag_skapo"]), prag_shok=float(P["prag_shok"]),
                         T_vzriv=float(P["T_vzriv"]), prag_vzriv=float(P["prag_vzriv"]),
                         rab_mid=P.get("rab_mid"))
            izh[str(ime)] = {"s": round(s, 3), "sastoyanie": pr["sastoyanie"]}
        except Exception:
            continue
    return izh or None


def _r(x, n):
    v = _chislo(x)
    return None if v is None else round(v, n)


_KRATKO = ("vv", "sastoyanie", "vsichki", "s", "s_izvor", "sigma", "shok", "n_svechi", "n_propusnati",
           "vazrast_min", "staro", "p_tp1_60", "p_stop_5", "greshka")


def red_za_dnevnik(rez: dict, kratko: bool = False) -> dict:
    """Плоският ред за live/veroyatnost_sianka.jsonl (~0,8 KB; kratko=True → ~0,3 KB, само състоянието,
    σ, шокът, свежестта и двете вероятности на присъдата — за редовете «fon»). Пълният речник остава
    в паметта на рънa. Ботът добавя своите полета (ev, utc, dir, …)."""
    rez = rez or {}
    sg = rez.get("sigma") or {}
    do_T = rez.get("do_T") or {}
    st = rez.get("stalba") or {}
    inf = st.get("inf") or {}
    bot = (rez.get("stalba_bot") or {}).get("inf") or {}
    if not rez.get("sastoyanie"):
        rez = dict(rez, sastoyanie=BEZ_DANNI, vsichki=[BEZ_DANNI])
    red = {
        "vv": rez.get("versiya"),
        "sastoyanie": rez.get("sastoyanie"),
        "vsichki": rez.get("vsichki"),
        "s": _r(rez.get("s"), 3), "s_izvor": rez.get("s_izvor"),
        "sigma": _r(sg.get("sigma"), 4), "sigma_predi": _r(sg.get("sigma_predi"), 4),
        "shok": _r(sg.get("shok"), 3), "hod_z": _r(sg.get("hod_z"), 3),
        "n_svechi": sg.get("n_polzvani"), "n_propusnati": sg.get("n_propusnati"),
        "posledna_t": sg.get("posledna_t"), "vazrast_min": _r(sg.get("vazrast_min"), 1),
        "staro": sg.get("staro"),
    }
    for T, v in do_T.items():
        red["p_tp1_%s" % T] = _r(v.get("tp1"), 6)
        red["p_stop_%s" % T] = _r(v.get("stop"), 6)
    red.update({
        "p_tp1_bez_tavan": _r(rez.get("p_tp1_bez_tavan"), 6),
        "p_tp3": _r((inf.get("p") or {}).get("tp3"), 6),
        "p_stop": _r((inf.get("p") or {}).get("stop"), 6),
        "E_zakon": _r(inf.get("E_zakon"), 4),
        "E_poziciya": _r(inf.get("E_poziciya"), 4),
        "E_zakon_bot": _r(bot.get("E_zakon"), 4),
    })
    for T, v in st.items():
        if T != "inf":
            red["E_zakon_%s" % T] = _r(v.get("E_zakon"), 4)
    red.update({
        "vreme_do_izhod": _r((rez.get("vreme") or {}).get("do_izhod"), 2),
        "zhivot": _r((inf.get("vremena_bez_tavan") or {}).get("zhivot"), 2),
        "matematika": rez.get("matematika"), "net": _r(rez.get("net"), 4),
        "prichini": rez.get("prichini") or None,
        "greshka": rez.get("greshka"),
        "ms": _r(rez.get("ms"), 1),
    })
    if kratko:
        return {k: red.get(k) for k in _KRATKO}
    return red


__all__ = ["VERSIYA", "BLIZNAK", "PIP", "ZAKON", "PLAN", "SASTOYANIYA", "BEZ_DANNI",
           "erfc_prenosim", "p_first", "p_first_within", "p_stop_within", "p_none_within",
           "exp_time", "exp_time_cond", "ladder", "sigma_per_min", "verdict",
           "veroyatnost", "prisada_po_profili", "red_za_dnevnik"]
