"""Controlli di funzioni.py su dati inventati: se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def main():
    # VIX: tre episodi ben separati
    v = np.full(400, 15.0)
    v[100:103] = 35.0
    v[300] = 31.0
    v[301] = 12.0
    v[302] = 33.0     # entro la quiete dal precedente: non è un nuovo episodio
    ep = f.episodi(v, 30.0, 63)
    assert list(ep) == [100, 300], ep
    # un episodio che continua a stare sopra non ne apre altri
    v2 = np.full(300, 15.0); v2[100:200] = 40.0
    assert list(f.episodi(v2, 30.0, 63)) == [100]
    # nessun episodio prima che passi la quiete iniziale
    v3 = np.full(100, 15.0); v3[10] = 40.0
    assert len(f.episodi(v3, 30.0, 63)) == 0
    # rendimenti
    c = 100.0 * 1.01 ** np.arange(400)
    ent = np.array([101, 390])
    r = f.rendimenti_forward(c, ent, 21)
    assert len(r) == 1 and abs(r[0] - (1.01 ** 21 - 1)) < 1e-9
    # minimo successivo: serie che scende poi sale
    c2 = np.r_[100.0, 90.0, 95.0, 110.0, 120.0]
    m = f.minimo_successivo(c2, np.array([0]), 3)
    assert abs(m[0] - (-0.10)) < 1e-12
    # scimmie: con rendimenti tutti uguali la media è sempre quella
    rng = np.random.default_rng(1)
    c3 = 100.0 * 1.001 ** np.arange(500)
    s = f.scimmie_medie(c3, np.arange(10, 200), 5, 21, 50, rng)
    assert np.allclose(s, 1.001 ** 21 - 1)
    print("verifica_motore: tutto ok")


if __name__ == "__main__":
    main()
