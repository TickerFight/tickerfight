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


def volatilita_annua(rend: pd.Series, pos: pd.Series) -> float:
    return float((rend * pos.astype(float)).std() * np.sqrt(252))


def blocchi(pos: np.ndarray) -> list[tuple[bool, int]]:
    """Scompone una posizione in blocchi consecutivi (stato, lunghezza)."""
    pos = np.asarray(pos, bool)
    if len(pos) == 0:
        return []
    cambi = np.flatnonzero(pos[1:] != pos[:-1]) + 1
    inizi = np.r_[0, cambi]
    fini = np.r_[cambi, len(pos)]
    return [(bool(pos[a]), int(b - a)) for a, b in zip(inizi, fini)]


def calendario_casuale(blocchi_orig: list[tuple[bool, int]], rng: np.random.Generator) -> np.ndarray:
    """Stessi periodi dentro e fuori della regola, in ordine mescolato: stessa quota investita, stesso numero di cambi."""
    dentro = [l for s, l in blocchi_orig if s]
    fuori = [l for s, l in blocchi_orig if not s]
    rng.shuffle(dentro)
    rng.shuffle(fuori)
    di, fi = iter(dentro), iter(fuori)
    pezzi = [np.full(next(di) if s else next(fi), s) for s, _ in blocchi_orig]
    return np.concatenate(pezzi)
