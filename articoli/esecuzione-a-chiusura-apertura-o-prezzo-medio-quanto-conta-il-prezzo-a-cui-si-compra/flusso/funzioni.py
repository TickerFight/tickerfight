"""Funzioni dell'articolo 9: segnali da medie mobili, rendimenti di una regola per prezzo di esecuzione, costi, metriche, bootstrap a blocchi."""
import numpy as np


def sma(c: np.ndarray, n: int) -> np.ndarray:
    """Media mobile semplice delle ultime n chiusure (incluso oggi); NaN per i primi n-1 giorni."""
    c = np.asarray(c, dtype=float)
    out = np.full(len(c), np.nan)
    cs = np.concatenate([[0.0], np.cumsum(c)])
    out[n - 1:] = (cs[n:] - cs[:-n]) / n
    return out


def posizione(c: np.ndarray, n: int) -> np.ndarray:
    """Posizione decisa alla chiusura del giorno t: 1 se la chiusura è sopra la media di n giorni, 0 altrimenti; NaN finché la media non esiste."""
    m = sma(c, n)
    p = (np.asarray(c) > m).astype(float)
    p[np.isnan(m)] = np.nan
    return p


def log_rendimenti_regola(o, c, a, pos, modo: str, costo: float) -> np.ndarray:
    """Rendimenti logaritmici giornalieri per i giorni t = 1.. (indice relativo alle serie), dato il segnale `pos` deciso alla chiusura di ogni giorno.
    `modo` è il prezzo di esecuzione dell'ordine per il segnale del giorno t-1:
       'stessa_chiusura'  alla chiusura del giorno t-1 (quella con cui si calcola il segnale)
       'apertura'         all'apertura del giorno t
       'prezzo_medio'     al prezzo medio `a` del giorno t
       'chiusura_dopo'    alla chiusura del giorno t
    Il giorno t, la posizione precedente p0 = pos[t-2] vale fino al prezzo di esecuzione, la nuova p1 = pos[t-1] da lì alla chiusura del giorno t.
    Il costo `costo` (frazione) si paga a ogni cambio di posizione. Il primo valore valido è il giorno t in cui pos[t-2] esiste."""
    o, c, a = (np.asarray(v, dtype=float) for v in (o, c, a))
    pos = np.asarray(pos, dtype=float)
    n = len(c)
    out = np.full(n, np.nan)
    t = np.arange(2, n)
    p0, p1 = pos[t - 2], pos[t - 1]
    if modo == "stessa_chiusura":
        f = c[t - 1]
    elif modo == "apertura":
        f = o[t]
    elif modo == "prezzo_medio":
        f = a[t]
    elif modo == "chiusura_dopo":
        f = c[t]
    else:
        raise ValueError(modo)
    r = p0 * np.log(f / c[t - 1]) + p1 * np.log(c[t] / f)
    r = r + np.where(p0 != p1, np.log(1.0 - costo), 0.0)
    out[t] = r
    return out


def metriche(r: np.ndarray, ga: int) -> dict:
    """CAGR, volatilità, Sharpe (tasso zero) e perdita massima da rendimenti logaritmici giornalieri (senza NaN)."""
    r = np.asarray(r, dtype=float)
    e = np.exp(np.cumsum(r))
    picco = np.maximum.accumulate(np.concatenate([[1.0], e]))[1:]
    return {"cagr": float(np.exp(r.mean() * ga) - 1.0), "vol": float(r.std(ddof=1) * np.sqrt(ga)),
            "sharpe": float(r.mean() / r.std(ddof=1) * np.sqrt(ga)), "dd": float(np.min(e / picco - 1.0))}


def cambi(pos: np.ndarray) -> int:
    """Numero di cambi di posizione (acquisti più vendite) lungo la serie dei segnali, ignorando i NaN iniziali."""
    p = np.asarray(pos, dtype=float)
    p = p[~np.isnan(p)]
    return int(np.sum(p[1:] != p[:-1]))


def bootstrap_differenza(d: np.ndarray, n_boot: int, blocco: int, ga: int, livello: float, rng) -> tuple[float, float]:
    """Intervallo del rendimento logaritmico medio annualizzato di una serie di differenze giornaliere, con blocchi circolari."""
    d = np.asarray(d, dtype=float)
    n = len(d)
    nb = int(np.ceil(n / blocco))
    salti = np.arange(blocco)[None, :]
    m = np.empty(n_boot)
    for i in range(n_boot):
        idx = ((rng.integers(0, n, nb)[:, None] + salti) % n).ravel()[:n]
        m[i] = d[idx].mean()
    lo, hi = np.quantile(m, [(1 - livello) / 2, 1 - (1 - livello) / 2])
    return float(lo * ga), float(hi * ga)
