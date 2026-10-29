"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def uguale(a, b, tol=1e-9, nome=""):
    assert abs(a - b) < tol, f"{nome}: {a} != {b}"
    print(f"ok  {nome}")


# 1. rendimento composto: due anni al 10% annuo
uguale(f.cagr_da_log(2 * np.log(1.1), 2.0), 0.10, nome="rendimento composto")
# 2. giorni estremi
r = np.array([0.01, -0.05, 0.03, 0.02, -0.01, 0.03])
assert list(f.indici_estremi(r, 2, True)) == [2, 5], f.indici_estremi(r, 2, True)
assert list(f.indici_estremi(r, 2, False)) == [1, 4]
print("ok  giorni migliori e peggiori (a parità vince la data più antica)")
# 3. saltare il giorno migliore su una finestra: confronto col calcolo diretto
lr = np.log1p(r)
bh, sal = f.perdita_finestre(lr, np.array([0]), 6, 1, 1.0)
uguale(bh[0], np.exp(lr.sum()) - 1, nome="buy & hold della finestra")
uguale(sal[0], np.exp(lr.sum() - np.log1p(0.03)) - 1, nome="saltando il giorno migliore")
# 4. regime: prezzi in salita poi in discesa, media a 3 chiusure
c = np.array([10, 11, 12, 13, 9, 8, 14.0])
s = f.sotto_media(c, 3)
# chiusure: t=0..6; media a 3 da t=2: 11, 12, 11.33, 10, 11.0 (t=6); sotto: t=4 (9<11.33), t=5 (8<10)
assert list(s) == [False, False, False, False, True, True], list(s)
print("ok  regime sotto la media (usa la chiusura precedente)")
# 5. vicinanza
v = f.vicino_a(np.array([5, 101, 50]), np.array([5, 20, 70]), 30)
assert list(v) == [True, False, True]
print("ok  vicinanza")
# 6. inizi di mese
import pandas as pd
idx = pd.bdate_range("2020-01-01", periods=70)
p = f.inizi_mese(idx)
assert idx[p[1]].month == 2 and idx[p[1]].day == 3
print("ok  inizi di mese")
print("Tutti i controlli superati.")
