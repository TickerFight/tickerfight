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


# 1. Rendimenti e valore: crescita costante dell'1% al giorno, sempre investiti
c = serie(100 * 1.01 ** np.arange(11))
r = m.rendimenti(c)
v = m.valore(r, pd.Series(True, index=c.index))
controlla("rendimento del primo giorno è zero", r.iloc[0] == 0.0)
controlla("valore dopo dieci giorni di +1% = 1,01^10", abs(v.iloc[-1] - 1.01 ** 10) < 1e-12)

# 2. In cassa il valore non cambia
v0 = m.valore(r, pd.Series(False, index=c.index))
controlla("in cassa il valore resta 1", (v0 == 1.0).all())

# 3. Il ritardo: ritardo 0 lascia il segnale com'è, ritardo 1 lo sposta di un giorno
s = pd.Series([False, True, True, False, True], index=c.index[:5])
controlla("ritardo 0 = segnale", (m.posizione(s, 0) == s).all())
controlla("ritardo 1 = segnale di ieri", list(m.posizione(s, 1)) == [False, False, True, True, False])
controlla("ritardo 2 = segnale di due giorni fa", list(m.posizione(s, 2)) == [False, False, False, True, True])
controlla("la posizione è booleana", m.posizione(s, 1).dtype == bool)
try:
    m.posizione(s, -1)
    controlla("ritardo negativo rifiutato", False)
except ValueError:
    controlla("ritardo negativo rifiutato", True)

# 4. Nessun look-ahead nella versione onesta: tagliare il futuro non cambia la posizione di oggi
rng = np.random.default_rng(3)
close = serie(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 700))))
sig_pieno = m.segnale_medie(close, 10, 40)
pos_pieno = m.posizione(sig_pieno, 1)
ok_taglio = True
for taglio in (100, 250, 400, 650):
    sig_t = m.segnale_medie(close.iloc[:taglio], 10, 40)
    pos_t = m.posizione(sig_t, 1)
    ok_taglio &= bool((pos_t.values == pos_pieno.iloc[:taglio].values).all())
controlla("la posizione onesta non cambia se si taglia il futuro", ok_taglio)

# 5. Il segnale con ritardo 0 invece guarda la chiusura di oggi: cambiare il prezzo di oggi cambia la posizione di oggi
close_su, close_giu = close.copy(), close.copy()
close_su.iloc[-1] = close.iloc[-2] * 1.5       # oggi la chiusura sale
close_giu.iloc[-1] = close.iloc[-2] * 0.5      # oggi la chiusura scende
sig_a, sig_b = m.segnale_un_giorno(close_su), m.segnale_un_giorno(close_giu)
controlla("segnale e posizione del giorno cambiano se cambia la chiusura di oggi (ritardo 0)",
          m.posizione(sig_a, 0).iloc[-1] != m.posizione(sig_b, 0).iloc[-1])
controlla("con ritardo 1 la posizione di oggi non dipende dalla chiusura di oggi",
          m.posizione(sig_a, 1).iloc[-1] == m.posizione(sig_b, 1).iloc[-1])

# 6. La regola di un giorno con look-ahead è sempre investita nei giorni di rialzo e mai in quelli di ribasso
rend = m.rendimenti(close)
pos_cheat = m.posizione(m.segnale_un_giorno(close), 0)
controlla("con look-ahead la regola di un giorno guadagna solo nei giorni di rialzo", bool((rend[pos_cheat] > 0).all()))
controlla("con look-ahead non prende mai un giorno di ribasso", bool((rend[~pos_cheat] <= 0).all()))

# 7. Su dati inventati con andamento a zigzag, il look-ahead vale di più dell'onesto, e il valore non è mai negativo
zig = serie(100 + np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1], float))
rz = m.rendimenti(zig)
sz = m.segnale_un_giorno(zig)
vc, vo = m.valore(rz, m.posizione(sz, 0)), m.valore(rz, m.posizione(sz, 1))
controlla("con look-ahead sullo zigzag il valore sale, con segnale onesto scende", vc.iloc[-1] > 1 > vo.iloc[-1])

# 8. CAGR e perdita massima
v2 = pd.Series([1.0, 1.2, 0.9, 1.5])
controlla("perdita massima = 0,9/1,2 - 1", abs(m.perdita_massima(v2) - (0.9 / 1.2 - 1)) < 1e-12)
controlla("CAGR su due anni di un raddoppio", abs(m.cagr(pd.Series([1.0, 2.0]), 2.0) - (2 ** 0.5 - 1)) < 1e-12)

# 9. Il segnale medie 50/200 non esiste prima di avere duecento chiusure
s200 = m.segnale_medie(serie(100 + np.arange(300.0)), 50, 200)
controlla("nessun segnale prima di avere la media lenta", not s200.iloc[:199].any())

print(f"\nVerifica del motore: {n_ok} controlli superati.")
