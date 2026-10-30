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


def minimo_permutazione(x: np.ndarray, mese: np.ndarray, n: int, rng: np.random.Generator) -> tuple[float, float]:
    """Media più bassa tra i dodici mesi di calendario: valore osservato e p-value per permutazione dei rendimenti tra i mesi
    (quota di permutazioni con un minimo almeno così basso, con +1). Misura quanto è raro il «peggiore dei dodici», non di un mese scelto prima."""
    x = np.asarray(x, float)
    mese = np.asarray(mese, int)
    conta = np.bincount(mese, minlength=13)[1:]
    oss = (np.bincount(mese, weights=x, minlength=13)[1:] / conta).min()
    cont = 0
    for _ in range(n):
        xp = rng.permutation(x)
        m = (np.bincount(mese, weights=xp, minlength=13)[1:] / conta).min()
        if m <= oss:
            cont += 1
    return float(oss), float((1 + cont) / (n + 1))
