"""Motore del volatility targeting. Funzioni pure su serie di prezzi: nessun accesso a file, nessuna rete.

Regole (da dichiarare nell'articolo):
  - volatilità: deviazione standard dei rendimenti giornalieri semplici delle ultime `finestra` sedute, annualizzata;
  - a fine mese (ultima seduta del mese) il peso obiettivo è min(tetto, obiettivo / volatilità);
  - il peso calcolato alla chiusura t viene scambiato alla chiusura t+1 e lavora sul rendimento della seduta t+2
    (segnale di ieri, posizione di oggi): la posizione che guadagna il rendimento di t è quindi `segnale[t-2]`;
  - la quota non investita sta in cassa, che non rende; i dividendi non sono considerati;
  - ogni scambio costa `costo_bp` punti base sul valore scambiato (|variazione del peso|); anche l'acquisto iniziale.
"""
import numpy as np
import pandas as pd


def rendimenti(close: pd.Series) -> pd.Series:
    return close.pct_change()


def fine_mese(indice: pd.DatetimeIndex) -> np.ndarray:
    """True nell'ultima seduta di ogni mese; l'ultima riga dei dati non conta (il mese può non essere finito)."""
    mese = indice.year * 12 + indice.month
    ultimo = np.r_[mese[1:] != mese[:-1], False]
    return np.asarray(ultimo)


def volatilita(r: pd.Series, finestra: int, giorni_anno: int) -> pd.Series:
    return r.rolling(finestra).std(ddof=1) * np.sqrt(giorni_anno)


def segnale_peso(close: pd.Series, obiettivo: float, finestra: int, tetto: float, giorni_anno: int) -> pd.Series:
    """Peso obiettivo noto alla chiusura di ogni seduta (cambia solo a fine mese, poi resta fermo)."""
    r = rendimenti(close)
    vol = volatilita(r, finestra, giorni_anno)
    peso = np.minimum(tetto, obiettivo / vol)
    peso = peso.where(pd.Series(fine_mese(close.index), index=close.index))
    return peso.ffill()


def posizione(segnale: pd.Series) -> pd.Series:
    """Peso con cui si guadagna il rendimento della seduta t: segnale della seduta t-2."""
    return segnale.shift(2)


def serie_strategia(close: pd.Series, obiettivo: float, finestra: int, tetto: float, giorni_anno: int,
                    costo_bp: float) -> pd.DataFrame:
    """Rendimenti giornalieri netti di strategia e buy & hold, dalla prima seduta con posizione definita."""
    r = rendimenti(close)
    sig = segnale_peso(close, obiettivo, finestra, tetto, giorni_anno)
    pos = posizione(sig)
    valido = pos.notna() & r.notna()
    primo = np.flatnonzero(valido.to_numpy())
    if len(primo) == 0:
        raise ValueError("nessuna seduta con posizione definita")
    i0 = int(primo[0])
    r = r.iloc[i0:]
    pos = pos.iloc[i0:]
    sig = sig.iloc[i0:]
    prec = pos.shift(1).fillna(0.0)                     # prima seduta: si parte da zero, l'acquisto iniziale costa
    scambio = (pos - prec).abs()
    c = costo_bp / 1e4
    rs = pos * r - c * scambio
    rb = r.copy()
    rb.iloc[0] -= c * 1.0                                # buy & hold: anche lui paga l'acquisto iniziale
    fm = fine_mese(close.index)
    effettivo = np.r_[False, False, fm[:-2]][i0:]          # True nella seduta in cui il nuovo peso comincia a lavorare
    periodo = np.cumsum(effettivo)
    return pd.DataFrame({"r": r, "peso": pos, "scambio": scambio, "strategia": rs, "buyhold": rb,
                         "periodo": periodo})


def equity(rend: pd.Series | np.ndarray) -> np.ndarray:
    return np.cumprod(1.0 + np.asarray(rend, dtype=float))


def sharpe(rend, giorni_anno: int) -> float:
    x = np.asarray(rend, dtype=float)
    sd = x.std(ddof=0)
    return float(x.mean() / sd * np.sqrt(giorni_anno)) if sd > 0 else float("nan")


def vol_annua(rend, giorni_anno: int) -> float:
    return float(np.asarray(rend, dtype=float).std(ddof=0) * np.sqrt(giorni_anno))


def perdita_massima(rend) -> float:
    e = np.r_[1.0, equity(rend)]
    return float((e / np.maximum.accumulate(e) - 1).min())


def cagr(rend, anni: float) -> float:
    return float(equity(rend)[-1] ** (1 / anni) - 1)


def volvol(rend: pd.Series, giorni_anno: int) -> float:
    """Deviazione standard della volatilità annualizzata misurata su 252 sedute mobili."""
    v = rend.rolling(giorni_anno).std(ddof=0) * np.sqrt(giorni_anno)
    return float(v.dropna().std(ddof=0))


def sharpe_da_somme(w: np.ndarray, s1: np.ndarray, s2: np.ndarray, n: int, giorni_anno: int) -> np.ndarray:
    """Sharpe lordo di un portafoglio a pesi costanti per periodo: w, s1 (somma r), s2 (somma r^2) per periodo.
    Accetta w con più righe (una per scimmia)."""
    media = (w * s1).sum(axis=-1) / n
    m2 = (w ** 2 * s2).sum(axis=-1) / n
    sd = np.sqrt(np.maximum(m2 - media ** 2, 1e-30))
    return media / sd * np.sqrt(giorni_anno)


def bootstrap_dsharpe(rs: np.ndarray, rb: np.ndarray, n_boot: int, blocco: int, giorni_anno: int,
                      rng, a_pezzi: int = 100) -> np.ndarray:
    """Differenza di Sharpe (strategia - buy & hold) su ricampionamenti a blocchi circolari, coppie di giorni insieme."""
    n = len(rs)
    nb = int(np.ceil(n / blocco))
    out = np.empty(n_boot)
    off = np.arange(blocco)
    fatti = 0
    while fatti < n_boot:
        k = min(a_pezzi, n_boot - fatti)
        st = rng.integers(0, n, size=(k, nb))
        idx = ((st[:, :, None] + off) % n).reshape(k, nb * blocco)[:, :n]
        xs, xb = rs[idx], rb[idx]
        ss = xs.mean(axis=1) / np.maximum(xs.std(axis=1), 1e-30)
        sb = xb.mean(axis=1) / np.maximum(xb.std(axis=1), 1e-30)
        out[fatti:fatti + k] = (ss - sb) * np.sqrt(giorni_anno)
        fatti += k
    return out
