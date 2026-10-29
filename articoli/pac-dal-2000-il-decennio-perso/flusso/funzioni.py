"""Funzioni dell'articolo 426: prezzi mensili, piano di accumulo, lump sum, rimescolamento dei rendimenti mensili."""
import numpy as np
import pandas as pd

import config


def prezzi_mensili(close: pd.Series) -> pd.Series:
    """Chiusura della prima seduta di ogni mese; il primo mese, se parziale, è scartato."""
    c = close.dropna()
    c = c[c > 0]
    mese = c.index.to_period("M")
    p = c.groupby(mese).first()
    if c.index[0].day > 5:                 # il primo mese dei dati è parziale: lo si scarta
        p = p.iloc[1:]
    return p


def valore_netto(lordo: np.ndarray, versato: float) -> np.ndarray:
    """Valore dopo la commissione di vendita e l'imposta sulla plusvalenza (se positiva)."""
    plus = lordo - versato - config.COMMISSIONE
    return lordo - config.COMMISSIONE - np.where(plus > 0, config.ALIQUOTA * plus, 0.0)


def piani(p: np.ndarray, mesi: int = None) -> tuple[np.ndarray, np.ndarray]:
    """Rendimento totale netto del PAC e del lump sum per ogni data di partenza s con una finestra completa.

    PAC: versamento a ogni mese s..s+mesi-1 (commissione su ogni acquisto), vendita alla chiusura del mese s+mesi.
    Lump sum: la stessa somma totale investita nel mese s (una commissione), vendita nello stesso istante.
    """
    mesi = mesi or config.MESI
    n = len(p)
    inv = np.r_[0.0, np.cumsum(1.0 / p)]
    starts = np.arange(0, n - mesi)                       # s + mesi deve esistere
    unita = (config.VERSAMENTO - config.COMMISSIONE) * (inv[starts + mesi] - inv[starts])
    versato = config.VERSAMENTO * mesi
    pac = valore_netto(unita * p[starts + mesi], versato) / versato - 1
    quote_ls = (versato - config.COMMISSIONE) / p[starts]
    ls = valore_netto(quote_ls * p[starts + mesi], versato) / versato - 1
    return pac, ls


def curva_piano(p: np.ndarray, s: int, mesi: int = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Valore lordo del PAC, del lump sum e totale versato, mese per mese, per il piano che parte in s (mesi+1 punti)."""
    mesi = mesi or config.MESI
    k = np.arange(mesi + 1)
    unita = np.r_[0.0, np.cumsum((config.VERSAMENTO - config.COMMISSIONE) / p[s:s + mesi])]
    pac = unita * p[s:s + mesi + 1]
    ls = (config.VERSAMENTO * mesi - config.COMMISSIONE) / p[s] * p[s:s + mesi + 1]
    return pac, ls, config.VERSAMENTO * np.minimum(k, mesi)


def serie_rimescolata(p: np.ndarray, rng) -> np.ndarray:
    """Serie con gli stessi rendimenti logaritmici mensili in ordine casuale, stesso punto di partenza."""
    r = np.diff(np.log(p))
    return p[0] * np.exp(np.r_[0.0, np.cumsum(rng.permutation(r))])
