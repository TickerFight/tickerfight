"""Funzioni di calcolo dell'articolo 122: regola a media mobile, metriche, drawdown."""
import numpy as np
import pandas as pd


def posizione_sma(close: np.ndarray, n: int) -> np.ndarray:
    """1 se la chiusura è sopra la media semplice delle ultime n chiusure (inclusa quella di oggi), 0 altrimenti; nan nei primi n-1 giorni."""
    c = pd.Series(close, dtype=float)
    m = c.rolling(n).mean()
    pos = (c > m).astype(float).to_numpy().copy()
    pos[np.isnan(m.to_numpy())] = np.nan
    return pos


def rendimenti_regola(close: np.ndarray, pos: np.ndarray, costo: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rendimenti giornalieri semplici della regola e del buy & hold sugli stessi giorni, e posizioni effettive.
    La posizione decisa alla chiusura di t-1 vale per il rendimento di t; a ogni cambio di posizione si paga `costo`.
    I giorni senza segnale (prime n-1 sedute e il primo giorno dopo) sono scartati."""
    c = np.asarray(close, float)
    r = c[1:] / c[:-1] - 1.0
    p = pos[:-1]
    ok = ~np.isnan(p)
    r, p = r[ok], p[ok]
    cambi = np.abs(np.diff(np.concatenate([[p[0]], p])))
    return p * r - costo * cambi, r, p


def cagr(x: np.ndarray, ga: int) -> float:
    return float(np.exp(np.mean(np.log1p(x)) * ga) - 1.0)


def sharpe(x: np.ndarray, ga: int) -> float:
    s = np.std(x, ddof=1)
    return float(np.mean(x) / s * np.sqrt(ga)) if s > 0 else float("nan")


def max_drawdown(x: np.ndarray) -> float:
    """Massima perdita dal massimo precedente della curva dei rendimenti composti (negativa)."""
    eq = np.cumprod(1.0 + np.asarray(x, float))
    picco = np.maximum.accumulate(eq)
    return float((eq / picco - 1.0).min())


def n_cambi(p: np.ndarray) -> int:
    return int(np.sum(np.abs(np.diff(p)) > 0))
