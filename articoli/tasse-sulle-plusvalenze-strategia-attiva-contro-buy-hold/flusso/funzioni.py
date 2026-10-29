"""Funzioni dell'articolo 108: filtro sotto la media mobile e simulazione dell'imposta sulle plusvalenze con compensazione delle minusvalenze."""
import numpy as np
import pandas as pd


def media_mobile(close: np.ndarray, lung: int) -> np.ndarray:
    return pd.Series(np.asarray(close, dtype=float)).rolling(lung).mean().to_numpy()


def posizione_semplice(close: np.ndarray, sma: np.ndarray) -> np.ndarray:
    """1 = investito, 0 = in liquidità, deciso alla chiusura t (sopra la media: investito)."""
    return (np.asarray(close) >= np.asarray(sma)).astype(int)


def simula_fisco(lr: np.ndarray, pos: np.ndarray, anni_solari: np.ndarray, aliquota: float, costo: float = 0.0,
                 anni_credito: int = 4) -> dict:
    """Capitale iniziale 1. Il giorno t il capitale investito rende exp(lr[t]) se pos[t] = 1, zero altrimenti.
    A ogni cambio di posizione si paga il costo (moltiplicativo). A ogni uscita si realizza la plusvalenza (o minusvalenza) rispetto al capitale
    di ingresso: la plusvalenza è tassata al netto delle minusvalenze ancora valide (fino al quarto anno solare dopo la perdita, consumate dalla più vecchia);
    la minusvalenza diventa credito. L'imposta è tolta subito dal capitale. Alla fine, se si è investiti, si liquida e si tassa la plusvalenza latente.
    Restituisce il capitale finale, le imposte per anno solare, il capitale all'inizio di ogni anno e le plusvalenze/minusvalenze realizzate."""
    lr, pos, yrs = np.asarray(lr, dtype=float), np.asarray(pos), np.asarray(anni_solari)
    w = 1.0
    base = 1.0 if pos[0] == 1 else None
    crediti: list[list[float]] = []                    # [anno della perdita, importo]
    imposte: dict[int, float] = {}
    realizzi: list[float] = []
    capitale_anno: dict[int, float] = {}
    prec = pos[0]

    def tassa(gain: float, anno: int) -> float:
        nonlocal crediti
        realizzi.append(gain)
        crediti = [c for c in crediti if c[0] + anni_credito >= anno and c[1] > 0]
        if gain <= 0:
            if gain < 0:
                crediti.append([anno, -gain])
            return 0.0
        resto = gain
        for c in crediti:
            usa = min(c[1], resto)
            c[1] -= usa
            resto -= usa
            if resto <= 0:
                break
        t = aliquota * resto
        imposte[anno] = imposte.get(anno, 0.0) + t
        return t

    for t in range(len(lr)):
        anno = int(yrs[t])
        capitale_anno.setdefault(anno, w)
        if pos[t] != prec:
            w *= (1.0 - costo)
            if pos[t] == 0:                            # uscita: si realizza
                w -= tassa(w - base, anno)
                base = None
            else:                                      # ingresso: nuovo prezzo di carico
                base = w
            prec = pos[t]
        if pos[t] == 1:
            w *= np.exp(lr[t])
    if prec == 1 and base is not None:                 # liquidazione finale
        w -= tassa(w - base, int(yrs[len(lr) - 1]))
    return dict(capitale=w, imposte=imposte, capitale_anno=capitale_anno, realizzi=realizzi)


def cagr_da_capitale(capitale: float, anni: float) -> float:
    return float(capitale ** (1.0 / anni) - 1.0)
