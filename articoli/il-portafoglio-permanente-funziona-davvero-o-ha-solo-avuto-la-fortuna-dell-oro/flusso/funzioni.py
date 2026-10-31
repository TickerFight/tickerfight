"""Funzioni dell'esperimento: serie mensili, portafoglio ribilanciato a pesi fissi, statistiche, bootstrap.

Convenzioni: tutti i rendimenti sono mensili e semplici (0,01 = 1%).
"""
import numpy as np
import pandas as pd


def fine_mese(serie: pd.Series) -> pd.Series:
    """Ultimo valore di ogni mese (indice = periodo mensile)."""
    s = serie.sort_index()
    return s.groupby(s.index.to_period("M")).last()


def portafoglio(R: np.ndarray, mesi: pd.PeriodIndex, W) -> np.ndarray:
    """Rendimenti mensili di un portafoglio ribilanciato a ogni gennaio (e al primo mese).

    R: array (n_mesi, N) di rendimenti mensili degli N asset.
    W: pesi. Array (N,) = un portafoglio; (S, N) = S portafogli; (S, Y, N) = S portafogli con pesi diversi per ognuno degli Y anni solari.
    Restituisce un array (S, n_mesi).
    """
    anni = np.array([m.year for m in mesi])
    anni_u = list(dict.fromkeys(anni))
    W = np.asarray(W, float)
    if W.ndim == 1:
        W = W[None, None, :]
    elif W.ndim == 2:
        W = W[:, None, :]
    S = W.shape[0]
    out = np.empty((S, len(mesi)))
    v = None
    for i, m in enumerate(mesi):
        if i == 0 or m.month == 1:
            w = W[:, 0, :] if W.shape[1] == 1 else W[:, anni_u.index(m.year), :]
            v = w.copy()
        tot = v.sum(axis=1)
        v = v * (1.0 + R[i][None, :])
        out[:, i] = v.sum(axis=1) / tot - 1.0
    return out


def mesi_sott_acqua(r: np.ndarray) -> int:
    """Il periodo più lungo (in mesi) passato sotto il massimo precedente."""
    v = np.r_[1.0, np.cumprod(1.0 + r)]
    picco = np.maximum.accumulate(v)
    sotto = v < picco - 1e-12
    best = cur = 0
    for s in sotto:
        cur = cur + 1 if s else 0
        best = max(best, cur)
    return best


def cagr(r: np.ndarray) -> float:
    return float(np.prod(1.0 + r) ** (12.0 / len(r)) - 1.0)


def volatilita(r: np.ndarray) -> float:
    return float(np.std(r, ddof=1) * np.sqrt(12.0))


def sharpe(r: np.ndarray, cassa: np.ndarray, asse: int = -1):
    """Sharpe annualizzato sugli eccessi mensili rispetto alla liquidità."""
    e = r - cassa
    return e.mean(axis=asse) / e.std(axis=asse, ddof=1) * np.sqrt(12.0)


def perdita_massima(r: np.ndarray) -> float:
    """Massimo calo dal picco (numero negativo), sul valore cumulato dei rendimenti mensili."""
    v = np.cumprod(1.0 + np.r_[0.0, r][1:])
    v = np.r_[1.0, v]
    return float((v / np.maximum.accumulate(v) - 1.0).min())


def rendimenti_anno_solare(r: np.ndarray, mesi: pd.PeriodIndex) -> pd.Series:
    anni = np.array([m.year for m in mesi])
    return pd.Series(1.0 + r, index=anni).groupby(level=0).prod() - 1.0


def indici_blocchi(n: int, blocco: int, rng) -> np.ndarray:
    """Indici di un campione bootstrap a blocchi circolari lungo n."""
    k = int(np.ceil(n / blocco))
    inizi = rng.integers(0, n, k)
    return ((inizi[:, None] + np.arange(blocco)[None, :]) % n).ravel()[:n]
