"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np
import pandas as pd

import funzioni as f


def uguale(a, b, tol=1e-9, nome=""):
    assert abs(a - b) < tol, f"{nome}: {a} != {b}"
    print(f"ok  {nome}")


rng = np.random.default_rng(1)
# 1. CAGR: rendimento logaritmico costante
uguale(f.cagr_da_media(np.log(1.10) / 252, 252), 0.10, nome="CAGR di un rendimento costante del 10%")
# 2. intervallo con formula: contiene il valore noto e l'ampiezza scende con la radice del numero di anni
x = rng.normal(0.0004, 0.01, 252 * 40)
c, lo, hi = f.intervallo_formula(x, 252, 1.96)
assert lo < c < hi, "centro nell'intervallo"
print("ok  il CAGR sta dentro il proprio intervallo")
a1 = f.intervallo_formula(x[: 252 * 10], 252, 1.96)
a4 = f.intervallo_formula(x, 252, 1.96)
rapp = (a1[2] - a1[1]) / (a4[2] - a4[1])
assert 1.7 < rapp < 2.4, f"rapporto delle ampiezze {rapp}"
print("ok  quadruplicando i dati l'ampiezza si dimezza circa")
# 3. bootstrap sui giorni e formula coincidono approssimativamente su dati indipendenti
bl, bh = f.bootstrap_giorni(x, 600, 252, 0.95, rng)
assert abs((bh - bl) - (hi - lo)) / (hi - lo) < 0.15, "bootstrap giorni vs formula"
print("ok  bootstrap sui giorni vicino alla formula")
# 4. bootstrap a blocchi su dati indipendenti: ampiezza simile; su dati con memoria forte: più larga
kl, kh = f.bootstrap_blocchi(x, 600, 21, 252, 0.95, rng)
assert 0.8 < (kh - kl) / (hi - lo) < 1.25, "blocchi su dati indipendenti"
m = np.zeros(252 * 40)
e = rng.normal(0, 0.01, len(m))
for t in range(1, len(m)):
    m[t] = 0.3 * m[t - 1] + e[t]
_, fl, fh = f.intervallo_formula(m, 252, 1.96)
ml, mh = f.bootstrap_blocchi(m, 600, 63, 252, 0.95, rng)
assert (mh - ml) > 1.2 * (fh - fl), "blocchi su dati con memoria"
print("ok  con memoria forte il bootstrap a blocchi è più largo della formula")
# 5. copertura su dati iid: vicina al 95%
y = rng.normal(0.0003, 0.01, 252 * 200)
cop, n = f.copertura(y, 252 * 10, np.arange(0, len(y) - 252 * 10, 21), y.mean() * 252, 252, 1.959964)
assert 0.88 < cop <= 1.0 and n > 100, f"copertura {cop}"
print("ok  copertura vicina al valore nominale su dati indipendenti")
# 6. anni necessari: sigma 20%, semiampiezza 1 punto -> (1,96*20)^2 = 1536,64 anni
uguale(f.anni_necessari(0.20, 0.01, 1.96), (1.96 * 20) ** 2, tol=1e-6, nome="anni necessari")
# 7. inizi_mese
d = pd.bdate_range("2020-01-01", periods=70)
i = f.inizi_mese(d)
assert i[0] == 0 and d[i[1]].month == 2, "inizi_mese"
print("ok  inizi_mese")
# 8. copertura onesta su dati indipendenti: vicina al 95%; con un cambio di regime (media diversa nella seconda metà) crolla
cf, nf = f.copertura_fuori(y, 252 * 10, np.arange(0, len(y) - 252 * 10, 21), 252, 1.959964)
assert 0.88 < cf <= 1.0 and nf > 100, f"copertura onesta {cf}"
print("ok  copertura onesta vicina al valore nominale su dati indipendenti")
y2 = y.copy()
y2[len(y2) // 2:] += 0.0006
cf2, _ = f.copertura_fuori(y2, 252 * 10, np.arange(0, len(y2) - 252 * 10, 21), 252, 1.959964)
assert cf2 < cf - 0.1, f"copertura con regimi {cf2} contro {cf}"
print("ok  con regimi diversi la copertura onesta scende")
