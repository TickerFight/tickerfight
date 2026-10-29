"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np
import pandas as pd

import funzioni as f


def uguale(a, b, tol=1e-9, nome=""):
    assert abs(a - b) < tol, f"{nome}: {a} != {b}"
    print(f"ok  {nome}")


# 1. prezzo sempre in salita: sopra la media, sempre investiti dopo il ritardo; nessun costo dopo il primo ingresso
c = 100.0 * 1.001 ** np.arange(600)
s, b, pos = f.rendimenti_regola(c, 50, 0.001)
assert pos[:2].sum() == 0 and pos[52:].min() == 1.0, "posizione"
uguale(s[60], b[60], nome="stessa cosa del buy & hold quando si è dentro")
# 2. nessun look-ahead: il segnale del giorno k usa solo chiusure fino a k-2
c2 = np.r_[np.full(100, 100.0), 200.0, np.full(100, 200.0)]            # salto alla chiusura 100
s2, b2, pos2 = f.rendimenti_regola(c2, 50, 0.0)
assert pos2[100] == 0.0 and pos2[101] == 0.0 and pos2[102] == 1.0, "il segnale deve essere in ritardo di due sedute"
print("ok  nessun look-ahead")
# 3. costo: ingresso e poi uscita (quando la media raggiunge il prezzo) costano due volte il costo
uguale(sum(f.rendimenti_regola(c2, 50, 0.01)[0] - f.rendimenti_regola(c2, 50, 0.0)[0]), -0.02, nome="costo di ingresso e uscita")
# 4. metriche: serie costante
cg, sh, dd = f.metriche_finestra(np.full(252, 0.001), 252)
uguale(cg, 1.001 ** 252 - 1, nome="cagr")
uguale(dd, 0.0, nome="perdita massima nulla")
cg, sh, dd = f.metriche_finestra(np.array([0.2, -0.5, 0.0]), 252)
uguale(dd, 0.5, nome="perdita massima del 50%")
# 5. inizi di mese
idx = pd.bdate_range("2020-01-01", periods=70)
p = f.inizi_mese(idx, 0)
assert idx[p[0]].day == 1 and idx[p[1]].month == 2 and idx[p[1]].day == 3, "inizi di mese"
print("ok  inizi di mese")
print("Tutti i controlli superati.")
