"""Funzioni dell'articolo 303: rendimenti mensili, scelta dell'ordine ARIMA, previsioni fuori campione, test di Clark-West, bootstrap."""
import math
import warnings

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.tsa.arima.model import ARIMA


def rendimenti_mensili(close: pd.Series) -> pd.Series:
    """Rendimenti logaritmici mensili sulle chiusure dell'ultimo giorno di Borsa di ogni mese. L'ultimo mese dei dati,
    di solito incompleto, è scartato."""
    mese = close.groupby([close.index.year, close.index.month]).last()
    mese.index = pd.PeriodIndex([pd.Period(year=a, month=m, freq="M") for a, m in mese.index])
    return np.log(mese).diff().dropna().iloc[:-1]


def adatta(y: np.ndarray, p: int, q: int):
    """ARMA(p, q) con costante sui rendimenti; None se l'adattamento non converge."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            ris = ARIMA(y, order=(p, 0, q), trend="c").fit()
        except Exception:
            return None
    if not np.isfinite(ris.bic):
        return None
    return ris


def scegli_ordine(y: np.ndarray, pmax: int, qmax: int, criterio: str = "bic"):
    """Prova tutti gli ordini (p, q) fino a (pmax, qmax). Restituisce (ordine migliore, risultato, tabella {(p,q): criterio})."""
    tabella, miglior = {}, (None, None, np.inf)
    for p in range(pmax + 1):
        for q in range(qmax + 1):
            ris = adatta(y, p, q)
            if ris is None:
                continue
            v = ris.bic if criterio == "bic" else ris.aic
            tabella[(p, q)] = float(v)
            if v < miglior[2]:
                miglior = ((p, q), ris, v)
    return miglior[0], miglior[1], tabella


def previsioni_rolling(y: np.ndarray, iniziale: int, ogni: int, pmax: int, qmax: int):
    """Previsione a un mese per tutti i mesi da `iniziale` in poi. Ogni `ogni` mesi si sceglie l'ordine con il BIC e si ristimina il modello su tutti
    i dati fino a quel mese; nei mesi in mezzo i parametri restano fissi e la previsione usa solo i rendimenti già noti.
    Restituisce (previsione ARIMA, media storica, valori reali, ordini scelti per blocco)."""
    T = len(y)
    f_mod, f_med, reale, ordini = [], [], [], []
    for t0 in range(iniziale, T, ogni):
        ordine, ris, _ = scegli_ordine(y[:t0], pmax, qmax)
        t1 = min(t0 + ogni, T)
        nuovo = ris.apply(y[:t1])                     # stessi parametri, dati noti fino a t1
        pred = np.asarray(nuovo.predict(start=t0, end=t1 - 1))
        # la previsione del mese t usa solo i dati fino a t - 1: predict() in-sample è una previsione a un passo
        f_mod.extend(pred.tolist())
        f_med.extend([float(y[:t].mean()) for t in range(t0, t1)])
        reale.extend(y[t0:t1].tolist())
        ordini.append(ordine)
    return np.array(f_mod), np.array(f_med), np.array(reale), ordini


def newey_west_t(x: np.ndarray, lag: int) -> float:
    """Statistica t della media di x con errore standard di Newey-West (pesi di Bartlett)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    d = x - x.mean()
    s = float(d @ d) / n
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * float(d[k:] @ d[:-k]) / n
    return float(x.mean() / math.sqrt(s / n))


def clark_west(reale, f_base, f_mod, lag: int) -> tuple[float, float]:
    """Test di Clark-West per modelli annidati: il modello più grande batte quello di base? Restituisce (t, p-value a una coda)."""
    reale, f_base, f_mod = (np.asarray(v, dtype=float) for v in (reale, f_base, f_mod))
    e_b, e_m = reale - f_base, reale - f_mod
    f = e_b ** 2 - (e_m ** 2 - (f_base - f_mod) ** 2)
    t = newey_west_t(f, lag)
    return t, float(1 - norm.cdf(t))


def r2_fuori_campione(reale, f_base, f_mod) -> float:
    reale, f_base, f_mod = (np.asarray(v, dtype=float) for v in (reale, f_base, f_mod))
    return float(1 - np.sum((reale - f_mod) ** 2) / np.sum((reale - f_base) ** 2))


def bootstrap_stazionario(rng, n: int, lunghezza_media: float, n_boot: int):
    """Indici di un bootstrap stazionario (Politis-Romano): blocchi di lunghezza geometrica con media `lunghezza_media`."""
    p = 1.0 / lunghezza_media
    for _ in range(n_boot):
        idx = np.empty(n, dtype=int)
        idx[0] = rng.integers(n)
        nuovo = rng.random(n) < p
        salti = rng.integers(n, size=n)
        for i in range(1, n):
            idx[i] = salti[i] if nuovo[i] else (idx[i - 1] + 1) % n
        yield idx


def ljung_box_serie(x: np.ndarray, h: int) -> tuple[float, float]:
    from statsmodels.stats.diagnostic import acorr_ljungbox
    r = acorr_ljungbox(np.asarray(x, dtype=float), lags=[h], return_df=True)
    return float(r["lb_stat"].iloc[0]), float(r["lb_pvalue"].iloc[0])
