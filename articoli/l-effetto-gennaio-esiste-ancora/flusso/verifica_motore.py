"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np
import pandas as pd

import funzioni as f


def ok(nome, cond):
    assert cond, nome
    print(f"ok  {nome}")


idx = pd.bdate_range("2020-01-01", "2021-12-31")
c = pd.Series(np.arange(1.0, len(idx) + 1), index=idx)
r = f.rendimenti_mensili(c)
ok("il primo mese incompleto è perso", r.index[0] == pd.Period("2020-02"))
m = c.groupby(c.index.to_period("M")).last()
ok("rendimento da fine mese a fine mese", abs(r.iloc[0] - (m.iloc[1] / m.iloc[0] - 1)) < 1e-12)
rng = np.random.default_rng(0)
x = rng.normal(0, 1, 600)
e = np.zeros(600, bool)
e[:50] = True
x[e] += 3.0
d, p = f.permutazione_differenza(x, e, 500, rng)
ok("differenza grande: p-value piccolo", d > 2.5 and p < 0.01)
x2 = rng.normal(0, 1, 600)
d2, p2 = f.permutazione_differenza(x2, e, 500, rng)
ok("nessuna differenza: p-value non piccolo", p2 > 0.05)
idx2 = pd.period_range("2020-01", "2020-12", freq="M")
rm = pd.Series([0.10] + [0.01] * 11, index=idx2)
d3 = f.resto_anno(rm)
ok("resto dell'anno: undici mesi composti", len(d3) == 1 and abs(d3["resto"].iloc[0] - (1.01 ** 11 - 1)) < 1e-12 and d3["gennaio"].iloc[0] == 0.10)
