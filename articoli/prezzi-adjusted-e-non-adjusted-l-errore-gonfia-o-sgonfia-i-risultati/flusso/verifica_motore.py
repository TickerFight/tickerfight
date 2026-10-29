"""Controlli del motore su dati inventati: se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import motore_vettoriale as m

idx = pd.bdate_range("2020-01-01", periods=10)
close = pd.Series([100, 101, 102, 103, 104, 52, 52.5, 53, 53.5, 54.0], index=idx)   # split 2 a 1 il sesto giorno
spl = pd.Series(0.0, index=idx)
spl.iloc[5] = 2.0
g = m.ricostruisci_grezzo(close, spl)
assert np.allclose(g.iloc[5:], close.iloc[5:]), "dopo lo split grezzo = corretto"
assert np.allclose(g.iloc[:5], close.iloc[:5] * 2.0), "prima dello split il grezzo è il corretto per 2"
# due split
spl2 = pd.Series(0.0, index=idx); spl2.iloc[3] = 3.0; spl2.iloc[7] = 2.0
g2 = m.ricostruisci_grezzo(pd.Series(10.0, index=idx), spl2)
assert np.allclose(g2.to_numpy(), [60, 60, 60, 20, 20, 20, 20, 10, 10, 10]), g2.to_numpy()
# posizione: il ritardo uno sposta il segnale
s = pd.Series([False, True, True, False], index=idx[:4])
assert list(m.posizione(s, 1)) == [False, False, True, True]
assert list(m.posizione(s, 0)) == [False, True, True, False]
try:
    m.posizione(s, -1)
    raise AssertionError("ritardo negativo accettato")
except ValueError:
    pass
# valore e cagr
v = m.valore(pd.Series([0.1, 0.1]), pd.Series([True, False]))
assert abs(v.iloc[-1] - 1.1) < 1e-12
assert abs(m.cagr(pd.Series([2.0]), 2.0) - (2 ** 0.5 - 1)) < 1e-12
print("Tutti i controlli del motore sono passati")
