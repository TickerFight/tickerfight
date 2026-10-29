"""Funzioni dell'articolo 81: Sharpe su finestre mobili, simulazione esatta dello Sharpe campionario."""
import numpy as np
import pandas as pd


def sharpe_finestre(r: np.ndarray, inizi: np.ndarray, lung: int, ga: int) -> np.ndarray:
    """Sharpe annuo (tasso zero) di r[i:i+lung] per ogni i in `inizi`; usa somme cumulate (media e deviazione standard campionaria)."""
    r = np.asarray(r, dtype=float)
    c1 = np.concatenate([[0.0], np.cumsum(r)])
    c2 = np.concatenate([[0.0], np.cumsum(r * r)])
    i = np.asarray(inizi)
    s1 = c1[i + lung] - c1[i]
    s2 = c2[i + lung] - c2[i]
    media = s1 / lung
    var = (s2 - lung * media ** 2) / (lung - 1)
    return media / np.sqrt(var) * np.sqrt(ga)


def sharpe_simulato(anni: float, sharpe_vero: float, ga: int, n: int, rng) -> np.ndarray:
    """n Sharpe campionari (annui) di backtest di `anni` anni su rendimenti normali indipendenti con Sharpe vero `sharpe_vero`.

    Per dati normali la media campionaria è normale e la varianza campionaria è chi quadro, indipendenti: si estraggono direttamente."""
    k = int(round(anni * ga))
    mu = sharpe_vero / ga                 # media giornaliera con deviazione standard giornaliera = 1/sqrt(ga) (volatilità annua 1)
    sd = 1.0 / np.sqrt(ga)
    media = mu + sd / np.sqrt(k) * rng.standard_normal(n)
    s = sd * np.sqrt(rng.chisquare(k - 1, size=n) / (k - 1))
    return media / s * np.sqrt(ga)


def inizi_mese(date: pd.DatetimeIndex) -> np.ndarray:
    """Posizioni della prima seduta di ogni mese."""
    s = pd.Series(np.arange(len(date)), index=date)
    return s.groupby([date.year, date.month]).first().to_numpy()
