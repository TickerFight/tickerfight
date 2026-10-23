"""Funzioni dell'esperimento: prezzi del primo giorno di Borsa di ogni mese, valore di lump sum e PAC, scimmie, massimi.

Convenzioni: p[i] è il prezzo del primo giorno di Borsa del mese i. Partendo dal mese t, il lump sum compra tutto in t;
il PAC compra BUDGET/N in ciascuno dei mesi t, t+1, ..., t+N-1. Entrambi sono valutati al prezzo p[t+h].
Quote frazionarie; la cassa non ancora investita non rende; nessun costo (confronto lordo).
"""
import numpy as np
import pandas as pd


def prezzi_mensili(chiusure: pd.Series) -> pd.Series:
    """Chiusura del primo giorno di Borsa di ogni mese (indice = data di quel giorno)."""
    s = chiusure.sort_index()
    mese = s.index.to_period("M")
    return s.groupby(mese).head(1).rename("prezzo")


def valore_lump(p: np.ndarray, h: int, budget: float) -> np.ndarray:
    """Valore dopo h mesi del lump sum per ogni mese di partenza t = 0 .. len(p)-h-1."""
    n = len(p) - h
    return budget * p[h:h + n] / p[:n]


def valore_pac(p: np.ndarray, h: int, budget: float, rate: int) -> np.ndarray:
    """Valore dopo h mesi del PAC a `rate` rate (h >= rate) per ogni mese di partenza t."""
    if h < rate:
        raise ValueError("l'orizzonte deve coprire tutte le rate")
    n = len(p) - h
    inv = np.r_[0.0, np.cumsum(1.0 / p)]                      # somma di 1/p[0..i-1]
    t = np.arange(n)
    somma = inv[t + rate] - inv[t]                            # somma di 1/p[t..t+rate-1]
    return (budget / rate) * p[h:h + n] * somma


def valore_scimmia(p: np.ndarray, h: int, budget: float, rate: int, n_scimmie: int, rng) -> np.ndarray:
    """Matrice (n_partenze, n_scimmie): ogni scimmia piazza le rate in mesi a caso (con ripetizione) tra t e t+rate-1."""
    n = len(p) - h
    t = np.arange(n)[:, None, None]
    sc = rng.integers(0, rate, size=(1, n_scimmie, rate))
    acq = p[t + sc]                                            # prezzi a cui compra
    return (budget / rate) * p[h:h + n][:, None] * (1.0 / acq).sum(axis=2)


def vicino_ai_massimi(p: np.ndarray, soglia: float) -> np.ndarray:
    """True se il prezzo del mese è entro `soglia` dal massimo dei prezzi fino a quel mese incluso (nessun look-ahead)."""
    massimo = np.maximum.accumulate(p)
    return p >= massimo * (1.0 - soglia)


def decennio(data: pd.Timestamp) -> int:
    return (data.year // 10) * 10
