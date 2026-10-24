"""Funzioni dell'esperimento: serie mensili, obbligazione sintetica a 10 anni, portafoglio ribilanciato, statistiche, bootstrap.

Convenzioni: tutti i rendimenti sono mensili e semplici (0,01 = 1%); i rendimenti da tassi sono decimali annui (0,04 = 4%).
"""
import numpy as np
import pandas as pd


def fine_mese(serie: pd.Series) -> pd.Series:
    """Ultimo valore di ogni mese (indice = periodo mensile)."""
    s = serie.sort_index()
    return s.groupby(s.index.to_period("M")).last()


def prezzo_cedola_pari(cedola: float, y: float, n_semestri: float) -> float:
    """Prezzo (per 1 di nominale) di un'obbligazione a cedole semestrali, con cedola annua `cedola`, al rendimento annuo `y`."""
    i = y / 2.0
    if abs(i) < 1e-12:
        return cedola / 2.0 * n_semestri + 1.0
    return cedola / 2.0 * (1.0 - (1.0 + i) ** (-n_semestri)) / i + (1.0 + i) ** (-n_semestri)


def rendimento_obbligazione(y_prec: float, y_ora: float, scadenza: float = 10.0) -> float:
    """Rendimento di un mese di un Treasury a cedola pari comprato a fine mese precedente (cedola = y_prec) e rivenduto a fine mese.

    A fine mese la scadenza residua è scadenza - 1/12 anni; il rendimento è y_ora. Include il rateo di cedola di un mese.
    """
    n = 2.0 * (scadenza - 1.0 / 12.0)
    return prezzo_cedola_pari(y_prec, y_ora, n) + y_prec / 12.0 - 1.0


def portafoglio(rs: np.ndarray, rb: np.ndarray, mesi: pd.PeriodIndex, w) -> np.ndarray:
    """Rendimenti mensili di un portafoglio azioni/obbligazioni ribilanciato a ogni gennaio (e al primo mese).

    w: peso azionario. Scalare; oppure array (S,) = S portafogli con un peso ciascuno; oppure array (S, Y) con un peso per anno
    solare (Y = numero di anni solari distinti dei mesi, in ordine). Restituisce un array (S, n_mesi).
    """
    anni = np.array([m.year for m in mesi])
    anni_u = list(dict.fromkeys(anni))
    w = np.asarray(w, float)
    if w.ndim == 0:
        w = w.reshape(1, 1)
    elif w.ndim == 1:
        w = w[:, None]
    S = w.shape[0]
    out = np.empty((S, len(mesi)))
    va = vb = None
    for i, m in enumerate(mesi):
        if i == 0 or m.month == 1:
            wy = w[:, 0] if w.shape[1] == 1 else w[:, anni_u.index(m.year)]
            va, vb = wy.copy(), 1.0 - wy
        tot = va + vb
        va = va * (1.0 + rs[i])
        vb = vb * (1.0 + rb[i])
        out[:, i] = (va + vb) / tot - 1.0
    return out


def cagr(r: np.ndarray) -> float:
    return float(np.prod(1.0 + r) ** (12.0 / len(r)) - 1.0)


def volatilita(r: np.ndarray) -> float:
    return float(np.std(r, ddof=1) * np.sqrt(12.0))


def sharpe(r: np.ndarray, cassa: np.ndarray, asse: int = -1):
    """Sharpe annualizzato sugli eccessi mensili rispetto alla liquidità."""
    e = r - cassa
    return e.mean(axis=asse) / e.std(axis=asse, ddof=1) * np.sqrt(12.0)


def perdita_massima(r: np.ndarray) -> float:
    """Massimo calo dal picco (numero negativo), sul valore cumulato dei rendimenti mensili."""
    v = np.cumprod(1.0 + np.r_[0.0, r][1:])
    v = np.r_[1.0, v]
    return float((v / np.maximum.accumulate(v) - 1.0).min())


def rendimenti_anno_solare(r: np.ndarray, mesi: pd.PeriodIndex) -> pd.Series:
    anni = np.array([m.year for m in mesi])
    return pd.Series(1.0 + r, index=anni).groupby(level=0).prod() - 1.0


def regime(y_prec_pct: np.ndarray, soglia_bassi: float, soglia_alti: float) -> np.ndarray:
    """'bassi' sotto soglia_bassi, 'alti' da soglia_alti in su, 'medi' in mezzo (rendimento in %)."""
    return np.where(y_prec_pct < soglia_bassi, "bassi", np.where(y_prec_pct >= soglia_alti, "alti", "medi"))


def finestre_mobili(r: np.ndarray, n: int) -> np.ndarray:
    """Rendimento annualizzato dei rendimenti r[t+1 .. t+n] per ogni t con t+n < len(r) (t = ultimo mese noto alla partenza)."""
    lr = np.log1p(r)
    c = np.r_[0.0, np.cumsum(lr)]
    k = len(r) - n
    tot = c[n + 1:n + 1 + k] - c[1:1 + k] if k > 0 else np.array([])
    return np.expm1(tot * 12.0 / n)


def indici_blocchi(n: int, blocco: int, rng) -> np.ndarray:
    """Indici di un campione bootstrap a blocchi circolari lungo n."""
    k = int(np.ceil(n / blocco))
    inizi = rng.integers(0, n, k)
    return ((inizi[:, None] + np.arange(blocco)[None, :]) % n).ravel()[:n]
