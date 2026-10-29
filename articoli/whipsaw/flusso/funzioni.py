"""Funzioni dell'articolo 134: filtro sotto la media mobile, banda, cambi di posizione, episodi di uscita."""
import numpy as np
import pandas as pd


def media_mobile(close: np.ndarray, lung: int) -> np.ndarray:
    return pd.Series(np.asarray(close, dtype=float)).rolling(lung).mean().to_numpy()


def posizione_semplice(close: np.ndarray, sma: np.ndarray) -> np.ndarray:
    """1 = investito, 0 = in liquidità, deciso alla chiusura t (sopra la media: investito)."""
    return (np.asarray(close) >= np.asarray(sma)).astype(int)


def posizione_banda(close: np.ndarray, sma: np.ndarray, banda: float) -> np.ndarray:
    """Con banda: esce se la chiusura scende sotto media*(1-banda), rientra se sale sopra media*(1+banda); nel mezzo resta com'è."""
    close, sma = np.asarray(close, dtype=float), np.asarray(sma, dtype=float)
    pos = np.empty(len(close), dtype=int)
    stato = 1 if close[0] >= sma[0] else 0
    for t in range(len(close)):
        if stato == 1 and close[t] < sma[t] * (1 - banda):
            stato = 0
        elif stato == 0 and close[t] > sma[t] * (1 + banda):
            stato = 1
        pos[t] = stato
    return pos


def cambi(pos: np.ndarray) -> np.ndarray:
    """Posizioni t >= 1 in cui la posizione differisce da quella di t-1."""
    p = np.asarray(pos)
    return np.flatnonzero(p[1:] != p[:-1]) + 1


def episodi(pos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Uscite complete: (posizione di uscita, posizione di rientro). Un'uscita ancora aperta alla fine non è inclusa."""
    p = np.asarray(pos)
    c = cambi(p)
    usc = [t for t in c if p[t] == 0]
    rie = [t for t in c if p[t] == 1]
    out_u, out_r = [], []
    for u in usc:
        dopo = [t for t in rie if t > u]
        if not dopo:
            break
        out_u.append(u)
        out_r.append(dopo[0])
    return np.array(out_u, dtype=int), np.array(out_r, dtype=int)


def log_strategia(lr: np.ndarray, pos: np.ndarray, costo: float) -> float:
    """Somma dei log-rendimenti della strategia: lr[t] (da t a t+1) conta se pos[t] = 1; ogni cambio costa ln(1-costo)."""
    lr, pos = np.asarray(lr), np.asarray(pos)
    return float((lr * pos).sum() + len(cambi(pos)) * np.log(1 - costo))


def cagr_da_log(somma_log: float, anni: float) -> float:
    return float(np.exp(somma_log / anni) - 1.0)
