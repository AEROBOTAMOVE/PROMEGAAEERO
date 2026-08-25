# -*- coding: utf-8 -*-
"""СКЕПТИК·ПОСЛЕДИЦА — стъпка 7: МОЖЕ ЛИ ИЗОБЩО да гръмне вътре в try,
щом всичко е минало през _yf? Батерия от странни, но ЗАКОННИ след _yf рамки."""
import sys, os, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)
import pandas as pd, numpy as np, live_bot as lb

src = open("live_bot.py.преди_4114", encoding="utf-8").read()
i = src.index("def _tf_basis("); j = src.index("\n\n\n", i)
g = {"np": np, "pd": pd, "TF_BASIS_CAP": lb.TF_BASIS_CAP, "TF_BASIS_ALPHA": lb.TF_BASIS_ALPHA}
exec(compile(src[i:j], "OLD", "exec"), g); old = g["_tf_basis"]

idx = pd.date_range("2026-07-01", periods=60*24, freq="h")
intra = pd.DataFrame({"Open":4600.0,"High":4601.0,"Low":4599.0,
                      "Close": np.full(len(idx), 4600.0), "Volume":1}, index=idx)
r = intra.resample("1D").agg(Close=("Close","last")).dropna()
daily = pd.DataFrame({"Open":1.0,"High":1.0,"Low":1.0,
                      "Close": r["Close"].values-48.0, "Volume":1}, index=r.index)

случаи = {
    "нормално": (intra, daily),
    "интрадей с ЕДИН ред": (intra.iloc[:1], daily),
    "дублиран индекс": (pd.concat([intra, intra]).sort_index(), daily),
    "немонотонен индекс": (intra.sample(frac=1.0, random_state=1), daily),
    "дневен с ЕДИН ред": (intra, daily.iloc[:1]),
    "нула застъпване (различни години)": (intra, daily.set_axis(daily.index + pd.Timedelta(days=900))),
    "Close е цял (int)": (intra.assign(Close=intra["Close"].astype("int64")), daily),
    "Close е обект (низове)": (intra.assign(Close=intra["Close"].astype(str)), daily),
    "Close с NaN-ове": (intra.assign(Close=np.where(np.arange(len(intra)) % 3, np.nan, 4600.0)), daily),
    "интрадей е Series, не DataFrame": (intra["Close"], daily),
    "дневен е Series": (intra, daily["Close"]),
    "дневен с MultiIndex колони": (intra, daily.set_axis(pd.MultiIndex.from_product([daily.columns, ["GC=F"]]), axis=1)),
}
for име, (a, b) in случаи.items():
    st = {"tf_basis_g": -3.851}; nt = []
    try:
        v = old(st, "tf_basis_g", a, b, nt)
        # различаваме «сметна» от «върна пазеното»
        как = "СМЕТНА" if st["tf_basis_g"] != -3.851 or v != -3.851 else "върна пазеното (тихо)"
        print(f"{име:36s} -> {v!s:>10s} | {как} | бележки: {nt or '—'}")
    except Exception as e:
        print(f"{име:36s} -> ГРЪМНА извън функцията?! {type(e).__name__}")
