"""Funzioni dell'esperimento sull'overfitting, separate dal flusso perché si possano controllare su dati inventati."""
import numpy as np
import pandas as pd

import motore_vettoriale as m


def coppie(veloci, lente) -> list[tuple[int, int]]:
    return [(f, l) for f in veloci for l in lente if f < l]


def log_rendimenti(close: pd.Series, lista: list[tuple[int, int]], costo: float) -> np.ndarray:
    """Matrice (coppie x sedute) dei logaritmi di 1 + rendimento giornaliero netto della regola con segnale ritardato di un giorno.
    Il costo è una quota del valore a ogni cambio di posizione."""
    rend = m.rendimenti(close)
    medie = {}
    for n in sorted({x for c in lista for x in c}):
        medie[n] = close.rolling(n).mean()
    out = np.empty((len(lista), len(close)), dtype=np.float32)
    for k, (f, l) in enumerate(lista):
        seg = (medie[f] > medie[l]) & medie[l].notna()
        pos = m.posizione(seg, 1)
        cambi = pos.astype(int).diff().abs().fillna(0)
        r = rend * pos.astype(float) - costo * cambi
        out[k] = np.log1p(r.to_numpy())
    return out


def finestre(n: int, inizio: int, ott: int, prova: int, passo: int) -> list[tuple[int, int, int]]:
    """(inizio ottimizzazione, inizio prova, fine prova esclusa) di ogni finestra che sta dentro i dati."""
    out, s = [], inizio
    while s + ott + prova <= n:
        out.append((s, s + ott, s + ott + prova))
        s += passo
    return out


def cagr_finestra(logr: np.ndarray, date: pd.DatetimeIndex, a: int, b: int) -> np.ndarray:
    """Rendimento annuo composto di ogni riga della matrice sulle sedute da a (inclusa) a b (esclusa)."""
    anni = (date[b - 1] - date[a - 1]).days / 365.25
    return np.exp(logr[:, a:b].sum(axis=1, dtype=np.float64) / anni) - 1.0


def migliore_nei_sottoinsiemi(train: np.ndarray, test: np.ndarray, perm: np.ndarray, dimensioni) -> dict[int, tuple[float, float]]:
    """Per ogni dimensione n, tra i primi n elementi di ciascuna permutazione prende quello col rendimento di ottimizzazione più alto;
    restituisce la media, sulle permutazioni, del suo rendimento in ottimizzazione e in prova."""
    out = {}
    for n in dimensioni:
        idx = perm[:, :n]
        t = train[idx]
        j = idx[np.arange(len(idx)), t.argmax(axis=1)]
        out[n] = (float(train[j].mean()), float(test[j].mean()))
    return out
