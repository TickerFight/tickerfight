"""Motore vettoriale minimo: segnale, posizione, rendimenti. Senza commissioni né tasse, per isolare l'effetto del look-ahead.

Convenzioni:
  - rend[t] è il rendimento della seduta t: chiusura di t su chiusura di t-1;
  - il segnale[t] si calcola con le chiusure fino a t incluse;
  - posizione(segnale, ritardo): ritardo = 0 usa il segnale di t per il rendimento di t (LOOK-AHEAD: si compra alla
    chiusura di ieri sapendo la chiusura di oggi); ritardo = 1 usa il segnale di ieri (onesto).
"""
import numpy as np
import pandas as pd


def rendimenti(close: pd.Series) -> pd.Series:
    return close.pct_change().fillna(0.0)


def segnale_un_giorno(close: pd.Series) -> pd.Series:
    return close > close.shift(1)


def segnale_sopra_media(close: pd.Series, n: int) -> pd.Series:
    return (close > close.rolling(n).mean()) & close.rolling(n).mean().notna()


def segnale_medie(close: pd.Series, veloce: int, lenta: int) -> pd.Series:
    sl = close.rolling(lenta).mean()
    return (close.rolling(veloce).mean() > sl) & sl.notna()


def posizione(segnale: pd.Series, ritardo: int) -> pd.Series:
    """True se si è investiti nella seduta, dato il ritardo con cui il segnale è noto."""
    if ritardo < 0:
        raise ValueError("ritardo negativo: sarebbe usare il futuro")
    return segnale.shift(ritardo, fill_value=False).astype(bool)


def valore(rend: pd.Series, pos: pd.Series) -> pd.Series:
    """Valore di 1 investito, composto giorno per giorno: nei giorni in cassa il rendimento è zero."""
    return (1.0 + rend * pos.astype(float)).cumprod()


def cagr(v: pd.Series, anni: float) -> float:
    return float(v.iloc[-1] ** (1.0 / anni) - 1.0)


def perdita_massima(v: pd.Series) -> float:
    return float((v / v.cummax() - 1.0).min())


def ricostruisci_grezzo(close: pd.Series, splits: pd.Series) -> pd.Series:
    """Prezzo come era scritto sullo schermo il giorno stesso, prima delle correzioni per gli split.

    `close` è la chiusura già corretta per gli split (come la dà Yahoo Finance); `splits` vale 0 nei giorni senza split e
    il rapporto (per esempio 7 per un 7 a 1) nel giorno dello split. Il prezzo grezzo di un giorno t è la chiusura corretta
    moltiplicata per il prodotto dei rapporti di tutti gli split avvenuti DOPO t.
    """
    r = splits.where(splits > 0, 1.0).astype(float)
    dopo = r[::-1].cumprod()[::-1].shift(-1, fill_value=1.0)   # prodotto degli split strettamente successivi
    return close * dopo
