"""Controlli del motore su dati inventati. Se uno fallisce, il flusso si ferma."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

spec = importlib.util.spec_from_file_location("bt", Path(__file__).resolve().parent / "02_backtest_e_test.py")
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)
ERR = []


def ok(nome, cond):
    print("ok     " if cond else "FALLITO", nome)
    if not cond:
        ERR.append(nome)


r = np.full(120, 0.01)
ok("cagr: 1% al mese = (1,01^12)-1", abs(bt.cagr(r) - (1.01 ** 12 - 1)) < 1e-12)
ok("cagr: serie vuota = nan", np.isnan(bt.cagr(np.array([]))))
rg, rp = np.full(24, 0.01), np.full(24, 0.02)
ld = bt.finestre(rg, rp, 12)
ok("finestre: numero di finestre = n - w + 1", len(ld) == 13)
ok("finestre: differenza costante positiva", np.allclose(ld, 12 * (np.log(1.02) - np.log(1.01))))
ld2 = bt.finestre(rp, rg, 12)
ok("finestre: segno invertito se si scambiano le serie", np.allclose(ld2, -ld))
idx = pd.date_range("2000-01-31", periods=30, freq="ME")
s = pd.DataFrame({"Close": np.arange(1, 31, dtype=float)}, index=idx)
tmp = Path(__file__).resolve().parent / "_prova.csv"
s.to_csv(tmp)
m = bt.fine_mese(tmp)
tmp.unlink()
ok("fine_mese: esclude l'ultimo mese", len(m) == 29 and m.iloc[-1] == 29.0)
if ERR:
    raise SystemExit(f"{len(ERR)} controlli falliti")
print("Tutti i controlli superati.")
