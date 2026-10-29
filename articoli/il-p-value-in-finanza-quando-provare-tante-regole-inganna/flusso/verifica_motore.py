"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np
from scipy import stats

import funzioni as f


def ok(nome, cond):
    assert cond, nome
    print(f"ok  {nome}")


rng = np.random.default_rng(1)
# 1. segnali: prezzi crescenti 1, 2, 3, ... -> la chiusura di ieri è sempre sopra la media delle precedenti
c = np.arange(1.0, 301.0)
S, r = f.segnali_sma(c, [5, 20], 25)
ok("prezzi crescenti: segnale sempre acceso", S.min() == 1.0 and len(S) == len(r) == 300 - 1 - 25)
ok("rendimento calcolato come c[t]/c[t-1]-1", abs(r[0] - (c[26] / c[25] - 1)) < 1e-12)
# 2. nessun look-ahead: il segnale di oggi non cambia se si altera la chiusura di oggi
c2 = c.copy()
c2[100] = 0.1
S2, _ = f.segnali_sma(c2, [5, 20], 25)
ok("il segnale del giorno 100 non dipende dalla chiusura del giorno 100", np.array_equal(S[100 - 26], S2[100 - 26]))
ok("il segnale del giorno 101 dipende dalla chiusura del giorno 100", not np.array_equal(S[101 - 26], S2[101 - 26]))
# 3. t di Welch contro scipy
x = rng.normal(0.0003, 0.01, 4000)
s = (rng.random(4000) < 0.6).astype(float)
t = f.welch_t(x, s[:, None])[0]
ref = stats.ttest_ind(x[s == 1], x[s == 0], equal_var=False).statistic
ok("t di Welch coincide con scipy", abs(t - ref) < 1e-9)
# 4. p-value normale vicino a quello di scipy con molti dati
ok("p-value normale vicino a quello di scipy", abs(f.p_normale(t)[0] - stats.ttest_ind(x[s == 1], x[s == 0], equal_var=False).pvalue) < 5e-3)
# 5. Holm e Benjamini-Hochberg: valori noti
p = np.array([0.01, 0.04, 0.03, 0.005])
h = f.holm(p)
ok("Holm: valori attesi", np.allclose(h, [0.03, 0.06, 0.06, 0.02]))
bh = f.benjamini_hochberg(p)
ok("Benjamini-Hochberg: valori attesi", np.allclose(bh, [0.02, 0.04, 0.04, 0.02]))
ok("i p-value corretti non sono mai sotto quelli grezzi", (h >= p).all() and (bh >= p).all())
# 6. spostamenti circolari su dati senza effetto: circa il 5% delle regole è «significativo» per caso
S_ind = (rng.random((3000, 50)) < 0.5).astype(float)
r_ind = rng.normal(0, 0.01, 3000)
mx, cn = f.spostamenti(r_ind, S_ind, 200, 100, rng)
ok("senza effetto: in media circa il 5% di regole sopra la soglia", 0.02 * 50 < cn.mean() < 0.09 * 50)
# 7. con un segnale vero il massimo |t| osservato supera nettamente il 95° percentile nullo
y = rng.normal(0, 0.01, 3000)
S_vero = S_ind.copy()
S_vero[:, 0] = (y > 0).astype(float)
tmax = np.abs(f.welch_t(y, S_vero)).max()
ok("segnale vero: |t| ben sopra il 95° percentile dello spostamento", tmax > np.percentile(mx, 95) * 2)
# 8. CAGR e Sharpe di serie note
ok("CAGR di un rendimento costante", abs(f.cagr(np.full(252, 0.001), 252) - (1.001 ** 252 - 1)) < 1e-9)
ok("Sharpe di una serie alternata è nullo", abs(f.sharpe(np.tile([0.01, -0.01], 100), 252)) < 1e-9)
