"""Controlli del motore vettoriale su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import motore_vettoriale as m

n_ok = 0


def controlla(nome: str, condizione: bool) -> None:
    global n_ok
    print(("OK   " if condizione else "FAIL ") + nome)
    if not condizione:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


def serie(valori) -> pd.Series:
    return pd.Series(np.asarray(valori, float), index=pd.bdate_range("2020-01-01", periods=len(valori)))


# 1. Rendimenti e valore
c = serie(100 * 1.01 ** np.arange(11))
r = m.rendimenti(c)
controlla("rendimento del primo giorno è zero", r.iloc[0] == 0.0)
controlla("valore dopo dieci giorni di +1% = 1,01^10", abs(m.valore(r, pd.Series(True, index=c.index)).iloc[-1] - 1.01 ** 10) < 1e-12)
controlla("in cassa il valore resta 1", (m.valore(r, pd.Series(False, index=c.index)) == 1.0).all())

# 2. Il ritardo
s = pd.Series([False, True, True, False, True], index=c.index[:5])
controlla("ritardo 1 = segnale di ieri", list(m.posizione(s, 1)) == [False, False, True, True, False])
controlla("ritardo 2 = segnale di due giorni fa", list(m.posizione(s, 2)) == [False, False, False, True, True])
try:
    m.posizione(s, -1)
    controlla("ritardo negativo rifiutato", False)
except ValueError:
    controlla("ritardo negativo rifiutato", True)

# 3. Nessun look-ahead: tagliare il futuro non cambia la posizione onesta di oggi
rng = np.random.default_rng(3)
close = serie(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 700))))
pos_pieno = m.posizione(m.segnale_sopra_media(close, 50), 1)
ok = True
for taglio in (100, 250, 400, 650):
    pos_t = m.posizione(m.segnale_sopra_media(close.iloc[:taglio], 50), 1)
    ok &= bool((pos_t.values == pos_pieno.iloc[:taglio].values).all())
controlla("la posizione onesta non cambia se si taglia il futuro", ok)

# 4. Segnale sopra la media: non esiste prima di avere abbastanza chiusure
sg = m.segnale_sopra_media(serie(100 + np.arange(300.0)), 200)
controlla("nessun segnale prima di avere la media", not sg.iloc[:199].any())
controlla("serie sempre in salita: sopra la media dopo l'avvio", bool(sg.iloc[199:].all()))

# 5. CAGR e perdita massima
v2 = pd.Series([1.0, 1.2, 0.9, 1.5])
controlla("perdita massima = 0,9/1,2 - 1", abs(m.perdita_massima(v2) - (0.9 / 1.2 - 1)) < 1e-12)
controlla("CAGR su due anni di un raddoppio", abs(m.cagr(pd.Series([1.0, 2.0]), 2.0) - (2 ** 0.5 - 1)) < 1e-12)

# 6. Blocchi e calendari casuali
p = np.array([True, True, False, True, False, False, False, True])
b = m.blocchi(p)
controlla("blocchi: stati e lunghezze", b == [(True, 2), (False, 1), (True, 1), (False, 3), (True, 1)])
controlla("blocchi: la somma delle lunghezze è la lunghezza", sum(l for _, l in b) == len(p))
ok_q, ok_c, ok_len = True, True, True
for seme in range(50):
    q = m.calendario_casuale(b, np.random.default_rng(seme))
    ok_q &= int(q.sum()) == int(p.sum())
    ok_len &= len(q) == len(p)
    ok_c &= len(m.blocchi(q)) == len(b) and q[0] == p[0]
controlla("calendario casuale: stessa lunghezza", ok_len)
controlla("calendario casuale: stessa quota investita", ok_q)
controlla("calendario casuale: stesso numero di blocchi e stesso stato iniziale", ok_c)
lungo = np.repeat([True, False, True, False, True, False], [5, 3, 7, 2, 4, 9])
diversi = any(not np.array_equal(m.calendario_casuale(m.blocchi(lungo), np.random.default_rng(k)), lungo) for k in range(20))
controlla("calendario casuale: l'ordine dei blocchi cambia", diversi)

# 7. Volatilità
rr = pd.Series([0.01, -0.01] * 50)
controlla("volatilità annua di ±1% al giorno", abs(m.volatilita_annua(rr, pd.Series(True, index=rr.index)) - rr.std() * np.sqrt(252)) < 1e-12)

print(f"\nVerifica del motore: {n_ok} controlli superati.")
