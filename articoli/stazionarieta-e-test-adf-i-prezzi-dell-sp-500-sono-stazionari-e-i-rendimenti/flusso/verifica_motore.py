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


rng = np.random.default_rng(1)
controlla("finestre non sovrapposte e complete", fx.finestre(10, 3) == [(0, 3), (3, 6), (6, 9)])
c = pd.Series(100 * 1.01 ** np.arange(5))
controlla("log-rendimento di un +1% costante", np.allclose(fx.log_rendimenti(c).to_numpy(), np.log(1.01)))
ru = rng.normal(0, 0.01, 3000)
st, p, _ = fx.adf(ru, "c", 5)
controlla("rumore bianco: l'ADF rifiuta la radice unitaria", p < 0.001)
rw = fx.random_walk(rng, 3000, 0.01)
st, p, _ = fx.adf(rw, "c", 5)
controlla("random walk: l'ADF non rifiuta", p > 0.05)
a = fx.ar1(rng, 3000, 0.5, 0.01)
st, p, _ = fx.adf(a, "c", 5)
controlla("AR(1) con phi 0,5: l'ADF rifiuta", p < 0.001)
controlla("AR(1): deviazione standard vicina a quella teorica", abs(a.std() - 0.01 / np.sqrt(1 - 0.25)) < 0.002)
st1, p1, l1 = fx.adf(rw, "ct", 20)
controlla("autolag restituisce un numero di ritardi tra 0 e 20", 0 <= l1 <= 20)
print(f"{n_ok} controlli superati")
