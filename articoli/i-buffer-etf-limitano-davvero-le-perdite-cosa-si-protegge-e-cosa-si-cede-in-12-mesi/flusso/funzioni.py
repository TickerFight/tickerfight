"""Funzioni dell'articolo 482: finestre di 12 mesi per ogni fondo, rendimenti a confronto."""
import numpy as np
import pandas as pd


def primo_giorno(indice: pd.DatetimeIndex, anno: int, mese: int):
    """Primo giorno di borsa dell'anno/mese dati, oppure None se la serie non lo contiene."""
    sel = indice[(indice.year == anno) & (indice.month == mese)]
    return sel[0] if len(sel) else None


def finestre(prezzi: pd.DataFrame, fondi: dict, mesi: int) -> pd.DataFrame:
    """Una riga per ogni fondo e anno di partenza: date, rendimenti del fondo, dell'indice e della liquidità.

    `prezzi` ha le colonne dei fondi, 'SPY' e 'IRX' (% annuo). Sono tenute solo le finestre complete: il fondo ha un prezzo nel primo
    giorno di borsa del mese di partenza e nel primo giorno di borsa dello stesso mese `mesi`/12 anni dopo.
    """
    righe = []
    idx = prezzi.index
    for tk, mese in fondi.items():
        if tk not in prezzi.columns:
            continue
        serie = prezzi[tk].dropna()
        for anno in range(idx[0].year, idx[-1].year + 1):
            a = primo_giorno(idx, anno, mese)
            b = primo_giorno(idx, anno + mesi // 12, mese)
            if a is None or b is None:
                continue
            if a not in serie.index or b not in serie.index:
                continue
            giorni = (b - a).days
            cash = (1 + prezzi.loc[a, "IRX"] / 100) ** (giorni / 365.0) - 1
            righe.append({"fondo": tk, "anno_partenza": anno, "inizio": a, "fine": b, "giorni": giorni,
                          "r_fondo": serie[b] / serie[a] - 1,
                          "r_spy": prezzi.loc[b, "SPY"] / prezzi.loc[a, "SPY"] - 1,
                          "r_cash": cash})
    return pd.DataFrame(righe)


def mix(r_spy: np.ndarray, r_cash: np.ndarray, quota: float) -> np.ndarray:
    """Rendimento di un portafoglio con `quota` in indice e il resto in liquidità, ribilanciato all'inizio del periodo."""
    return quota * r_spy + (1 - quota) * r_cash
