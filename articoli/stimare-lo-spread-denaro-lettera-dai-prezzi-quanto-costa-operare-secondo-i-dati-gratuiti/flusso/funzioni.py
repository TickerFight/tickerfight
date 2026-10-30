"""Funzioni di calcolo dell'articolo 103: stimatori dello spread dai prezzi."""
import numpy as np
import pandas as pd

K = 3.0 - 2.0 * np.sqrt(2.0)


def cs_grezzo(h: np.ndarray, l: np.ndarray) -> np.ndarray:
    """Stima di Corwin-Schultz per ogni coppia di giorni consecutivi (t-1, t), assegnata al giorno t. Il primo elemento è nan.
    Può essere negativa. Spread in frazione del prezzo."""
    h, l = np.asarray(h, float), np.asarray(l, float)
    b1 = np.log(h / l) ** 2
    beta = b1[1:] + b1[:-1]
    hh = np.maximum(h[1:], h[:-1])
    ll = np.minimum(l[1:], l[:-1])
    gamma = np.log(hh / ll) ** 2
    alfa = (np.sqrt(2 * beta) - np.sqrt(beta)) / K - np.sqrt(gamma / K)
    s = 2 * (np.exp(alfa) - 1) / (1 + np.exp(alfa))
    return np.concatenate([[np.nan], s])


def roll_mensile(close: pd.Series) -> pd.Series:
    """Stimatore di Roll per mese: 2*sqrt(-cov(dp_t, dp_t-1)) / prezzo medio; nan se la covarianza è >= 0."""
    dp = close.diff()
    out = {}
    for mese, g in dp.groupby(close.index.to_period("M")):
        d = g.dropna().to_numpy()
        if len(d) < 10:
            continue
        cov = np.mean((d[1:] - d.mean()) * (d[:-1] - d.mean()))
        pm = close[close.index.to_period("M") == mese].mean()
        out[mese] = 2 * np.sqrt(-cov) / pm if cov < 0 else np.nan
    return pd.Series(out)


def media_mensile(serie: pd.Series) -> pd.Series:
    return serie.groupby(serie.index.to_period("M")).mean()


def vol_mensile(close: pd.Series) -> pd.Series:
    r = np.log(close).diff()
    return r.groupby(r.index.to_period("M")).std()
