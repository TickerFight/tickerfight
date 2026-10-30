"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def ok(nome, cond):
    assert cond, nome
    print(f"ok  {nome}")


c = np.concatenate([np.full(30, 100.0), [95.0, 89.0, 88.0, 100.0], np.full(30, 100.0), [85.0], np.full(5, 85.0)])
ev = f.eventi_calo(c, 20, 0.10, 20)
ok("il primo evento è la chiusura a 89 (11% sotto il massimo)", ev[0] == 31 and c[ev[0]] == 89.0)
ok("la pausa evita il secondo giorno consecutivo", 32 not in ev)
ok("un secondo evento dopo la pausa", len(ev) == 2 and c[ev[1]] == 85.0)
ok("rendimento avanti", abs(f.rend_avanti(np.array([100.0, 110, 121]), 2)[0] - 0.21) < 1e-12 and np.isnan(f.rend_avanti(np.array([100.0, 110, 121]), 2)[1]))
m = f.minimo_avanti(np.array([100.0, 90, 95, 80, 100, 100]), 3)
ok("minimo nei tre giorni successivi", abs(m[0] - (-0.20)) < 1e-12 and abs(m[1] - (80 / 90 - 1)) < 1e-12 and np.isnan(m[3]))
rng = np.random.default_rng(0)
v = rng.normal(0, 1, 2000)
ok("p-value vicino a mezzo per un'osservazione tipica", 0.2 < f.pval_casuali(v, 0.0, 20, 500, rng) < 0.8)
ok("p-value piccolo per un valore enorme", f.pval_casuali(v, 3.0, 20, 500, rng) < 0.01)
