"""Funzioni dell'articolo 301: test ADF, finestre, simulazioni."""
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller


def log_rendimenti(close: pd.Series) -> pd.Series:
    return np.log(close).diff().dropna()


def adf(x, regressione: str, maxlag: int, autolag="AIC") -> tuple[float, float, int]:
    """Restituisce statistica, p-value e ritardi usati."""
    r = adfuller(np.asarray(x, float), maxlag=maxlag, regression=regressione, autolag=autolag, result_object=False)
    return float(r[0]), float(r[1]), int(r[2])


def finestre(n: int, ampiezza: int) -> list[tuple[int, int]]:
    """Finestre consecutive non sovrapposte; l'ultima parte incompleta è scartata."""
    return [(a, a + ampiezza) for a in range(0, n - ampiezza + 1, ampiezza)]


def random_walk(rng, n: int, sigma: float, mu: float = 0.0) -> np.ndarray:
    return np.cumsum(rng.normal(mu, sigma, n))


def ar1(rng, n: int, phi: float, sigma: float) -> np.ndarray:
    """AR(1) stazionario (media zero), partendo dalla distribuzione stazionaria."""
    e = rng.normal(0.0, sigma, n)
    x = np.empty(n)
    x[0] = rng.normal(0.0, sigma / np.sqrt(1 - phi ** 2))
    for t in range(1, n):
        x[t] = phi * x[t - 1] + e[t]
    return x
