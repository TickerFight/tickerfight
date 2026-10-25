"""Controlli delle funzioni su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import funzioni as fx

n_ok = 0


def controlla(nome, cond):
    global n_ok
    print(("OK   " if cond else "FAIL ") + nome)
    if not cond:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


inv = np.array([0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0], dtype=bool)
controlla("episodi: un solo mese isolato è scartato", fx.episodi(inv, 3, 2) == [(1, 3), (6, 9)])
controlla("episodi: unione quando il gap è sotto soglia", fx.episodi(inv, 3, 3) == [(1, 9)])
r = np.full(12, 0.01)
controlla("CAGR di +1% al mese", abs(fx.cagr(r) - (1.01 ** 12 - 1)) < 1e-12)
controlla("drawdown di una serie sempre in salita è zero", fx.max_drawdown(r) == 0.0)
controlla("drawdown: -50% poi risalita", abs(fx.max_drawdown(np.array([0.1, -0.5, 0.2])) - (-0.5)) < 1e-12)
fuori = np.array([False, True, False])
s = fx.rendimenti_strategia(np.array([0.1, -0.2, 0.05]), np.array([0.0, 0.0, 0.0]), fuori)
controlla("strategia: in liquidità il mese segnalato", np.allclose(s, [0.1, 0.0, 0.05]))
idx = pd.date_range("2000-01-01", periods=70, freq="D")
d = pd.DataFrame({"a": np.arange(70.0)}, index=idx)
m = fx.mensile(d)
controlla("mensile: ultimo giorno del mese", float(m["a"].iloc[0]) == 30.0)
controlla("indice_mesi", fx.indice_mesi("2000-04", pd.Timestamp("2000-01-31")) == 3)
print(f"{n_ok} controlli superati")
