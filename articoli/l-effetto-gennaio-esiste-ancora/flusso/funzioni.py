"""Funzioni di calcolo dell'articolo 162: rendimenti mensili e test di permutazione."""
import numpy as np
import pandas as pd


def rendimenti_mensili(close: pd.Series) -> pd.Series:
    """Rendimento semplice da fine mese a fine mese. Il primo mese (incompleto) è perso. Indice: Period mensile."""
    m = close.groupby(close.index.to_period("M")).last()
    return m.pct_change().dropna()


def permutazione_differenza(x: np.ndarray, etichetta: np.ndarray, n: int, rng: np.random.Generator) -> tuple[float, float]:
    """Differenza tra la media dei rendimenti con etichetta vera e quella degli altri; p-value bilaterale per permutazione delle etichette
    (con +1 al numeratore e al denominatore)."""
    x = np.asarray(x, float)
    e = np.asarray(etichetta, bool)
    oss = x[e].mean() - x[~e].mean()
    k = int(e.sum())
    cont = 0
    for _ in range(n):
        idx = rng.permutation(len(x))[:k]
        m = np.zeros(len(x), bool)
        m[idx] = True
        if abs(x[m].mean() - x[~m].mean()) >= abs(oss):
            cont += 1
    return float(oss), float((1 + cont) / (n + 1))


def resto_anno(rend_mensili: pd.Series) -> pd.DataFrame:
    """Per ogni anno completo: rendimento di gennaio e rendimento composto da febbraio a dicembre."""
    righe = []
    for anno, g in rend_mensili.groupby(rend_mensili.index.year):
        if len(g) == 12 and g.index[0].month == 1:
            righe.append({"anno": anno, "gennaio": g.iloc[0], "resto": float(np.prod(1 + g.iloc[1:].to_numpy()) - 1)})
    return pd.DataFrame(righe)
