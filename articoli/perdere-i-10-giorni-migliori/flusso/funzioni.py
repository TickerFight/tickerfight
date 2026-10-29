"""Funzioni dell'articolo 326: rendimento composto saltando giorni, finestre mobili, regime sotto la media a 200 sedute."""
import numpy as np
import pandas as pd


def cagr_da_log(somma_log: float, anni: float) -> float:
    """Rendimento annuo composto da una somma di logaritmi di (1 + r) su `anni` anni."""
    return float(np.exp(somma_log / anni) - 1.0)


def indici_estremi(r: np.ndarray, n: int, migliori: bool) -> np.ndarray:
    """Posizioni degli n rendimenti più alti (migliori=True) o più bassi, in ordine dal più estremo; a parità vince la data più antica."""
    r = np.asarray(r, dtype=float)
    ordine = np.argsort(-r if migliori else r, kind="stable")
    return ordine[:n]


def perdita_finestre(lr: np.ndarray, inizi: np.ndarray, lung: int, n: int, anni: float) -> tuple[np.ndarray, np.ndarray]:
    """Per ogni finestra [i, i+lung): (rendimento annuo composto del buy & hold, rendimento saltando gli n giorni migliori della finestra)."""
    lr = np.asarray(lr, dtype=float)
    bh = np.empty(len(inizi))
    sal = np.empty(len(inizi))
    for k, i in enumerate(inizi):
        w = lr[i:i + lung]
        tot = w.sum()
        top = np.partition(w, -n)[-n:].sum()
        bh[k] = cagr_da_log(tot, anni)
        sal[k] = cagr_da_log(tot - top, anni)
    return bh, sal


def sotto_media(close: np.ndarray, lung: int) -> np.ndarray:
    """Per ogni rendimento (dal secondo prezzo in poi): True se alla chiusura PRECEDENTE l'indice era sotto la media delle ultime `lung` chiusure
    (inclusa quella). Dove la media non è ancora calcolabile vale False (si resta investiti)."""
    c = pd.Series(np.asarray(close, dtype=float))
    sma = c.rolling(lung).mean()
    sotto = (c < sma).to_numpy()          # sotto[t]: chiusura t sotto la media che termina in t (False se NaN)
    return sotto[:-1]                     # il rendimento t -> t+1 usa il segnale della chiusura t


def vicino_a(posizioni: np.ndarray, riferimenti: np.ndarray, distanza: int) -> np.ndarray:
    """Per ogni posizione: True se almeno un riferimento dista al massimo `distanza` sedute (la posizione stessa esclusa)."""
    out = []
    for p in posizioni:
        d = np.abs(np.asarray(riferimenti) - p)
        out.append(bool(((d > 0) & (d <= distanza)).any()))
    return np.array(out)


def inizi_mese(date: pd.DatetimeIndex) -> np.ndarray:
    """Posizioni della prima seduta di ogni mese."""
    s = pd.Series(np.arange(len(date)), index=date)
    return s.groupby([date.year, date.month]).first().to_numpy()
