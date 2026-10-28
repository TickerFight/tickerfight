"""Motore delle regole sul VIX. Funzioni pure su serie di prezzi: nessun accesso a file, nessuna rete.

Regole (da dichiarare nell'articolo):
  - percentile del VIX: quota delle chiusure del VIX, dalla prima disponibile fino al giorno t compreso, che sono
    uguali o inferiori alla chiusura di t (finestra crescente, nessuna informazione futura); definito solo dopo
    `storia_minima` giorni;
  - il segnale si prende all'ultima seduta di ogni mese e resta fermo fino al mese dopo;
  - il segnale della chiusura t è scambiato alla chiusura t+1 e lavora sul rendimento della seduta t+2:
    la posizione che guadagna il rendimento di t è `segnale[t-2]`;
  - regola A: 1 (in azioni) se il percentile è sotto la soglia, 0 (cassa, che non rende) altrimenti;
    regola B: 1 se il percentile è uguale o sopra la soglia, 0 altrimenti;
  - ogni scambio costa `costo_bp` punti base sul valore scambiato; anche l'acquisto iniziale.
"""
import numpy as np
import pandas as pd


def rendimenti(close: pd.Series) -> pd.Series:
    return close.pct_change()


def fine_mese(indice: pd.DatetimeIndex) -> np.ndarray:
    """True nell'ultima seduta di ogni mese; l'ultima riga dei dati non conta (il mese può non essere finito)."""
    mese = indice.year * 12 + indice.month
    return np.asarray(np.r_[mese[1:] != mese[:-1], False])


def percentile_crescente(vix: pd.Series, storia_minima: int) -> pd.Series:
    """Percentile del VIX rispetto alla sua storia fino a oggi (compreso). NaN nei primi `storia_minima` giorni."""
    v = vix.to_numpy(dtype=float)
    out = np.full(len(v), np.nan)
    for i in range(storia_minima - 1, len(v)):
        out[i] = np.mean(v[: i + 1] <= v[i])
    return pd.Series(out, index=vix.index)


def segnale_percentile(pct: pd.Series) -> pd.Series:
    """Percentile preso a fine mese e mantenuto fino al mese successivo."""
    fm = pd.Series(fine_mese(pct.index), index=pct.index)
    return pct.where(fm).ffill()


def regola(pct_ritardato: pd.Series, tipo: str, soglia: float) -> pd.Series:
    if tipo == "A":
        pos = (pct_ritardato < soglia).astype(float)
    elif tipo == "B":
        pos = (pct_ritardato >= soglia).astype(float)
    else:
        raise ValueError(tipo)
    return pos.where(pct_ritardato.notna())


def tabella_base(close: pd.Series, vix: pd.Series, storia_minima: int) -> pd.DataFrame:
    """Per ogni seduta con segnale definito: rendimento, percentile in vigore (segnale di due sedute prima) e periodo mensile."""
    comune = close.index.intersection(vix.index)
    close, vix = close.loc[comune], vix.loc[comune]
    r = rendimenti(close)
    pct = percentile_crescente(vix, storia_minima)
    sig = segnale_percentile(pct)
    pct_in_vigore = sig.shift(2)
    valido = pct_in_vigore.notna() & r.notna()
    primo = np.flatnonzero(valido.to_numpy())
    if len(primo) == 0:
        raise ValueError("nessuna seduta con segnale definito")
    i0 = int(primo[0])
    fm = fine_mese(close.index)
    effettivo = np.r_[False, False, fm[:-2]]          # True nella seduta in cui il nuovo segnale comincia a lavorare
    periodo = np.cumsum(effettivo)
    d = pd.DataFrame({"r": r, "pct": pct_in_vigore, "periodo": periodo}, index=close.index).iloc[i0:]
    return d


def serie_regola(d: pd.DataFrame, tipo: str, soglia: float, costo_bp: float) -> pd.DataFrame:
    pos = regola(d["pct"], tipo, soglia)
    prec = pos.shift(1).fillna(0.0)
    scambio = (pos - prec).abs()
    c = costo_bp / 1e4
    out = d.copy()
    out["peso"] = pos
    out["scambio"] = scambio
    out["strategia"] = pos * d["r"] - c * scambio
    rb = d["r"].copy()
    rb.iloc[0] -= c
    out["buyhold"] = rb
    return out


def mesi(d: pd.DataFrame, giorni_anno: int) -> pd.DataFrame:
    """Un record per periodo mensile: percentile in vigore, rendimento del periodo, volatilità annualizzata, giorni."""
    g = d.groupby("periodo")
    out = pd.DataFrame({
        "pct": g["pct"].first(),
        "rend": g["r"].apply(lambda x: float(np.prod(1 + x) - 1)),
        "vol": g["r"].apply(lambda x: float(x.std(ddof=1) * np.sqrt(giorni_anno)) if len(x) > 2 else np.nan),
        "giorni": g["r"].size(),
    })
    return out.dropna()


def rango(x: np.ndarray) -> np.ndarray:
    return pd.Series(x).rank().to_numpy()


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.corrcoef(rango(x), rango(y))[0, 1])


def spearman_permutazione(x: np.ndarray, y: np.ndarray, n: int, rng) -> tuple[float, float]:
    """Correlazione di rango e p-value a due code con test di permutazione."""
    rx, ry = rango(x), rango(y)
    rho = float(np.corrcoef(rx, ry)[0, 1])
    rxc = (rx - rx.mean()) / rx.std()
    ryc = (ry - ry.mean()) / ry.std()
    perm = rng.permuted(np.tile(ryc, (n, 1)), axis=1)
    rhos = (perm * rxc).mean(axis=1)
    p = (int((np.abs(rhos) >= abs(rho) - 1e-12).sum()) + 1) / (n + 1)
    return rho, p


def quintili(pct: np.ndarray, k: int) -> np.ndarray:
    """Indice del quintile (0..k-1) con soglie fisse sul percentile: [0,0.2), [0.2,0.4), ..."""
    return np.minimum((np.asarray(pct) * k).astype(int), k - 1)


def equity(rend) -> np.ndarray:
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


def sharpe_da_somme(w: np.ndarray, s1: np.ndarray, s2: np.ndarray, n: int, giorni_anno: int) -> np.ndarray:
    """Sharpe lordo di un portafoglio a pesi costanti per periodo (w, s1 = somma r, s2 = somma r^2 per periodo)."""
    media = (w * s1).sum(axis=-1) / n
    m2 = (w ** 2 * s2).sum(axis=-1) / n
    sd = np.sqrt(np.maximum(m2 - media ** 2, 1e-30))
    return media / sd * np.sqrt(giorni_anno)


def bootstrap_dsharpe(rs: np.ndarray, rb: np.ndarray, n_boot: int, blocco: int, giorni_anno: int,
                      rng, a_pezzi: int = 100) -> np.ndarray:
    """Differenza di Sharpe (regola - buy & hold) su ricampionamenti a blocchi circolari, coppie di giorni insieme."""
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


def bootstrap_diff_medie(a: np.ndarray, b: np.ndarray, n_boot: int, rng) -> np.ndarray:
    """Differenza tra la media di a e la media di b, ricampionando separatamente i due gruppi."""
    ia = rng.integers(0, len(a), size=(n_boot, len(a)))
    ib = rng.integers(0, len(b), size=(n_boot, len(b)))
    return a[ia].mean(axis=1) - b[ib].mean(axis=1)
