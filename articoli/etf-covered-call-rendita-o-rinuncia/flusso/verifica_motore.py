"""Controlli di motore.py su dati inventati, con risultati calcolabili a mano. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import funzioni as f
import motore as m

rng = np.random.default_rng(1)


def uguale(a, b, tol=1e-9, nome=""):
    assert abs(a - b) < tol, f"{nome}: {a} != {b}"
    print(f"ok  {nome}")


# 1. rendimento composto: +10% e -10% in due sedute
r = np.array([0.10, -0.10])
uguale(m.equity(r)[-1], 0.99, nome="equity")
uguale(m.cagr(np.full(252, 0.0), 252), 0.0, nome="cagr nullo")
uguale(m.cagr(np.full(252, 0.001), 252), 1.001 ** 252 - 1, nome="cagr costante")
# 2. perdita massima: sale a 1,2 poi scende a 0,6 -> -50%
uguale(m.max_dd(np.array([0.2, -0.5])), -0.5, nome="perdita massima")
# 3. volatilità e Sharpe di una serie alternata +1% / -1%
alt = np.tile([0.01, -0.01], 126)
uguale(m.vol(alt, 252), np.std(alt, ddof=1) * np.sqrt(252), nome="volatilità")
uguale(m.sharpe(alt + 0.0, 252), 0.0, tol=1e-9, nome="Sharpe nullo")
# 4. fine mese: tre mesi finti
idx = pd.bdate_range("2020-01-01", periods=70)
fini = m.fine_mese(idx)
assert idx[fini[0]].month == 1 and idx[fini[0] + 1].month == 2, "fine mese"
print("ok  fine mese")
# 5. finestre: A cresce 1% al giorno, B ferma, C scende 1%: A vince sempre, rendimento a 10 sedute noto
T = 600
R = np.column_stack([np.full(T, 0.01), np.zeros(T), np.full(T, -0.01)])
cum = np.cumprod(1.0 + R, axis=0)
pos, rend = m.rendimento_finestre(cum, np.array([50, 100, 599]), 10)
uguale(rend[0, 0], 1.01 ** 10 - 1, nome="rendimento finestra A")
uguale(rend[0, 1], 0.0, nome="rendimento finestra B")
uguale(rend[0, 2], 0.99 ** 10 - 1, nome="rendimento finestra C")
q = m.quote_vincitrici(rend)
assert q.tolist() == [1.0, 0.0, 0.0], "quote vincitrici"
print("ok  quote vincitrici")
# 6. persistenza: se A vince sempre, passato = futuro sempre
fm = m.fine_mese(pd.bdate_range("2000-01-03", periods=T))
pa, fu = m.persistenza(cum, fm, 60)
assert len(pa) > 5 and (pa == fu).all() and (pa == 0).all(), "persistenza"
print("ok  persistenza")
# 7. permutazione: su dati indipendenti il p-value è alto; su dati identici con due classi è basso
a = rng.integers(0, 3, 300)
b = rng.integers(0, 3, 300)
_, p = m.p_permutazione(a, b, 500, rng)
assert p > 0.05, f"permutazione su dati indipendenti: p={p}"
_, p2 = m.p_permutazione(a, a, 500, rng)
assert p2 < 0.01, "permutazione su dati identici"
print("ok  permutazione")
# 8. correlazione mobile: serie identiche -> 1; opposte -> -1
x = pd.Series(rng.normal(size=300))
uguale(m.correlazione_mobile(x, x, 50).dropna().min(), 1.0, tol=1e-9, nome="correlazione 1")
uguale(m.correlazione_mobile(x, -x, 50).dropna().max(), -1.0, tol=1e-9, nome="correlazione -1")
# 9. bootstrap: due serie identiche -> differenza di Sharpe zero
d = m.bootstrap_diff_sharpe(x.to_numpy() * 0.01, x.to_numpy() * 0.01, 50, 21, 252, rng)
assert np.abs(d).max() < 1e-9, "bootstrap identico"
print("ok  bootstrap")
# 10. mensili e scimmie: tre aree con rendimento mensile costante 1%, 0, -1% -> la scimmia ha valore tra i tre estremi
Rm = np.column_stack([np.full(T, 0.0005), np.zeros(T), np.full(T, -0.0005)])
mens = m.rendimenti_mensili(Rm, fm)
uguale(np.prod(1 + mens[:, 0]), np.prod(1 + Rm[:, 0]), tol=1e-9, nome="mesi ricompongono il totale")
sc = m.scimmie_valore_finale(mens, 2000, rng)
assert (sc <= np.prod(1 + mens[:, 0]) + 1e-9).all() and (sc >= np.prod(1 + mens[:, 2]) - 1e-9).all(), "scimmie nei limiti"
print("ok  scimmie")
# 11. cattura: fondo che prende metà dei rialzi e tutti i ribassi
idx_m = np.array([0.04, -0.02, 0.02, -0.04])
fondo = np.array([0.02, -0.02, 0.01, -0.04])
su, giu = f.cattura(fondo, idx_m)
uguale(su, 0.5, nome="cattura rialzi")
uguale(giu, 1.0, nome="cattura ribassi")
# 12. peso a stessa volatilità: con liquidità costante la volatilità è lineare nel peso
ri = rng.normal(0.0004, 0.01, 2000)
liq = np.full(2000, 0.0001)
w = f.peso_stessa_volatilita(ri, liq, 0.5 * m.vol(ri, 252), 252)
uguale(w, 0.5, tol=1e-6, nome="peso a stessa volatilità")
uguale(m.vol(f.miscela(ri, liq, w), 252), 0.5 * m.vol(ri, 252), tol=1e-6, nome="volatilità della miscela")
assert f.peso_stessa_volatilita(ri, liq, 2 * m.vol(ri, 252), 252) == 1.0, "obiettivo oltre l'indice"
print("ok  peso limite")
print("Tutti i controlli superati.")
