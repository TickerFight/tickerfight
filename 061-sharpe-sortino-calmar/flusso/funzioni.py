"""Funzioni dell'articolo 61: regole, metriche, correlazioni di rango, bootstrap e scimmie.
Separate dal flusso perché si possano controllare su dati inventati (verifica_motore.py)."""
import numpy as np
import pandas as pd

import motore_vettoriale as m


# --- Regole -------------------------------------------------------------------------------------------------
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
    """Quota investita (0, 1 o 0,5) nella seduta; il segnale di ieri decide la posizione di oggi."""
    if spec[0] == "meta":
        return pd.Series(0.5, index=close.index)
    return m.posizione(segnale(close, spec), 1).astype(float)


def rendimenti_netti(close: pd.Series, pos: pd.Series, costo: float) -> pd.Series:
    """Rendimento giornaliero della regola, meno il costo su ogni variazione della quota investita."""
    cambi = pos.diff().abs().fillna(0.0)
    return m.rendimenti(close) * pos - costo * cambi


# --- Metriche (lavorano sull'ultimo asse: una riga per regola) ----------------------------------------------------
def _nan_se(cond_ok, valori):
    return np.where(cond_ok, valori, np.nan)


def sharpe(R: np.ndarray, sedute_anno: int = 252, tasso: float = 0.0) -> np.ndarray:
    R = np.asarray(R, dtype=float)
    sd = R.std(axis=-1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = (R.mean(axis=-1) - tasso / sedute_anno) / sd * np.sqrt(sedute_anno)
    return _nan_se(sd > 0, v)


def sortino(R: np.ndarray, sedute_anno: int = 252, obiettivo: float = 0.0) -> np.ndarray:
    R = np.asarray(R, dtype=float)
    dd = np.sqrt((np.minimum(R - obiettivo / sedute_anno, 0.0) ** 2).mean(axis=-1))
    with np.errstate(divide="ignore", invalid="ignore"):
        v = (R.mean(axis=-1) - obiettivo / sedute_anno) / dd * np.sqrt(sedute_anno)
    return _nan_se(dd > 0, v)


def cagr(R: np.ndarray, anni: float) -> np.ndarray:
    R = np.asarray(R, dtype=float)
    return np.exp(np.log1p(R).sum(axis=-1) / anni) - 1.0


def perdita_massima(R: np.ndarray) -> np.ndarray:
    """Perdita massima dal massimo precedente (numero negativo o zero), partendo da un valore iniziale 1."""
    R = np.asarray(R, dtype=float)
    v = np.cumprod(1.0 + R, axis=-1)
    v = np.concatenate([np.ones(v.shape[:-1] + (1,)), v], axis=-1)
    return (v / np.maximum.accumulate(v, axis=-1) - 1.0).min(axis=-1)


def calmar(R: np.ndarray, anni: float) -> np.ndarray:
    mdd = perdita_massima(R)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = cagr(R, anni) / (-mdd)
    return _nan_se(mdd < 0, v)


# --- Classifiche e correlazioni di rango ---------------------------------------------------------------------------
def posti(valori) -> np.ndarray:
    """Posto in classifica, 1 = valore più alto; parità = posto medio; valori non definiti = ultimi."""
    v = np.where(np.isnan(np.asarray(valori, dtype=float)), -np.inf, valori)
    return pd.Series(v).rank(ascending=False, method="average").to_numpy()


def vincitore(valori) -> int:
    v = np.where(np.isnan(np.asarray(valori, dtype=float)), -np.inf, valori)
    return int(np.argmax(v))


def spearman(a, b) -> float:
    pa, pb = posti(a), posti(b)
    if pa.std() == 0 or pb.std() == 0:
        return float("nan")
    return float(np.corrcoef(pa, pb)[0, 1])


def kendall(a, b) -> float:
    """Tau-b di Kendall tra due vettori."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    da, db = np.sign(a[:, None] - a[None, :]), np.sign(b[:, None] - b[None, :])
    iu = np.triu_indices(len(a), 1)
    x, y = da[iu], db[iu]
    den = np.sqrt((x != 0).sum() * (y != 0).sum())
    return float((x * y).sum() / den) if den > 0 else float("nan")


# --- Blocchi, bootstrap, scimmie ---------------------------------------------------------------------------------------
def blocchi(n: int, lunghezza: int) -> list[tuple[int, int]]:
    """Intervalli [a, b) di blocchi consecutivi non sovrapposti che stanno dentro n sedute."""
    return [(k * lunghezza, (k + 1) * lunghezza) for k in range(n // lunghezza)]


def indici_blocchi_circolari(n: int, lunghezza: int, ripetizioni: int, rng) -> np.ndarray:
    """Indici (ripetizioni x n) di un bootstrap a blocchi circolari: blocchi di sedute consecutive, estratti con reinserimento."""
    nb = -(-n // lunghezza)
    inizi = rng.integers(0, n, size=(ripetizioni, nb))
    idx = (inizi[:, :, None] + np.arange(lunghezza)[None, None, :]) % n
    return idx.reshape(ripetizioni, nb * lunghezza)[:, :n]


def sequenze(pos_investito: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Valori (True investito / False cassa) e lunghezze delle sequenze consecutive."""
    b = np.asarray(pos_investito, dtype=bool)
    inizi = np.r_[0, np.flatnonzero(b[1:] != b[:-1]) + 1]
    return b[inizi], np.diff(np.r_[inizi, len(b)])


def scimmia(valori: np.ndarray, lunghezze: np.ndarray, rng) -> np.ndarray:
    """Posizione casuale con lo stesso numero di cambi e lo stesso tempo investito: si rimescolano le lunghezze delle sequenze
    investite tra le sequenze investite e quelle in cassa tra le sequenze in cassa; la prima sequenza resta del suo tipo."""
    l = lunghezze.copy()
    for stato in (True, False):
        mask = valori == stato
        l[mask] = rng.permutation(l[mask])
    return np.repeat(valori, l)
