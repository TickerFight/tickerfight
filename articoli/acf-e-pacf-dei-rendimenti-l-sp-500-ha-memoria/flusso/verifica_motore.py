"""Controlli delle funzioni su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import acf as acf_sm

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

x = rng.normal(0, 0.01, 4000)
controlla("l'ACF coincide con quella di statsmodels", np.allclose(fx.acf(x, 10), acf_sm(x, nlags=10, fft=True), atol=1e-8))
bianco = fx.acf(x, 20)
controlla("rumore bianco: tutte le autocorrelazioni dentro quattro errori standard", np.all(np.abs(bianco[1:]) < 4 / np.sqrt(len(x))))
q, p = fx.ljung_box(bianco, len(x), 20)
controlla("rumore bianco: Ljung-Box non rifiuta a livello 0,001", p > 0.001)

a = fx.ar1(rng, 20000, 0.5, 0.01)
ra = fx.acf(a, 5)
controlla("AR(1) con phi 0,5: ACF al primo ritardo vicino a 0,5", abs(ra[1] - 0.5) < 0.02)
controlla("AR(1) con phi 0,5: ACF al secondo ritardo vicino a 0,25", abs(ra[2] - 0.25) < 0.02)
pa = fx.pacf_da_acf(ra)
controlla("AR(1): la PACF al primo ritardo uguaglia l'ACF", abs(pa[1] - ra[1]) < 1e-12)
controlla("AR(1): la PACF dopo il primo ritardo è quasi zero", np.all(np.abs(pa[2:]) < 0.03))
q2, p2 = fx.ljung_box(fx.acf(a, 20), len(a), 20)
controlla("AR(1): Ljung-Box rifiuta con decisione", p2 < 1e-10)

ar2 = np.zeros(20000)
e = rng.normal(0, 1, 20000)
for t in range(2, len(ar2)):
    ar2[t] = 0.5 * ar2[t - 1] - 0.3 * ar2[t - 2] + e[t]
pa2 = fx.pacf_da_acf(fx.acf(ar2, 5))
controlla("AR(2): la PACF al secondo ritardo vicino a -0,3", abs(pa2[2] + 0.3) < 0.03)
controlla("AR(2): la PACF dal terzo ritardo è quasi zero", np.all(np.abs(pa2[3:]) < 0.03))

h = fx.holm([0.01, 0.04, 0.03])
controlla("Holm: ordine e valori attesi", np.allclose(h, [0.03, 0.06, 0.06]))
controlla("p-value normale a due code: z=1,96 vale circa 0,05", abs(fx.p_normale(1.96) - 0.05) < 0.001)

# volatilità a grappoli: ACF dei valori assoluti positiva anche se i rendimenti non hanno memoria
sigma = np.exp(fx.ar1(rng, 20000, 0.98, 0.15))
g = rng.normal(0, 1, 20000) * sigma
controlla("grappoli di volatilità: rendimenti senza memoria", abs(fx.acf(g, 1)[1]) < 4 / np.sqrt(len(g)))
controlla("grappoli di volatilità: valori assoluti con memoria", fx.acf(np.abs(g), 1)[1] > 0.1)

# il rimescolamento distrugge la memoria dei valori assoluti
perm = rng.permutation(g)
controlla("rimescolati, i valori assoluti perdono la memoria", abs(fx.acf(np.abs(perm), 1)[1]) < 4 / np.sqrt(len(g)))
print(f"{n_ok} controlli superati")
