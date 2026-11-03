"""Il motore vettoriale dell'articolo n. 6. Conta le righe di codice (esclusi vuote, commenti e docstring): sono meno di 50."""
import numpy as np
import pandas as pd


def segnale_sopra_media(close: pd.Series, n: int) -> pd.Series:
    media = close.rolling(n).mean()
    return (close > media) & media.notna()          # vero = voglio essere investito


def segnale_medie(close: pd.Series, veloce: int, lenta: int) -> pd.Series:
    lenta_ = close.rolling(lenta).mean()
    return (close.rolling(veloce).mean() > lenta_) & lenta_.notna()


def segnale_un_giorno(close: pd.Series) -> pd.Series:
    return close > close.shift(1)


def backtest(close: pd.Series, segnale: pd.Series, costo: float = 0.0) -> pd.DataFrame:
    """Restituisce posizione, rendimento netto e valore di 1 investito, seduta per seduta."""
    rend = close.pct_change().fillna(0.0)                       # rendimento di ogni seduta
    pos = segnale.shift(1, fill_value=False).astype(float)      # il segnale di ieri decide la posizione di oggi
    cambi = pos.diff().abs().fillna(0.0)                        # 1 quando si compra o si vende
    netto = pos * rend - costo * cambi                          # rendimento della seduta, al netto dei costi
    return pd.DataFrame({"pos": pos, "netto": netto, "valore": (1.0 + netto).cumprod()})


def cagr(valore: pd.Series, anni: float) -> float:
    return float(valore.iloc[-1] ** (1.0 / anni) - 1.0)


def perdita_massima(valore: pd.Series) -> float:
    return float((valore / valore.cummax() - 1.0).min())
