"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def uguale(a, b, tol=1e-9, nome=""):
    assert abs(a - b) < tol, f"{nome}: {a} != {b}"
    print(f"ok  {nome}")


r = np.array([1.0, 3.0, 2.0, 4.0, 5.0, 7.0])
g = np.array([0, 0, 1, 1, 2, 2])
m = f.medie_per_gruppo(r, g, 3)
assert list(m) == [2.0, 3.0, 6.0], m
print("ok  medie per gruppo")
# permutazione: gruppi identici -> p-value alto; gruppi molto diversi -> p-value basso
rng = np.random.default_rng(1)
x = rng.normal(0, 1, 5000)
gi = np.tile(np.arange(5), 1000)
p, sim = f.p_permutazione(x, gi.copy(), 500, rng)
assert p > 0.05, p
print("ok  permutazione senza differenze: p-value", round(p, 2))
y = x + gi * 0.5
p2, _ = f.p_permutazione(y, gi.copy(), 500, rng)
assert p2 < 0.01, p2
print("ok  permutazione con differenze nette: p-value", round(p2, 3))
# costo di pareggio: 100 giorni con -0,1% ciascuno: il pareggio è a ln(1-c) = ln(0.999)/2
lg = np.full(100, np.log(0.999))
uguale(f.costo_pareggio(lg), 1 - np.exp(np.log(0.999) / 2), nome="costo di pareggio")
uguale(f.costo_pareggio(np.full(10, 0.01)), 0.0, nome="costo di pareggio senza vantaggio")
print("Tutti i controlli superati.")
