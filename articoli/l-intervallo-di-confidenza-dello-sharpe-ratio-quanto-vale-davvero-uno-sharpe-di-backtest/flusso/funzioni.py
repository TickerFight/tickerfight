"""Funzioni dell'articolo 82: Sharpe, errori standard (Lo, Mertens), bootstrap, copertura onesta, anni necessari, regola a media mobile."""
import math

import numpy as np
import pandas as pd


def sharpe(x: np.ndarray, ga: int) -> float:
    x = np.asarray(x, dtype=float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(ga))


def se_lo(x: np.ndarray, ga: int) -> float:
    """Errore standard annualizzato dello Sharpe con rendimenti indipendenti e normali (Lo, 2002): radice di (1 + SR^2 / 2) / n, per SR del periodo."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    sr = x.mean() / x.std(ddof=1)
    return float(math.sqrt(ga) * math.sqrt((1.0 + 0.5 * sr * sr) / n))


def se_mertens(x: np.ndarray, ga: int) -> float:
    """Come se_lo ma con asimmetria g3 e curtosi g4 (non in eccesso): radice di (1 - g3 SR + (g4 - 1) SR^2 / 4) / n (Mertens, 2002)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    sd = x.std(ddof=1)
    sr = x.mean() / sd
    z = (x - x.mean()) / x.std(ddof=0)
    g3, g4 = float(np.mean(z ** 3)), float(np.mean(z ** 4))
    return float(math.sqrt(ga) * math.sqrt((1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr * sr) / n))


def intervallo(sr: float, se: float, z: float) -> tuple[float, float]:
    return sr - z * se, sr + z * se


def bootstrap_sharpe(x: np.ndarray, n_boot: int, blocco: int, ga: int, livello: float, rng) -> tuple[float, float]:
    """Intervallo percentile dello Sharpe annualizzato. blocco = 1: bootstrap sui giorni; blocco > 1: blocchi circolari."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    nb = int(np.ceil(n / blocco))
    salti = np.arange(blocco)[None, :]
    s = np.empty(n_boot)
    for i in range(n_boot):
        if blocco == 1:
            y = x[rng.integers(0, n, n)]
        else:
            y = x[((rng.integers(0, n, nb)[:, None] + salti) % n).ravel()[:n]]
        s[i] = y.mean() / y.std(ddof=1) * math.sqrt(ga)
    lo, hi = np.quantile(s, [(1 - livello) / 2, 1 - (1 - livello) / 2])
    return float(lo), float(hi)


def copertura_fuori(x: np.ndarray, lung: int, inizi: np.ndarray, ga: int, z: float) -> tuple[float, int]:
    """Per ogni finestra di `lung` sedute: l'intervallo (Lo) dello Sharpe della finestra, allargato per l'incertezza del riferimento, contiene lo Sharpe di tutte le ALTRE sedute?"""
    x = np.asarray(x, dtype=float)
    n = len(x)
    inizi = np.asarray(inizi)
    inizi = inizi[inizi + lung <= n]
    c1 = np.concatenate([[0.0], np.cumsum(x)])
    c2 = np.concatenate([[0.0], np.cumsum(x * x)])
    s1, s2 = c1[inizi + lung] - c1[inizi], c2[inizi + lung] - c2[inizi]
    mw = s1 / lung
    sdw = np.sqrt((s2 - lung * mw ** 2) / (lung - 1))
    r1, r2, nr = c1[-1] - s1, c2[-1] - s2, n - lung
    mr = r1 / nr
    sdr = np.sqrt((r2 - nr * mr ** 2) / (nr - 1))
    srw, srr = mw / sdw, mr / sdr
    sew = np.sqrt(ga) * np.sqrt((1 + 0.5 * srw ** 2) / lung)
    ser = np.sqrt(ga) * np.sqrt((1 + 0.5 * srr ** 2) / nr)
    diff = (srw - srr) * math.sqrt(ga)
    return float(np.mean(np.abs(diff) <= z * np.sqrt(sew ** 2 + ser ** 2))), int(len(inizi))


def anni_necessari(sr_annuo: float, semiampiezza: float, z: float, ga: int) -> float:
    """Anni di dati perché la semiampiezza dell'intervallo di Lo dello Sharpe annualizzato scenda a `semiampiezza`: z^2 (1 + SR_giorno^2 / 2) / h^2."""
    sr_d = sr_annuo / math.sqrt(ga)
    return float(z * z * (1.0 + 0.5 * sr_d * sr_d) / (semiampiezza ** 2))


def regola_sma(c: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Rendimenti semplici giornalieri della regola «investito se la chiusura di ieri è sopra la media di n chiusure fino a ieri incluso, altrimenti fermo»
    e del buy & hold, per le sedute t = n + 1 .. fine (stesse date)."""
    c = np.asarray(c, dtype=float)
    cs = np.concatenate([[0.0], np.cumsum(c)])
    t = np.arange(n + 1, len(c))
    ieri = t - 1
    sma = (cs[ieri + 1] - cs[ieri + 1 - n]) / n
    pos = (c[ieri] > sma).astype(float)
    r = c[t] / c[t - 1] - 1.0
    return pos * r, r


def differenza_sharpe_bootstrap(xa: np.ndarray, xb: np.ndarray, n_boot: int, blocco: int, ga: int, livello: float, rng) -> tuple[float, float]:
    """Intervallo percentile della differenza di Sharpe (a - b) ricampionando a blocchi le stesse date per entrambe le serie."""
    xa, xb = np.asarray(xa, dtype=float), np.asarray(xb, dtype=float)
    n = len(xa)
    nb = int(np.ceil(n / blocco))
    salti = np.arange(blocco)[None, :]
    d = np.empty(n_boot)
    for i in range(n_boot):
        idx = ((rng.integers(0, n, nb)[:, None] + salti) % n).ravel()[:n]
        a, b = xa[idx], xb[idx]
        d[i] = (a.mean() / a.std(ddof=1) - b.mean() / b.std(ddof=1)) * math.sqrt(ga)
    lo, hi = np.quantile(d, [(1 - livello) / 2, 1 - (1 - livello) / 2])
    return float(lo), float(hi)


def inizi_mese(date: pd.DatetimeIndex) -> np.ndarray:
    s = pd.Series(np.arange(len(date)), index=date)
    return s.groupby([date.year, date.month]).first().to_numpy()
