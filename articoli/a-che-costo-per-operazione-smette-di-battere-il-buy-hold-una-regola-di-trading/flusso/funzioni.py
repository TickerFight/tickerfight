"""Funzioni dell'articolo 102: regole, rendimenti netti dei costi, costo di pareggio, scimmie.
Separate dal flusso perché si possano controllare su dati inventati (verifica_motore.py)."""
import numpy as np
import pandas as pd

import motore_vettoriale as m


# --- Regole (le stesse dell'articolo 61) --------------------------------------------------------------------------
def segnale(close: pd.Series, spec: tuple) -> pd.Series:
    """True se la regola è 'investito', calcolato con le chiusure fino a t incluse."""
    tipo = spec[0]
    if tipo == "bh":
        return pd.Series(True, index=close.index)
    if tipo == "sopra_media":
        return m.segnale_sopra_media(close, spec[1])
    if tipo == "incrocio":
        return m.segnale_medie(close, spec[1], spec[2])
    if tipo == "momentum":
        passato = close.shift(spec[1])
        return (close > passato) & passato.notna()
    if tipo == "calma":
        vol = m.rendimenti(close).rolling(spec[1]).std() * np.sqrt(252)
        return (vol < spec[2]) & vol.notna()
    if tipo == "ritorno_media":
        lenta = close.rolling(spec[2]).mean()
        return (close < close.rolling(spec[1]).mean()) & (close > lenta) & lenta.notna()
    raise ValueError(f"regola sconosciuta: {tipo}")


def posizione_regola(close: pd.Series, spec: tuple) -> pd.Series:
    """Quota investita (0 o 1) nella seduta; il segnale di ieri decide la posizione di oggi."""
    return m.posizione(segnale(close, spec), 1).astype(float)


def rendimenti_netti(rend: pd.Series, pos: pd.Series, costo: float) -> pd.Series:
    """Rendimento giornaliero della regola (rend = rendimenti giornalieri dell'indice), meno il costo su ogni variazione della quota investita."""
    cambi = pos.diff().abs()
    cambi.iloc[0] = abs(pos.iloc[0])          # l'ingresso iniziale dalla cassa è un cambio e si paga
    return rend * pos - costo * cambi


# --- Metriche ----------------------------------------------------------------------------------------------------------
def sharpe(R: np.ndarray, sedute_anno: int = 252) -> np.ndarray:
    R = np.asarray(R, dtype=float)
    sd = R.std(axis=-1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = R.mean(axis=-1) / sd * np.sqrt(sedute_anno)
    return np.where(sd > 0, v, np.nan)


def cagr(R: np.ndarray, anni: float) -> np.ndarray:
    R = np.asarray(R, dtype=float)
    return np.exp(np.log1p(R).sum(axis=-1) / anni) - 1.0


def perdita_massima(R: np.ndarray) -> np.ndarray:
    R = np.asarray(R, dtype=float)
    v = np.cumprod(1.0 + R, axis=-1)
    v = np.concatenate([np.ones(v.shape[:-1] + (1,)), v], axis=-1)
    return (v / np.maximum.accumulate(v, axis=-1) - 1.0).min(axis=-1)


# --- Ribilanciamento ---------------------------------------------------------------------------------------------------
def mix_ribilanciato(rend: np.ndarray, quota: float, ogni: int, costo: float) -> np.ndarray:
    """Rendimenti giornalieri netti di un portafoglio con una quota fissa nell'indice e il resto in cassa (rendimento zero).

    Ogni `ogni` sedute (alla chiusura) la quota derivata viene riportata a `quota`; si paga `costo` sul valore scambiato,
    cioè |quota derivata - quota| del valore del portafoglio. All'inizio si parte tutto in cassa e si compra la quota obiettivo
    il primo giorno (anche questo scambio si paga: `quota` del valore)."""
    rend = np.asarray(rend, dtype=float)
    out = np.empty(len(rend))
    w = quota
    for t, r in enumerate(rend):
        p = w * r
        w = w * (1.0 + r) / (1.0 + p)
        netto = p
        if t == 0:
            netto = (1.0 + p) * (1.0 - costo * quota) - 1.0   # ingresso iniziale dalla cassa
        if (t + 1) % ogni == 0:
            scambio = abs(w - quota)
            netto = (1.0 + netto) * (1.0 - costo * scambio) - 1.0
            w = quota
        out[t] = netto
    return out


# --- Scimmie -----------------------------------------------------------------------------------------------------------
def posizioni_scimmie(n: int, T: int, prob: float, rng) -> np.ndarray:
    """n posizioni casuali (1 investito, 0 cassa) lunghe T: partono investite e a ogni seduta cambiano stato con probabilità `prob`."""
    cambia = rng.random((n, T)) < prob
    cambia[:, 0] = False
    return (np.cumsum(cambia, axis=1) % 2 == 0).astype(float)


def rendimenti_scimmie(rend: np.ndarray, pos: np.ndarray, costo: float) -> np.ndarray:
    """Rendimenti netti di più posizioni (una per riga); il costo si paga a ogni cambio di stato."""
    cambi = np.abs(np.diff(pos, axis=1, prepend=np.zeros((pos.shape[0], 1))))   # l'ingresso iniziale dalla cassa si paga
    return rend[None, :] * pos - costo * cambi


# --- Correlazione di rango tra due classifiche ---------------------------------------------------------------------------
def posti(valori) -> np.ndarray:
    """Posto in classifica, 1 = valore più alto; parità = posto medio; valori non definiti = ultimi."""
    v = np.where(np.isnan(np.asarray(valori, dtype=float)), -np.inf, valori)
    return pd.Series(v).rank(ascending=False, method="average").to_numpy()


def kendall(a, b) -> float:
    """Tau-b di Kendall tra due vettori."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    da, db = np.sign(a[:, None] - a[None, :]), np.sign(b[:, None] - b[None, :])
    iu = np.triu_indices(len(a), 1)
    x, y = da[iu], db[iu]
    den = np.sqrt((x != 0).sum() * (y != 0).sum())
    return float((x * y).sum() / den) if den > 0 else float("nan")


# --- Costo di pareggio (articolo 102) ------------------------------------------------------------------------------------
def costo_pareggio(f_regola, f_riferimento, massimo: float, passi: int = 60) -> tuple[float, str]:
    """Costo per cambio a cui una regola smette di battere il riferimento.

    f_regola(c) e f_riferimento(c) restituiscono la misura (rendimento annuo o Sharpe) a costo c; la differenza non cresce con c.
    Ritorna (costo, stato): 'gia_sotto' se già a costo zero la regola non batte il riferimento (costo 0);
    'oltre' se la batte ancora al costo massimo (costo = massimo); altrimenti 'normale', con il costo trovato per bisezione."""
    if not f_regola(0.0) > f_riferimento(0.0):
        return 0.0, "gia_sotto"
    if f_regola(massimo) > f_riferimento(massimo):
        return massimo, "oltre"
    lo, hi = 0.0, massimo
    for _ in range(passi):
        mid = (lo + hi) / 2
        if f_regola(mid) > f_riferimento(mid):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2, "normale"


def spearman(a, b) -> float:
    """Correlazione di rango di Spearman (parità = rango medio)."""
    ra = pd.Series(np.asarray(a, dtype=float)).rank(method="average")
    rb = pd.Series(np.asarray(b, dtype=float)).rank(method="average")
    return float(np.corrcoef(ra, rb)[0, 1])
