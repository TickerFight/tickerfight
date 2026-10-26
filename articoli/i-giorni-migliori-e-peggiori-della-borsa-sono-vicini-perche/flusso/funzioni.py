"""Funzioni dell'esperimento: giorni estremi, distanze, volatilità di ieri, rimescolamento, filtro, scimmie.

Convenzioni: r[t] è il rendimento semplice della seduta t (da chiusura t-1 a chiusura t). Ogni stima di volatilità
"di ieri" per la seduta t usa solo rendimenti fino a t-1: nessun look-ahead.
"""
import bisect

import numpy as np
import pandas as pd


def rendimenti(chiusure: pd.Series) -> pd.Series:
    s = chiusure.sort_index()
    return s.pct_change().dropna()


def posizioni_estreme(r: np.ndarray, quota: float) -> tuple[np.ndarray, np.ndarray]:
    """Posizioni (ordinate) dei k giorni peggiori e dei k giorni migliori, con k = quota * numero di sedute."""
    k = max(1, int(round(quota * len(r))))
    peggiori = np.sort(np.argpartition(r, k - 1)[:k])
    migliori = np.sort(np.argpartition(-r, k - 1)[:k])
    return peggiori, migliori


def distanza_vicino(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Per ogni posizione di a, distanza in sedute dalla posizione più vicina di b (entrambi ordinati)."""
    i = np.searchsorted(b, a)
    sx = np.where(i > 0, a - b[np.maximum(i - 1, 0)], np.iinfo(np.int64).max // 4)
    dx = np.where(i < len(b), b[np.minimum(i, len(b) - 1)] - a, np.iinfo(np.int64).max // 4)
    return np.minimum(sx, dx)


def statistiche_vicinanza(r: np.ndarray, quota: float, finestra: int) -> dict:
    pe, mi = posizioni_estreme(r, quota)
    d_pm = distanza_vicino(pe, mi)
    d_mp = distanza_vicino(mi, pe)
    return {"mediana_peggiori_migliori": float(np.median(d_pm)),
            "quota_peggiori_con_migliore": float(np.mean(d_pm <= finestra)),
            "quota_migliori_con_peggiore": float(np.mean(d_mp <= finestra)),
            "n_estremi": int(len(pe))}


def quota_anni_top(r: np.ndarray, anni: np.ndarray, quota: float, n_top: int) -> float:
    """Quota dei giorni estremi (migliori e peggiori) che cade nei n_top anni con più giorni estremi."""
    pe, mi = posizioni_estreme(r, quota)
    tutti = np.concatenate([pe, mi])
    conti = np.bincount(anni[tutti] - anni.min())
    return float(np.sort(conti)[::-1][:n_top].sum() / conti.sum())


def vol_ewma_ieri(r: np.ndarray, lam: float, rodaggio: int) -> np.ndarray:
    """sigma[t] = volatilità EWMA stimata con i rendimenti fino a t-1. Le prime `rodaggio` sedute sono usate per innescarla."""
    s2 = np.empty(len(r))
    s2[0] = np.var(r[:rodaggio])
    for t in range(1, len(r)):
        s2[t] = lam * s2[t - 1] + (1 - lam) * r[t - 1] ** 2
    return np.sqrt(s2)


def vol_mobile_ieri(r: np.ndarray, finestra: int) -> np.ndarray:
    """Deviazione standard degli ultimi `finestra` rendimenti fino a t-1 (NaN se non ci sono abbastanza sedute)."""
    return pd.Series(r).rolling(finestra).std().shift(1).to_numpy()


def quote_per_quintile(vol: np.ndarray, posizioni: np.ndarray) -> np.ndarray:
    """Quota delle posizioni date che cade in ciascun quinto (0 = volatilità più bassa .. 4 = più alta) delle sedute con vol valida."""
    valide = ~np.isnan(vol)
    soglie = np.quantile(vol[valide], [0.2, 0.4, 0.6, 0.8])
    p = posizioni[valide[posizioni]]
    q = np.searchsorted(soglie, vol[p], side="right")
    return np.bincount(q, minlength=5) / len(p)


def segnale_filtro(r: np.ndarray, finestra: int, percentile: float, storia_minima: int) -> np.ndarray:
    """True = in liquidità alla seduta t. La soglia è il percentile della volatilità osservata fino a t-1 (storia espandente)."""
    vol = vol_mobile_ieri(r, finestra)
    liq = np.zeros(len(r), dtype=bool)
    storia: list[float] = []
    for t in range(len(r)):
        if t > finestra and not np.isnan(vol[t - 1]):
            bisect.insort(storia, vol[t - 1])
        if t >= storia_minima and not np.isnan(vol[t]) and len(storia) > 20:
            soglia = storia[int(np.floor(percentile * (len(storia) - 1)))]
            liq[t] = vol[t] > soglia
    return liq


def rendimenti_filtro(r: np.ndarray, liq: np.ndarray, costo: float) -> np.ndarray:
    """Rendimento giornaliero della strategia: 0 in liquidità, r altrimenti; il costo si paga a ogni cambio di stato."""
    out = np.where(liq, 0.0, r)
    cambi = np.r_[False, liq[1:] != liq[:-1]]
    return out - costo * cambi


def cagr(r: np.ndarray, anni: float) -> float:
    return float(np.exp(np.sum(np.log1p(r)) / anni) - 1.0)


def cagr_scimmie(r: np.ndarray, n_fuori: int, anni: float, n: int, rng) -> np.ndarray:
    """Scimmie che stanno in liquidità per n_fuori sedute scelte a caso (stesso periodo): rendimento annuo composto di ciascuna."""
    lr = np.log1p(r)
    tot = lr.sum()
    out = np.empty(n)
    for k in range(n):
        fuori = rng.choice(len(r), n_fuori, replace=False)
        out[k] = np.exp((tot - lr[fuori].sum()) / anni) - 1.0
    return out


def holm(p: dict) -> dict:
    ordine = sorted(p, key=p.get)
    m = len(ordine)
    out, massimo = {}, 0.0
    for k, nome in enumerate(ordine):
        massimo = max(massimo, min(1.0, (m - k) * p[nome]))
        out[nome] = massimo
    return out
