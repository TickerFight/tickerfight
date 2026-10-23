"""Funzioni dell'esperimento: prezzi del primo giorno di Borsa di ogni mese, valore di lump sum e PAC, rimescolamento.

Convenzioni: p[i] è il prezzo del primo giorno di Borsa del mese i. Partendo dal mese t, il lump sum compra tutto in t;
il PAC compra BUDGET/N_RATE in ciascuno dei mesi t, t+1, ..., t+N_RATE-1. Entrambi sono valutati al prezzo p[t+h].
Quote frazionarie; la cassa non ancora investita non rende; la commissione è in euro fissi per ordine e si sottrae al valore finale.
"""
import numpy as np
import pandas as pd


def prezzi_mensili(chiusure: pd.Series) -> pd.Series:
    """Chiusura del primo giorno di Borsa di ogni mese (indice = data di quel giorno)."""
    s = chiusure.sort_index()
    mese = s.index.to_period("M")
    return s.groupby(mese).head(1).rename("prezzo")


def valore_lump(p: np.ndarray, h: int, budget: float, comm: float) -> np.ndarray:
    """Valore dopo h mesi del lump sum per ogni mese di partenza t = 0 .. len(p)-h-1."""
    n = len(p) - h
    return budget * p[h:h + n] / p[:n] - comm


def valore_pac(p: np.ndarray, h: int, budget: float, rate: int, comm: float) -> np.ndarray:
    """Valore dopo h mesi del PAC (h >= rate) per ogni mese di partenza t."""
    if h < rate:
        raise ValueError("l'orizzonte deve coprire tutte le rate")
    n = len(p) - h
    inv = np.r_[0.0, np.cumsum(1.0 / p)]                      # somma di 1/p[0..i-1]
    t = np.arange(n)
    somma = inv[t + rate] - inv[t]                            # somma di 1/p[t..t+rate-1]
    return (budget / rate) * p[h:h + n] * somma - rate * comm


def valore_scimmia(p: np.ndarray, h: int, budget: float, rate: int, n_scimmie: int, rng) -> np.ndarray:
    """Matrice (n_partenze, n_scimmie): ogni scimmia piazza le rate in mesi a caso (con ripetizione) tra t e t+rate-1."""
    n = len(p) - h
    t = np.arange(n)[:, None, None]
    sc = rng.integers(0, rate, size=(1, n_scimmie, rate))
    acq = p[t + sc]                                            # prezzi a cui compra
    return (budget / rate) * p[h:h + n][:, None] * (1.0 / acq).sum(axis=2)


def serie_rimescolata(p: np.ndarray, rng) -> np.ndarray:
    """Stessi rendimenti mensili, in ordine casuale, dallo stesso prezzo iniziale."""
    r = np.diff(np.log(p))
    return p[0] * np.exp(np.r_[0.0, np.cumsum(rng.permutation(r))])


def quota_lump_rimescolate(p: np.ndarray, h: int, budget: float, rate: int, n: int, rng) -> np.ndarray:
    """Quota di partenze in cui il lump sum batte il PAC (senza commissioni) in ciascuna di n storie rimescolate."""
    out = np.empty(n)
    for k in range(n):
        q = serie_rimescolata(p, rng)
        out[k] = np.mean(valore_lump(q, h, budget, 0.0) > valore_pac(q, h, budget, rate, 0.0))
    return out


def holm(p: dict) -> dict:
    ordine = sorted(p, key=p.get)
    m = len(ordine)
    out, massimo = {}, 0.0
    for k, nome in enumerate(ordine):
        massimo = max(massimo, min(1.0, (m - k) * p[nome]))
        out[nome] = massimo
    return out
