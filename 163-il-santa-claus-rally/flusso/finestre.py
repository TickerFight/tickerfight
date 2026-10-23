"""Funzioni della finestra del Santa Claus rally: trovare le finestre, simulare in modo veloce le scimmie.

Una finestra con k sedute di dicembre e m di gennaio: si compra alla chiusura della (k+1)-esima seduta contando dalla fine
di dicembre (così restano k sedute da vivere a dicembre) e si vende alla chiusura della m-esima seduta di gennaio
(se m = 0, all'ultima seduta di dicembre). Durata: k + m sedute da chiusura a chiusura.
"""
import numpy as np
import pandas as pd

import simulazione as s


def trova_finestre(indice: pd.DatetimeIndex, k: int, m: int):
    """Restituisce (entrata, uscita, anno_dicembre): posizioni nell'indice e anno del dicembre di ogni finestra completa."""
    anno, mese = indice.year.to_numpy(), indice.month.to_numpy()
    ent, usc, anni = [], [], []
    for a in range(int(anno.min()), int(anno.max())):
        dic = np.flatnonzero((anno == a) & (mese == 12))
        gen = np.flatnonzero((anno == a + 1) & (mese == 1))
        if len(dic) < k + 1 or len(gen) < max(m, 1):
            continue
        ent.append(int(dic[-(k + 1)]))
        usc.append(int(gen[m - 1]) if m > 0 else int(dic[-1]))
        anni.append(a)
    return np.array(ent, dtype=int), np.array(usc, dtype=int), np.array(anni, dtype=int)


def finale_veloce(C: np.ndarray, anno_uscita: np.ndarray, ent: np.ndarray, usc: np.ndarray, capitale: float,
                  commissione: float, aliquota: float) -> tuple[float, float]:
    """Valore finale netto e tasse di una sequenza di finestre (acquisto e vendita alla chiusura, cambio 1).
    Stesse regole di simulazione.simula: commissione su ogni ordine, tassa con compensazione delle minusvalenze."""
    zaino = s.Zaino(aliquota)
    cassa, tasse = float(capitale), 0.0
    for e, x, a in zip(ent, usc, anno_uscita):
        investito = cassa - commissione
        if investito <= 0:
            continue
        azioni = investito / C[e]
        netto = azioni * C[x] - commissione
        t = zaino.tassa(int(a), netto - cassa)
        tasse += t
        cassa = netto - t
    return cassa, tasse


def scimmie(C: np.ndarray, ini: np.ndarray, durata: int, fine_ultimo: int, n_scimmie: int, rng) -> np.ndarray:
    """Posizioni di entrata (n_scimmie x K): una finestra per anno, piazzata a caso dentro il blocco dell'anno.
    Il blocco k va dall'entrata reale k a quella k+1 (l'ultimo fino a fine_ultimo); la scimmia ha la stessa durata."""
    fine = np.r_[ini[1:], fine_ultimo]
    alto = np.maximum(fine - durata - 1, ini)
    return rng.integers(ini, alto + 1, size=(n_scimmie, len(ini)))
