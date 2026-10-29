"""Funzioni dell'articolo 83: CAGR dai rendimenti logaritmici, intervalli (formula, bootstrap sui giorni, bootstrap a blocchi), copertura, anni necessari."""
import numpy as np
import pandas as pd


def cagr_da_media(media_giornaliera: float, ga: int) -> float:
    """CAGR dal rendimento logaritmico medio giornaliero."""
    return float(np.exp(media_giornaliera * ga) - 1.0)


def intervallo_formula(x: np.ndarray, ga: int, z: float) -> tuple[float, float, float]:
    """(cagr, estremo basso, estremo alto) con l'errore standard sigma / radice(n) della media dei rendimenti logaritmici."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    media, sd = x.mean(), x.std(ddof=1)
    se = sd / np.sqrt(n)
    return cagr_da_media(media, ga), cagr_da_media(media - z * se, ga), cagr_da_media(media + z * se, ga)


def bootstrap_giorni(x: np.ndarray, n_boot: int, ga: int, livello: float, rng) -> tuple[float, float]:
    """Intervallo percentile del CAGR pescando i rendimenti giornalieri con reinserimento."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    m = np.array([x[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    lo, hi = np.quantile(m, [(1 - livello) / 2, 1 - (1 - livello) / 2])
    return cagr_da_media(lo, ga), cagr_da_media(hi, ga)


def bootstrap_blocchi(x: np.ndarray, n_boot: int, blocco: int, ga: int, livello: float, rng) -> tuple[float, float]:
    """Intervallo percentile del CAGR con blocchi circolari di `blocco` sedute consecutive."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    nb = int(np.ceil(n / blocco))
    salti = np.arange(blocco)[None, :]
    m = np.empty(n_boot)
    for i in range(n_boot):
        inizi = rng.integers(0, n, nb)[:, None]
        idx = ((inizi + salti) % n).ravel()[:n]
        m[i] = x[idx].mean()
    lo, hi = np.quantile(m, [(1 - livello) / 2, 1 - (1 - livello) / 2])
    return cagr_da_media(lo, ga), cagr_da_media(hi, ga)


def copertura(x: np.ndarray, lung: int, inizi: np.ndarray, vero_annuo_log: float, ga: int, z: float) -> tuple[float, int]:
    """Quota di finestre di `lung` sedute (partenze `inizi`) il cui intervallo (formula) contiene il rendimento logaritmico annuo `vero_annuo_log`."""
    x = np.asarray(x, dtype=float)
    inizi = np.asarray(inizi)
    inizi = inizi[inizi + lung <= len(x)]
    c1 = np.concatenate([[0.0], np.cumsum(x)])
    c2 = np.concatenate([[0.0], np.cumsum(x * x)])
    s1 = c1[inizi + lung] - c1[inizi]
    s2 = c2[inizi + lung] - c2[inizi]
    media = s1 / lung
    sd = np.sqrt((s2 - lung * media ** 2) / (lung - 1))
    se = sd / np.sqrt(lung)
    lo, hi = (media - z * se) * ga, (media + z * se) * ga
    return float(np.mean((lo <= vero_annuo_log) & (vero_annuo_log <= hi))), int(len(inizi))


def copertura_fuori(x: np.ndarray, lung: int, inizi: np.ndarray, ga: int, z: float) -> tuple[float, int]:
    """Copertura onesta: per ogni finestra di `lung` sedute, l'intervallo della finestra (allargato per l'incertezza del riferimento) contiene il
    rendimento logaritmico medio di TUTTE LE ALTRE sedute? Il riferimento non contiene la finestra stessa."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    inizi = np.asarray(inizi)
    inizi = inizi[inizi + lung <= n]
    c1 = np.concatenate([[0.0], np.cumsum(x)])
    c2 = np.concatenate([[0.0], np.cumsum(x * x)])
    s1 = c1[inizi + lung] - c1[inizi]
    s2 = c2[inizi + lung] - c2[inizi]
    media = s1 / lung
    sd = np.sqrt((s2 - lung * media ** 2) / (lung - 1))
    resto = (c1[-1] - s1) / (n - lung)
    se2 = sd ** 2 / lung + x.var(ddof=1) / (n - lung)
    return float(np.mean(np.abs(media - resto) <= z * np.sqrt(se2))), int(len(inizi))


def anni_necessari(sigma_annua: float, semiampiezza: float, z: float) -> float:
    """Anni di dati perché la semiampiezza dell'intervallo del rendimento logaritmico annuo scenda a `semiampiezza`: (z sigma / h)^2."""
    return float((z * sigma_annua / semiampiezza) ** 2)


def inizi_mese(date: pd.DatetimeIndex) -> np.ndarray:
    """Posizioni della prima seduta di ogni mese."""
    s = pd.Series(np.arange(len(date)), index=date)
    return s.groupby([date.year, date.month]).first().to_numpy()
