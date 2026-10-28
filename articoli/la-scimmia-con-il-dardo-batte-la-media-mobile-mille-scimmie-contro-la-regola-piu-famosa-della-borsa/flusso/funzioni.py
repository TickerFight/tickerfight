"""Funzioni dell'esperimento (media mobile contro scimmie), separate dal flusso per controllarle su dati inventati."""
import numpy as np
import pandas as pd

import config


def posizione_sma(close: pd.Series, n: int) -> np.ndarray:
    """1 se la chiusura di IERI è sopra la sua media a n sedute (calcolata con dati fino a ieri), altrimenti 0."""
    sma = close.rolling(n).mean()
    seg = (close > sma) & sma.notna()
    return seg.shift(1, fill_value=False).astype(np.int8).to_numpy()


def metriche(rend: np.ndarray, pos: np.ndarray, costo: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """rend: (T,) rendimenti dell'indice; pos: (M,T) posizioni 0/1. Si parte da liquidità: il primo acquisto costa.
    Restituisce (cagr, sharpe, perdita massima) per ognuna delle M righe."""
    pos = np.atleast_2d(pos)
    prima = np.concatenate([np.zeros((pos.shape[0], 1), dtype=pos.dtype), pos[:, :-1]], axis=1)
    cambi = np.abs(pos.astype(np.int8) - prima.astype(np.int8))
    r = pos * rend[None, :] - costo * cambi
    anni = r.shape[1] / config.SEDUTE_ANNO
    logv = np.log1p(r)
    cagr = np.exp(logv.sum(axis=1) / anni) - 1.0
    sd = r.std(axis=1, ddof=1)
    sharpe = np.where(sd > 0, r.mean(axis=1) / np.where(sd > 0, sd, 1) * np.sqrt(config.SEDUTE_ANNO), 0.0)
    v = np.cumprod(1.0 + r, axis=1)
    mdd = (v / np.maximum.accumulate(v, axis=1) - 1.0).min(axis=1)
    return cagr, sharpe, mdd


def blocchi(pos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Valori (0/1) e lunghezze dei periodi consecutivi di una posizione."""
    cambi = np.flatnonzero(np.diff(pos) != 0) + 1
    inizi = np.concatenate([[0], cambi])
    lung = np.diff(np.concatenate([inizi, [len(pos)]]))
    return pos[inizi], lung


def scimmia_a_blocchi(valori: np.ndarray, lung: np.ndarray, rng) -> np.ndarray:
    """Stessa alternanza dentro/fuori della regola, stesse durate ma rimescolate tra i periodi dello stesso tipo:
    stessa quota di tempo investito e stesso numero di operazioni."""
    nuove = lung.copy()
    for v in (0, 1):
        idx = np.flatnonzero(valori == v)
        nuove[idx] = lung[idx][rng.permutation(len(idx))]
    return np.repeat(valori, nuove).astype(np.int8)


def scimmie_a_moneta(T: int, quota: float, m: int, rng) -> np.ndarray:
    return (rng.random((m, T)) < quota).astype(np.int8)


def percentile_e_p(valore: float, scimmie: np.ndarray, migliore_se_alto: bool = True) -> tuple[float, float]:
    """Quota di scimmie che la regola batte (o pareggia) e p unilaterale (1 + scimmie migliori o uguali)/(M + 1).
    Per la perdita massima (negativa) più alto = meno profonda = migliore, quindi vale la stessa convenzione."""
    m = len(scimmie)
    batte = float((scimmie <= valore).mean())
    p = (1 + int((scimmie >= valore).sum())) / (m + 1)
    return batte, p


def holm(p: dict) -> dict:
    ordine = sorted(p, key=p.get)
    out, mx, k = {}, 0.0, len(ordine)
    for i, nome in enumerate(ordine):
        mx = max(mx, min(1.0, (k - i) * p[nome]))
        out[nome] = mx
    return out
