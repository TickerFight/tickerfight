"""Funzioni dell'articolo 302: autocorrelazione, autocorrelazione parziale, test di Ljung-Box, Holm, finestre."""
import math

import numpy as np
import pandas as pd
from scipy.stats import chi2


def log_rendimenti(close: pd.Series) -> pd.Series:
    return np.log(close).diff().dropna()


def acf(x, nlags: int) -> np.ndarray:
    """Autocorrelazione campionaria ai ritardi 0..nlags (stimatore consueto, con la varianza totale al denominatore)."""
    d = np.asarray(x, float)
    d = d - d.mean()
    ss = float(d @ d)
    return np.array([1.0] + [float(d[k:] @ d[:-k]) / ss for k in range(1, nlags + 1)])


def pacf_da_acf(rho: np.ndarray) -> np.ndarray:
    """Autocorrelazione parziale ai ritardi 0..m con la ricorsione di Durbin-Levinson, a partire da rho[0..m]."""
    m = len(rho) - 1
    phi = np.zeros((m + 1, m + 1))
    out = np.zeros(m + 1)
    out[0] = 1.0
    if m >= 1:
        phi[1, 1] = rho[1]
        out[1] = rho[1]
    for k in range(2, m + 1):
        num = rho[k] - sum(phi[k - 1, j] * rho[k - j] for j in range(1, k))
        den = 1.0 - sum(phi[k - 1, j] * rho[j] for j in range(1, k))
        phi[k, k] = num / den
        for j in range(1, k):
            phi[k, j] = phi[k - 1, j] - phi[k, k] * phi[k - 1, k - j]
        out[k] = phi[k, k]
    return out


def p_normale(z: float) -> float:
    """P-value a due code di una statistica normale standard."""
    return math.erfc(abs(z) / math.sqrt(2))


def ljung_box(rho: np.ndarray, n: int, h: int) -> tuple[float, float]:
    """Statistica Q e p-value del test di Ljung-Box sui primi h ritardi (ipotesi nulla: nessuna autocorrelazione)."""
    q = n * (n + 2) * sum(rho[k] ** 2 / (n - k) for k in range(1, h + 1))
    return float(q), float(chi2.sf(q, h))


def holm(p) -> np.ndarray:
    """P-value corretti con il metodo di Holm."""
    p = np.asarray(p, float)
    m = len(p)
    adj = np.empty(m)
    corrente = 0.0
    for rango, i in enumerate(np.argsort(p)):
        corrente = max(corrente, (m - rango) * p[i])
        adj[i] = min(1.0, corrente)
    return adj


def finestre(n: int, ampiezza: int) -> list[tuple[int, int]]:
    """Finestre consecutive non sovrapposte; l'ultima parte incompleta è scartata."""
    return [(a, a + ampiezza) for a in range(0, n - ampiezza + 1, ampiezza)]


def ar1(rng, n: int, phi: float, sigma: float) -> np.ndarray:
    """AR(1) stazionario (media zero), partendo dalla distribuzione stazionaria."""
    e = rng.normal(0.0, sigma, n)
    x = np.empty(n)
    x[0] = rng.normal(0.0, sigma / np.sqrt(1 - phi ** 2))
    for t in range(1, n):
        x[t] = phi * x[t - 1] + e[t]
    return x
