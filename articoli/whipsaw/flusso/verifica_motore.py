"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def uguale(a, b, tol=1e-9, nome=""):
    assert abs(a - b) < tol, f"{nome}: {a} != {b}"
    print(f"ok  {nome}")


# 1. media mobile
m = f.media_mobile(np.array([1, 2, 3, 4, 5.0]), 3)
assert np.isnan(m[1]) and m[2] == 2 and m[4] == 4
print("ok  media mobile")
# 2. posizione semplice, cambi, episodi
close = np.array([10, 12, 9, 8, 13, 14, 7, 15.0])
sma = np.full(8, 10.0)
p = f.posizione_semplice(close, sma)
assert list(p) == [1, 1, 0, 0, 1, 1, 0, 1], list(p)
assert list(f.cambi(p)) == [2, 4, 6, 7]
u, r = f.episodi(p)
assert list(u) == [2, 6] and list(r) == [4, 7], (u, r)
print("ok  posizione, cambi ed episodi")
# 3. episodio ancora aperto alla fine escluso; inizio fuori mercato ignorato
p2 = np.array([0, 0, 1, 1, 0, 0])
u2, r2 = f.episodi(p2)
assert len(u2) == 0 and len(r2) == 0, (u2, r2)
p3 = np.array([0, 1, 1, 0, 1])
u3, r3 = f.episodi(p3)
assert list(u3) == [3] and list(r3) == [4], (u3, r3)
print("ok  episodi aperti e iniziali")
# 4. banda: due chiusure appena sotto la media non fanno uscire
close = np.array([100, 99, 101, 97, 103.0])
sma = np.full(5, 100.0)
pb = f.posizione_banda(close, sma, 0.02)
assert list(pb) == [1, 1, 1, 0, 1], list(pb)
print("ok  banda")
# 5. strategia: costo per cambio e rendimento composto
lr = np.log1p(np.array([0.1, 0.1, -0.1, 0.1]))
pos = np.array([1, 1, 0, 1])
atteso = lr[0] + lr[1] + lr[3] + 2 * np.log(1 - 0.001)
uguale(f.log_strategia(lr, pos, 0.001), atteso, nome="log della strategia con costi")
uguale(f.cagr_da_log(2 * np.log(1.1), 2.0), 0.10, nome="rendimento composto")
print("Tutti i controlli superati.")
