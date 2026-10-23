"""Funzioni dell'esperimento: curve dei portafogli a pesi uguali con ribilanciamento annuale e metriche.

Convenzioni: prezzi[t, i] è la chiusura corretta del titolo i nel giorno t. I pesi dei portafogli sono decisi prima di
guardare qualunque rendimento (estrazione casuale) e restano uguali (1/k) all'inizio di ogni anno solare: nessun look-ahead.
Il valore parte da 1 nel primo giorno; il ribilanciamento avviene alla chiusura dell'ultimo giorno di Borsa dell'anno
precedente. Nessun costo, nessuna tassa.
"""
import numpy as np


def inizi_anno(anni: np.ndarray) -> list[tuple[int, int]]:
    """Per ogni anno solare, (indice del primo giorno, indice dell'ultimo giorno)."""
    out = []
    s = 0
    for t in range(1, len(anni) + 1):
        if t == len(anni) or anni[t] != anni[s]:
            out.append((s, t - 1))
            s = t
    return out


def curve_portafogli(prezzi: np.ndarray, anni: np.ndarray, pesi: np.ndarray) -> np.ndarray:
    """Valore di M portafogli (colonne di pesi, forma (N, M)) nel tempo, forma (T, M), partendo da 1.

    Dentro ogni anno il portafoglio è (prezzo / prezzo di base) @ pesi, dove la base è la chiusura dell'ultimo giorno
    dell'anno precedente; il valore della base si porta dietro quello degli anni passati.
    """
    T, M = len(prezzi), pesi.shape[1]
    V = np.ones((T, M))
    for s, e in inizi_anno(anni):
        b = s - 1 if s > 0 else 0
        ts = np.arange(max(s, 1), e + 1)
        if len(ts) == 0:
            continue
        V[ts] = V[b] * ((prezzi[ts] / prezzi[b]) @ pesi)
    return V


def cagr(V: np.ndarray, giorni_calendario: float, anno: float = 365.25) -> np.ndarray:
    """Rendimento annuo composto di ciascuna colonna di V (V[0] = valore iniziale, V[-1] finale)."""
    return (V[-1] / V[0]) ** (anno / giorni_calendario) - 1


def sharpe(V: np.ndarray, giorni_anno: int = 252, rf: float = 0.0) -> np.ndarray:
    r = V[1:] / V[:-1] - 1 - rf / giorni_anno
    sd = r.std(axis=0, ddof=1)
    return np.where(sd > 0, r.mean(axis=0) / np.where(sd > 0, sd, 1) * np.sqrt(giorni_anno), np.nan)


def max_drawdown(V: np.ndarray) -> np.ndarray:
    """Massima perdita dal massimo precedente (valore negativo o zero) per ogni colonna."""
    picco = np.maximum.accumulate(V, axis=0)
    return (V / picco - 1).min(axis=0)


def estrai_pesi(n_titoli: int, k: int, m: int, rng) -> np.ndarray:
    """M portafogli da k titoli scelti a caso (senza reinserimento) tra n_titoli, pesi 1/k. Forma (n_titoli, m)."""
    W = np.zeros((n_titoli, m))
    for j in range(m):
        W[rng.choice(n_titoli, size=k, replace=False), j] = 1.0 / k
    return W
