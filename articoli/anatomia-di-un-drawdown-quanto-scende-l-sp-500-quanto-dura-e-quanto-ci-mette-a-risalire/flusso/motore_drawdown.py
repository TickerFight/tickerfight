"""Calcolo dei drawdown: serie sott'acqua ed episodi (dal massimo storico al recupero)."""
import numpy as np


def serie_drawdown(close: np.ndarray) -> np.ndarray:
    """Drawdown a ogni seduta: chiusura / massimo storico fino a quel giorno - 1 (<= 0)."""
    picco = np.maximum.accumulate(close)
    return close / picco - 1.0


def episodi(close: np.ndarray, soglia: float = 0.0) -> list[dict]:
    """Elenco degli episodi con profondità >= soglia.

    Ogni episodio: i_picco (ultimo massimo prima della discesa), i_minimo, i_recupero (primo giorno con chiusura >= picco,
    None se l'episodio è ancora aperto), profondita (positiva). Gli indici sono posizioni nell'array.
    """
    out = []
    picco = close[0]
    i_picco = 0
    minimo = picco
    i_minimo = 0
    sotto = False
    for i in range(1, len(close)):
        c = close[i]
        if c >= picco:
            if sotto:
                prof = 1.0 - minimo / picco
                if prof >= soglia:
                    out.append({"i_picco": i_picco, "i_minimo": i_minimo, "i_recupero": i, "profondita": prof})
            picco, i_picco, minimo, i_minimo, sotto = c, i, c, i, False
        else:
            if not sotto:
                sotto = True
                minimo, i_minimo = c, i
            elif c < minimo:
                minimo, i_minimo = c, i
    if sotto:
        prof = 1.0 - minimo / picco
        if prof >= soglia:
            out.append({"i_picco": i_picco, "i_minimo": i_minimo, "i_recupero": None, "profondita": prof})
    return out


def rango_spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx = np.argsort(np.argsort(x, kind="stable"), kind="stable").astype(float)
    ry = np.argsort(np.argsort(y, kind="stable"), kind="stable").astype(float)
    # gestione dei pari: media dei ranghi
    def medi(v, r):
        for val in np.unique(v):
            m = v == val
            if m.sum() > 1:
                r[m] = r[m].mean()
        return r
    rx, ry = medi(x, rx), medi(y, ry)
    return float(np.corrcoef(rx, ry)[0, 1])
