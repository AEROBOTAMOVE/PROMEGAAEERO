import importlib.util, pathlib, sys
import pandas as pd
HERE=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location("lbx", HERE/"lb_nov.py")
lb=importlib.util.module_from_spec(spec); sys.modules["lbx"]=lb
sys.argv=["x"]; spec.loader.exec_module(lb)
now="2026-08-21T12:00"
for печат in ["2026-08-20T12:00","2026-08-14T20:56","2026-08-05T12:00",
              "2026-08-07T11:00","2026-08-07T13:00","2026-07-20T12:00","2026-05-01T12:00"]:
    стенно=(pd.Timestamp(now)-pd.Timestamp(печат)).total_seconds()/3600
    търг=lb._търговски_минути(печат, now)/60.0
    print(f"печат {печат} · стенно {стенно:8.1f}ч · търговско {търг:7.1f}ч · "
          f"минава ли прага {lb.СТАР_МАКРО_Ч}? {'ДА' if търг<=lb.СТАР_МАКРО_Ч else 'не'}")
