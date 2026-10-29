"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np
import pandas as pd

import funzioni as f


def uguale(a, b, tol=1e-9, nome=""):
    assert abs(a - b) < tol, f"{nome}: {a} != {b}"
    print(f"ok  {nome}")


rng = np.random.default_rng(1)
# 1. Sharpe di una finestra contro il calcolo diretto
r = rng.normal(0.0004, 0.01, 3000)
dir_ = np.mean(r[100:600]) / np.std(r[100:600], ddof=1) * np.sqrt(252)
uguale(f.sharpe_finestre(r, np.array([100]), 500, 252)[0], dir_, tol=1e-9, nome="Sharpe di una finestra")
# 2. finestre multiple
sh = f.sharpe_finestre(r, np.array([0, 10, 20]), 200, 252)
uguale(sh[1], np.mean(r[10:210]) / np.std(r[10:210], ddof=1) * np.sqrt(252), nome="seconda finestra")
# 3. simulazione: media dello Sharpe campionario vicina a quello vero, deviazione standard vicina a quella teorica
s = f.sharpe_simulato(10, 0.5, 252, 200000, rng)
assert abs(s.mean() - 0.5) < 0.02, s.mean()
teo = np.sqrt((1 + 0.5 ** 2 / 2) / 10)
assert abs(s.std() - teo) < 0.02, (s.std(), teo)
print("ok  simulazione: media e dispersione dello Sharpe")
# 4. simulazione con Sharpe vero zero: metà negativi
z = f.sharpe_simulato(5, 0.0, 252, 100000, rng)
assert abs((z < 0).mean() - 0.5) < 0.01
print("ok  simmetria con Sharpe vero zero")
# 5. inizi di mese
idx = pd.bdate_range("2020-01-01", periods=70)
p = f.inizi_mese(idx)
assert idx[p[1]].month == 2 and idx[p[1]].day == 3
print("ok  inizi di mese")
print("Tutti i controlli superati.")
