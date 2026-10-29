"""Funzioni dell'articolo 26: segnali da medie mobili, test t di Welch vettoriale, correzioni per test multipli, spostamenti circolari."""
import math

import numpy as np


def segnali_sma(c: np.ndarray, lunghezze, partenza: int) -> tuple[np.ndarray, np.ndarray]:
    """Dati le chiusure c[0..n], restituisce (S, r) per le sedute t = partenza + 1 .. n:
    r[t] = c[t] / c[t-1] - 1 e S[t, k] = 1 se la chiusura di ieri c[t-1] è sopra la media delle ultime N_k chiusure fino a ieri incluso."""
    c = np.asarray(c, dtype=float)
    cs = np.concatenate([[0.0], np.cumsum(c)])
    n = len(c) - 1
    t = np.arange(partenza + 1, n + 1)
    S = np.empty((len(t), len(lunghezze)))
    for j, k in enumerate(lunghezze):
        ieri = t - 1
        sma = (cs[ieri + 1] - cs[ieri + 1 - k]) / k
        S[:, j] = c[ieri] > sma
    r = c[t] / c[t - 1] - 1.0
    return S, r


def welch_t(r: np.ndarray, S: np.ndarray) -> np.ndarray:
    """Statistica t di Welch per la differenza tra il rendimento medio dei giorni con segnale (S = 1) e senza (S = 0), per ogni colonna di S."""
    m = len(r)
    n1 = S.sum(axis=0)
    n0 = m - n1
    tot1, tot2 = r.sum(), (r * r).sum()
    s1, q1 = S.T @ r, S.T @ (r * r)
    m1, m0 = s1 / n1, (tot1 - s1) / n0
    v1 = (q1 - n1 * m1 ** 2) / (n1 - 1)
    v0 = ((tot2 - q1) - n0 * m0 ** 2) / (n0 - 1)
    return (m1 - m0) / np.sqrt(v1 / n1 + v0 / n0)


def p_normale(t) -> np.ndarray:
    """P-value a due code con approssimazione normale (campioni molto grandi)."""
    t = np.atleast_1d(np.asarray(t, dtype=float))
    return np.array([math.erfc(abs(v) / math.sqrt(2)) for v in t])


def holm(p) -> np.ndarray:
    p = np.asarray(p, float)
    m = len(p)
    adj = np.empty(m)
    corrente = 0.0
    for rango, i in enumerate(np.argsort(p)):
        corrente = max(corrente, (m - rango) * p[i])
        adj[i] = min(1.0, corrente)
    return adj


def benjamini_hochberg(p) -> np.ndarray:
    """P-value corretti per il tasso di falsi scoperte (Benjamini-Hochberg)."""
    p = np.asarray(p, float)
    m = len(p)
    ordine = np.argsort(p)
    adj = np.empty(m)
    minimo = 1.0
    for rango in range(m - 1, -1, -1):
        i = ordine[rango]
        minimo = min(minimo, p[i] * m / (rango + 1))
        adj[i] = minimo
    return adj


def spostamenti(r: np.ndarray, S: np.ndarray, n: int, minimo: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """Per n spostamenti circolari dei rendimenti rispetto ai segnali: (massimo |t| tra le regole, numero di regole con |t| sopra 1,96)."""
    m = len(r)
    massimi = np.empty(n)
    conteggi = np.empty(n, dtype=int)
    for i in range(n):
        d = int(rng.integers(minimo, m - minimo))
        t = welch_t(np.roll(r, d), S)
        massimi[i] = np.abs(t).max()
        conteggi[i] = int((np.abs(t) > 1.959964).sum())
    return massimi, conteggi


def cagr(r: np.ndarray, ga: int) -> float:
    r = np.asarray(r, dtype=float)
    return float(np.prod(1.0 + r) ** (ga / len(r)) - 1.0)


def sharpe(r: np.ndarray, ga: int) -> float:
    r = np.asarray(r, dtype=float)
    return float(r.mean() / r.std(ddof=1) * math.sqrt(ga))
