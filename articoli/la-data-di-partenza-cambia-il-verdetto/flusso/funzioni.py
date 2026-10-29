"""Funzioni dell'articolo 13: filtro di tendenza a 200 sedute, metriche su finestre che partono da ogni mese."""
import numpy as np
import pandas as pd


def rendimenti_regola(close: np.ndarray, media: int, costo: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rendimenti giornalieri della regola, del buy & hold e posizione.

    Il giorno k ha il rendimento close[k]/close[k-1]-1. La posizione del giorno k è il segnale osservato alla chiusura k-2 (chiusura sopra la media
    mobile delle ultime `media` chiusure), eseguito alla chiusura k-1. Ogni cambio di posizione costa `costo` (frazione), sottratto al rendimento del giorno k.
    Gli indici 0 e 1 non hanno posizione (zero) e vanno scartati da chi usa la serie."""
    close = np.asarray(close, dtype=float)
    n = len(close)
    ret = np.zeros(n)
    ret[1:] = close[1:] / close[:-1] - 1.0
    sma = np.full(n, np.nan)
    cs = np.cumsum(np.insert(close, 0, 0.0))
    sma[media - 1:] = (cs[media:] - cs[:-media]) / media
    sig = np.zeros(n)
    ok = ~np.isnan(sma)
    sig[ok] = (close[ok] > sma[ok]).astype(float)
    pos = np.zeros(n)
    pos[2:] = sig[:-2]
    cambi = np.zeros(n)
    cambi[1:] = np.abs(pos[1:] - pos[:-1])
    strat = pos * ret - costo * cambi
    return strat, ret, pos


def metriche_finestra(r: np.ndarray, ga: int) -> tuple[float, float, float]:
    """(rendimento annuo composto, Sharpe con tasso zero, perdita massima come numero positivo) di una serie di rendimenti giornalieri."""
    r = np.asarray(r, dtype=float)
    cagr = float(np.prod(1.0 + r) ** (ga / len(r)) - 1.0)
    sd = np.std(r, ddof=1)
    sharpe = float(np.mean(r) / sd * np.sqrt(ga)) if sd > 0 else 0.0
    e = np.cumprod(1.0 + r)
    picco = np.maximum.accumulate(np.concatenate([[1.0], e]))[1:]
    return cagr, sharpe, float(-np.min(e / picco - 1.0))


def inizi_mese(date: pd.DatetimeIndex, prima: int) -> np.ndarray:
    """Posizioni della prima seduta di ogni mese, a partire dalla posizione `prima`."""
    s = pd.Series(np.arange(len(date)), index=date)
    pos = s.groupby([date.year, date.month]).first().to_numpy()
    return pos[pos >= prima]
