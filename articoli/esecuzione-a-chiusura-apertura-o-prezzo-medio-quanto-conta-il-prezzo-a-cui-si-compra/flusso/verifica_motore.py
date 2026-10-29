"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def ok(nome, cond):
    assert cond, nome
    print(f"ok  {nome}")


# 1. media mobile: 1, 2, 3, 4, 5 con finestra 3
ok("media mobile semplice", np.allclose(f.sma(np.arange(1.0, 6.0), 3)[2:], [2.0, 3.0, 4.0]) and np.isnan(f.sma(np.arange(1.0, 6.0), 3)[:2]).all())
# 2. posizione: prezzi crescenti -> sempre investito dopo la partenza
p = f.posizione(np.arange(1.0, 30.0), 5)
ok("prezzi crescenti: sempre investito", np.nanmin(p) == 1.0 and np.isnan(p[:4]).all())
# 3. serie con segnale che cambia a un giorno noto: closes 10,10,10,10,20 (media di 3 giorni): al giorno 4 la chiusura 20 > media 13,3 -> investito
c = np.array([10.0, 10, 10, 10, 20, 20, 20, 20])
o = c.copy()
a = c.copy()
pos = f.posizione(c, 3)
ok("il segnale scatta il giorno del salto", pos[3] == 0.0 and pos[4] == 1.0)
# 4. esecuzione: salto dell'ultima riga. Il segnale scatta alla chiusura del giorno 4 (da 10 a 20). Chi esegue alla stessa chiusura del giorno 4
#    guadagna il rendimento del giorno 5 (20 -> 20 = 0); nessun look-ahead qui perché il prezzo non si muove dopo. Verifica con prezzi che si muovono.
c = np.array([10.0, 10, 10, 10, 20, 24, 24, 24])
o = np.array([10.0, 10, 10, 10, 20, 22, 24, 24])    # apertura del giorno 5 a 22, chiusura a 24
a = (o + c) / 2
pos = f.posizione(c, 3)
r_stessa = f.log_rendimenti_regola(o, c, a, pos, "stessa_chiusura", 0.0)
r_open = f.log_rendimenti_regola(o, c, a, pos, "apertura", 0.0)
r_dopo = f.log_rendimenti_regola(o, c, a, pos, "chiusura_dopo", 0.0)
ok("giorno 5, stessa chiusura: guadagna da 20 a 24", abs(r_stessa[5] - np.log(24 / 20)) < 1e-12)
ok("giorno 5, apertura: guadagna da 22 a 24", abs(r_open[5] - np.log(24 / 22)) < 1e-12)
ok("giorno 5, chiusura del giorno dopo: non guadagna ancora", abs(r_dopo[5]) < 1e-12)
ok("giorno 6, chiusura del giorno dopo: entra al 24 e non guadagna", abs(r_dopo[6]) < 1e-12)
# 5. costo: un cambio di posizione costa log(1 - costo)
r_costo = f.log_rendimenti_regola(o, c, a, pos, "apertura", 0.01)
ok("il costo si paga una volta sul cambio", abs((r_open[5] - r_costo[5]) - (-np.log(0.99))) < 1e-12 and abs(r_open[6] - r_costo[6]) < 1e-12)
# 6. metriche
r = np.full(252, np.log(1.10) / 252)
m = f.metriche(r, 252)
ok("CAGR di un rendimento costante", abs(m["cagr"] - 0.10) < 1e-9 and abs(m["dd"]) < 1e-12)
# 7. numero di cambi
ok("conteggio dei cambi di posizione", f.cambi(np.array([np.nan, 0, 0, 1, 1, 0, 1])) == 3)
# 8. bootstrap: differenza costante -> intervallo stretto attorno al valore
rng = np.random.default_rng(1)
lo, hi = f.bootstrap_differenza(np.full(500, 0.001), 200, 21, 252, 0.95, rng)
ok("differenza costante: intervallo coincide col valore", abs(lo - 0.252) < 1e-9 and abs(hi - 0.252) < 1e-9)
