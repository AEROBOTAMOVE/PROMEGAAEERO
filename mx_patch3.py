# -*- coding: utf-8 -*-
import io
p="mx_final.py"; s=io.open(p,encoding="utf-8").read(); o=s
a = """    _rr = (\u0437.get("\u0441\u044a\u043e\u0442\u043d\u043e\u0448\u0435\u043d\u0438\u0435") or 0)
    if _rr:
        _\u0446 += f" \u00b7 \u0440\u0438\u0441\u043a\u0443\u0432\u0430\u0448 1, \u0437\u0430 \u0434\u0430 \u0432\u0437\u0435\u043c\u0435\u0448 {_rr:.1f}"
    L.append(_\u0446)"""
b = """    L.append(_\u0446)
    _rr = (\u0437.get("\u0441\u044a\u043e\u0442\u043d\u043e\u0448\u0435\u043d\u0438\u0435") or 0)
    if _rr:
        L.append(f"\u21b3 \u0441\u0440\u0435\u0449\u0443 {lb._\u043f\u0438\u043f\u0441(abs(\u0432\u0445 - \u0441\u0442))} \u0440\u0438\u0441\u043a \u0447\u0430\u043a\u0430\u043c {lb._\u043f\u0438\u043f\u0441(abs(\u04461 - \u0432\u0445))} \u2014 "
                 f"\u0442\u043e\u0435\u0441\u0442 {_rr:.1f} \u043f\u044a\u0442\u0438 \u043f\u043e\u0432\u0435\u0447\u0435, \u043e\u0442\u043a\u043e\u043b\u043a\u043e\u0442\u043e \u0440\u0438\u0441\u043a\u0443\u0432\u0430\u043c")"""
assert a in s, "не намерен"
s = s.replace(a, b, 1)
io.open(p,"w",encoding="utf-8").write(s); print("променен:", s!=o)
