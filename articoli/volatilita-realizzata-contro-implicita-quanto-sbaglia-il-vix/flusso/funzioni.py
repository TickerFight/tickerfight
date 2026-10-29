"""Funzioni dell'articolo 245: volatilità realizzata, premio, regressione e R quadro."""
import numpy as np
import pandas as pd


def vol_realizzata_passata(lr: np.ndarray, n: int, ga: int) -> np.ndarray:
    """Volatilità annua in punti delle n sedute che finiscono in t (usa solo dati fino a t). NaN fino a n-1."""
    return pd.Series(lr).rolling(n).std(ddof=1).to_numpy() * np.sqrt(ga) * 100.0


def vol_realizzata_futura(lr: np.ndarray, n: int, ga: int) -> np.ndarray:
    """Volatilità annua in punti delle n sedute successive a t (t+1 .. t+n). NaN per le ultime n posizioni."""
    return np.concatenate([vol_realizzata_passata(lr, n, ga)[n:], np.full(n, np.nan)])


def regressione(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Minimi quadrati y = a + b x. Restituisce (a, b, R quadro)."""
    b, a = np.polyfit(x, y, 1)
    pred = a + b * x
    r2 = 1.0 - np.sum((y - pred) ** 2) / np.sum((y - np.mean(y)) ** 2)
    return float(a), float(b), float(r2)
