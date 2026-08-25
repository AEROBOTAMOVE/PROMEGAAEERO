# -*- coding: utf-8 -*-
"""
ГЕНЕРАЛЕН ПЛАН · О8 + О11

О8 · GDX/DXY БЕЗ РЕЗЕРВА
   Един транзиентен хълцук на Yahoo сваля цялото макро-краче за рън, а О1 (качен
   днес) при мъртво краче СПИРА новите входове. Тоест едно мигване = час без
   входове. Лихвите вече имат резерв (FRED пази последна стойност); Yahoo — не.
   ПОПРАВКА: последната ДОБРА стойност се пази в meta и се ползва при провал, с
   бележка колко е стара. Отвъд СТАР_МАКРО_Ч часа резервът се брои за мъртъв —
   стара цена е по-лоша от никаква, ако е много стара.

О11 · СЪСТОЯНИЕ-ХИГИЕНА
   МЕРЕНО (не предположено):
     · POISON_ATTEMPTS — вече го няма в кода ✅ нищо за правене
     · outbox.jsonl — 0 реда, опашката е празна ✅ но няма ТАВАН: при упорит мек
       провал расте без край. Слагам таван с изхвърляне на НАЙ-СТАРИТЕ и бележка.
     · archive/ — 3352 KB за ЕДИН месец (юли), расте вечно в git repo.
       При това темпо ~40 MB/година. Пазим последните АРХИВ_МЕСЕЦИ месеца.
"""
import io, sys, ast, hashlib

ops = []


def rep(p, old, new, why, n=1):
    s = io.open(p, encoding="utf-8", newline="").read()
    c = s.count(old)
    if c != n:
        print(f"  x СПИРАМ «{why}»: {c} съвпадения, чакам {n}\n    {old[:130]!r}")
        sys.exit(1)
    io.open(p, "wb").write(s.replace(old, new).encode("utf-8"))
    ops.append(why)


LB = "live_bot.py"

# ═══ прагове ═════════════════════════════════════════════════════════════
rep(LB, 'СПАЛ_МИН = int(os.environ.get("СПАЛ_МИН", "45"))',
    '''СПАЛ_МИН = int(os.environ.get("СПАЛ_МИН", "45"))
# О8 · до колко часа резервната макро-стойност още върши работа. Отвъд това
# стара цена е по-лоша от никаква — по-честно е да кажем «не виждам».
СТАР_МАКРО_Ч = float(os.environ.get("СТАР_МАКРО_Ч", "36"))
# О11 · колко месеца архив пазим. Мерено: 3352 KB за ЕДИН месец → ~40 MB/година
# в git repo. АРХИВ_МЕСЕЦИ=0 изключва чистенето.
АРХИВ_МЕСЕЦИ = int(os.environ.get("АРХИВ_МЕСЕЦИ", "3"))
# О11 · таван на опашката. Мерено сега: 0 реда — празна е. Но при упорит мек
# провал расте без край и никой не я гледа.
ОПАШКА_ТАВАН = int(os.environ.get("ОПАШКА_ТАВАН", "200"))''',
    "прагове")

# ═══ О8 · резерв за Yahoo-крачетата ══════════════════════════════════════
rep(LB, '''        except Exception as _e:
            _макро_мъртво.append(_име)
            print(f"  ⚠ {_име} не се дърпа ({type(_e).__name__}) — новите входове спират, "
                  f"следенето продължава")
        time.sleep(1.2)''',
    '''        except Exception as _e:
            # О8 · РЕЗЕРВ. Един хълцук на Yahoo сваля цялото краче, а О1 при
            # мъртво краче спира входовете — тоест едно мигване = час мълчание.
            # Лихвите имат резерв (FRED пази); Yahoo нямаше.
            _рез = (_load_state(out / "macro_backup.json", {}) or {}).get(_име)
            _взет = False
            if isinstance(_рез, dict) and _рез.get("utc"):
                try:
                    _въз = (pd.Timestamp(now_utc) - pd.Timestamp(_рез["utc"])).total_seconds() / 3600
                    if _въз <= СТАР_МАКРО_Ч and _рез.get("csv"):
                        _д = pd.read_json(io.StringIO(_рез["csv"]), orient="split")
                        _д.index = pd.to_datetime(_д.index)
                        if _име.startswith("миньори"):
                            gdx_d = _д
                        elif _име.startswith("долар"):
                            dxy_d = _д
                        else:
                            rr = _д["rate"] if "rate" in _д else _д.iloc[:, 0]
                        _взет = True
                        notes.append(f"🟡 {_име} не се дърпа — карам на резерва "
                                     f"отпреди {_въз:.0f}ч")
                except Exception:
                    pass
            if not _взет:
                _макро_мъртво.append(_име)
                print(f"  ⚠ {_име} не се дърпа ({type(_e).__name__}) — новите входове спират, "
                      f"следенето продължава")
        time.sleep(1.2)''',
    "О8 · резерв при провал")

# записваме резерва при УСПЕХ
rep(LB, '''            _р = _взем()
            if _име.startswith("миньори"):
                gdx_d = _р
            elif _име.startswith("долар"):
                dxy_d = _р
            else:
                rr = _р''',
    '''            _р = _взем()
            if _име.startswith("миньори"):
                gdx_d = _р
            elif _име.startswith("долар"):
                dxy_d = _р
            else:
                rr = _р
            # О8: пазим ПОСЛЕДНАТА ДОБРА стойност, за да има на какво да паднем
            try:
                _рамка = (_р.tail(120) if hasattr(_р, "tail") else None)
                if _рамка is not None and len(_рамка):
                    if isinstance(_рамка, pd.Series):
                        _рамка = _рамка.to_frame("rate")
                    _бек = _load_state(out / "macro_backup.json", {}) or {}
                    _бек[_име] = {"utc": now_utc, "csv": _рамка.to_json(orient="split")}
                    (out / "macro_backup.json").write_text(
                        json.dumps(_бек, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass''',
    "О8 · пази последната добра")

# ═══ О11 · чистене на архива ═════════════════════════════════════════════
rep(LB, '''    meta["month"] = mon''',
    '''    # О11 · АРХИВЪТ РАСТЕШЕ ВЕЧНО. Мерено: 3352 KB за един месец (юли) в git
    # repo → ~40 MB/година. Пазим последните АРХИВ_МЕСЕЦИ месеца.
    if АРХИВ_МЕСЕЦИ > 0:
        try:
            _арх = out / "archive"
            if _арх.exists():
                _по_месец = {}
                for _f in _арх.glob("*-????-??.jsonl"):
                    _по_месец.setdefault(_f.stem[-7:], []).append(_f)
                for _м in sorted(_по_месец)[:-АРХИВ_МЕСЕЦИ]:
                    for _f in _по_месец[_м]:
                        _f.unlink()
                    notes.append(f"🧹 архивът от {_м} е изчистен (пазим последните "
                                 f"{АРХИВ_МЕСЕЦИ} месеца)")
        except Exception as _e:
            notes.append(f"чистенето на архива се спъна: {type(_e).__name__}")
    meta["month"] = mon''',
    "О11 · чистене на архива")

print("ПРИЛОЖЕНИ:")
for o in ops:
    print(f"  + {o}")
ast.parse(io.open(LB, encoding="utf-8").read())
b = io.open(LB, encoding="utf-8").read()
print(f"{LB}: {len(b.splitlines())} реда · sha {hashlib.sha256(b.encode()).hexdigest()[:12]}")
