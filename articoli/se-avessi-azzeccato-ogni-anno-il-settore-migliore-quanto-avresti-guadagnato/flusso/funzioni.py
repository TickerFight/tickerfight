"""Funzioni dell'esperimento: rendimenti per periodo, scelta con il senno di poi, scimmie, regola realizzabile, tasse.

R è una matrice (periodi x settori) di rendimenti semplici. La regola realizzabile usa solo rendimenti dei periodi
precedenti (nessun look-ahead); la scelta «con il senno di poi» lo usa apposta, ed è il punto dell'articolo.
"""
import numpy as np
import pandas as pd


def rendimenti_periodo(prezzi: pd.DataFrame, freq: str, anno_inizio: int, anno_fine: int) -> pd.DataFrame:
    """Rendimenti per periodo (anno 'YE', trimestre 'QE', mese 'ME') dall'ultimo prezzo del periodo prima all'ultimo del periodo."""
    ultimo = prezzi.sort_index().resample(freq).last()
    r = ultimo.pct_change().dropna(how="all")
    return r[(r.index.year >= anno_inizio) & (r.index.year <= anno_fine)]


def migliore_ex_post(R: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per ogni periodo, indice del settore col rendimento più alto e quel rendimento."""
    idx = R.argmax(axis=1)
    return idx, R[np.arange(len(R)), idx]


def cagr(r: np.ndarray, anni: float) -> float:
    return float(np.exp(np.sum(np.log1p(r)) / anni) - 1.0)


def curva_capitale(r: np.ndarray, capitale: float) -> np.ndarray:
    return capitale * np.cumprod(1 + r)


def scimmie(R: np.ndarray, n: int, anni: float, rng) -> np.ndarray:
    """Rendimento annuo composto di n scimmie: ognuna sceglie un settore a caso in ogni periodo."""
    T, K = R.shape
    lr = np.log1p(R)
    idx = rng.integers(0, K, size=(n, T))
    return np.exp(lr[np.arange(T)[None, :], idx].sum(axis=1) / anni) - 1.0


def vincitore_precedente(R: np.ndarray) -> np.ndarray:
    """Rendimento del periodo t del settore che ha vinto il periodo t-1 (per t >= 1). Nessun look-ahead."""
    idx = R.argmax(axis=1)
    return R[np.arange(1, len(R)), idx[:-1]]


def rango_vincitore_precedente(R: np.ndarray) -> np.ndarray:
    """Posizione (1 = migliore) che nel periodo t occupa il settore che ha vinto il periodo t-1."""
    idx = R.argmax(axis=1)
    out = []
    for t in range(1, len(R)):
        ordine = (-R[t]).argsort().argsort() + 1
        out.append(ordine[idx[t - 1]])
    return np.array(out)


def capitale_netto_rotazione(r: np.ndarray, capitale: float, costo: float, tassa: float) -> float:
    """Rotazione: a fine periodo si vende tutto (tassa sulle plusvalenze, minusvalenze riportate) e si ricompra.
    Il costo si paga su ogni acquisto e su ogni vendita; qui il primo acquisto e l'ultima vendita sono inclusi."""
    cap = capitale * (1 - costo)          # primo acquisto
    credito = 0.0
    for i, x in enumerate(r):
        guadagno = cap * x
        if guadagno < 0:
            credito += -guadagno
            imponibile = 0.0
        else:
            usa = min(credito, guadagno)
            credito -= usa
            imponibile = guadagno - usa
        cap = cap + guadagno - tassa * imponibile
        cap *= (1 - costo)                  # vendita
        if i < len(r) - 1:
            cap *= (1 - costo)              # nuovo acquisto (non dopo l'ultima vendita)
    return cap


def capitale_netto_buy_hold(r: np.ndarray, capitale: float, costo: float, tassa: float) -> float:
    """Compra all'inizio, vende alla fine; tassa sulla plusvalenza complessiva (se c'è)."""
    cap0 = capitale * (1 - costo)
    cap = cap0 * np.prod(1 + r)
    plus = max(0.0, cap - cap0)
    return (cap - tassa * plus) * (1 - costo)


def holm(p: dict) -> dict:
    ordine = sorted(p, key=p.get)
    m = len(ordine)
    out, massimo = {}, 0.0
    for k, nome in enumerate(ordine):
        massimo = max(massimo, min(1.0, (m - k) * p[nome]))
        out[nome] = massimo
    return out
