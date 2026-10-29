"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def uguale(a, b, tol=1e-9, nome=""):
    assert abs(a - b) < tol, f"{nome}: {a} != {b}"
    print(f"ok  {nome}")


# 1. volatilità passata: rendimenti alternati +1% / -1% -> deviazione standard campionaria nota
lr = np.tile([0.01, -0.01], 20)
p = f.vol_realizzata_passata(lr, 4, 252)
assert np.isnan(p[:3]).all()
atteso = np.std([0.01, -0.01, 0.01, -0.01], ddof=1) * np.sqrt(252) * 100
uguale(p[3], atteso, nome="volatilità passata")
# 2. futura = passata spostata: la futura in t è la passata in t+n
fu = f.vol_realizzata_futura(lr, 4, 252)
uguale(fu[0], p[4], nome="volatilità futura in t uguale alla passata in t+n")
assert np.isnan(fu[-4:]).all()
print("ok  ultime posizioni senza futuro")
# nessuna informazione dal futuro nella passata: cambiare un rendimento dopo t non modifica p[t]
lr2 = lr.copy()
lr2[10:] = 0.05
p2 = f.vol_realizzata_passata(lr2, 4, 252)
uguale(p2[9], p[9], nome="la passata in t non dipende da dati dopo t")
# 3. regressione su dati esatti
x = np.arange(10.0)
a, b, r2 = f.regressione(x, 3.0 + 2.0 * x)
uguale(a, 3.0, tol=1e-9, nome="intercetta")
uguale(b, 2.0, tol=1e-9, nome="pendenza")
uguale(r2, 1.0, tol=1e-9, nome="R quadro perfetto")
rng = np.random.default_rng(1)
xx = rng.normal(size=5000)
a, b, r2 = f.regressione(xx, rng.normal(size=5000))
assert r2 < 0.01
print("ok  R quadro vicino a zero senza relazione")
print("Tutti i controlli superati.")
