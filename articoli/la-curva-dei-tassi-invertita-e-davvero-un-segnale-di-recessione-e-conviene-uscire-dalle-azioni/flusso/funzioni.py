"""Funzioni dell'articolo 341: serie mensili, episodi di inversione, strategia, spostamenti circolari."""
import numpy as np
import pandas as pd


def mensile(df: pd.DataFrame) -> pd.DataFrame:
    """Ultima osservazione di ogni mese (fine-mese); i tassi giornalieri mancanti sono portati avanti prima."""
    d = df.sort_index().ffill()
    m = d.resample("ME").last()
    return m.dropna()


def episodi(inv: np.ndarray, min_mesi: int, gap: int) -> list[tuple[int, int]]:
    """Intervalli (inizio, fine) inclusi di mesi invertiti: unisce quelli separati da meno di `gap` mesi, poi scarta quelli con meno di `min_mesi` mesi invertiti."""
    runs, i, n = [], 0, len(inv)
    while i < n:
        if inv[i]:
            j = i
            while j + 1 < n and inv[j + 1]:
                j += 1
            runs.append([i, j])
            i = j + 1
        else:
            i += 1
    uniti: list[list[int]] = []
    for r in runs:
        if uniti and r[0] - uniti[-1][1] - 1 < gap:
            uniti[-1][1] = r[1]
        else:
            uniti.append(r)
    out = []
    for a, b in uniti:
        if int(inv[a:b + 1].sum()) >= min_mesi:
            out.append((a, b))
    return out


def rendimenti_strategia(rend_azioni: np.ndarray, rend_cash: np.ndarray, fuori: np.ndarray) -> np.ndarray:
    """rend_azioni[i] e rend_cash[i]: rendimento del mese i+1; fuori[i]: segnale a fine mese i (True = liquidità nel mese seguente)."""
    return np.where(fuori, rend_cash, rend_azioni)


def cagr(rend: np.ndarray) -> float:
    return float(np.prod(1 + rend) ** (12 / len(rend)) - 1)


def max_drawdown(rend: np.ndarray) -> float:
    c = np.cumprod(1 + rend)
    picco = np.maximum.accumulate(np.concatenate([[1.0], c]))[1:]
    return float((c / picco - 1).min())


def indice_mesi(periodo: str, primo: pd.Timestamp) -> int:
    """Numero di mesi tra il primo mese dei dati e il mese «AAAA-MM»."""
    p = pd.Period(periodo, freq="M")
    return (p - primo.to_period("M")).n
