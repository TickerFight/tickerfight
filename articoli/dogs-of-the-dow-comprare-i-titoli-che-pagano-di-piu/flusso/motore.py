"""Funzioni di calcolo dell'articolo 282: metriche, bootstrap, Dogs of the Dow e scimmie annuali.

Nessuna strategia di trading: sono confronti tra buy & hold. Le funzioni sono pure, così verifica_motore.py
le controlla su dati inventati con risultati calcolabili a mano.
"""
import numpy as np
import pandas as pd


def equity(r) -> np.ndarray:
    return np.cumprod(1.0 + np.asarray(r, dtype=float))


def cagr(r, ga: int) -> float:
    r = np.asarray(r, dtype=float)
    return float(np.prod(1.0 + r) ** (ga / len(r)) - 1.0)


def vol(r, ga: int) -> float:
    return float(np.std(np.asarray(r, dtype=float), ddof=1) * np.sqrt(ga))


def sharpe(r, ga: int) -> float:
    r = np.asarray(r, dtype=float)
    return float(np.mean(r) / np.std(r, ddof=1) * np.sqrt(ga))


def max_dd(r) -> float:
    e = equity(r)
    picco = np.maximum.accumulate(np.concatenate([[1.0], e]))[1:]
    return float(np.min(e / picco - 1.0))


def fine_mese(indice: pd.DatetimeIndex) -> np.ndarray:
    """Posizioni dell'ultima seduta di ogni mese (escluso l'ultimo mese se incompleto non è controllato: si usa quanto c'è)."""
    s = pd.Series(np.arange(len(indice)), index=indice)
    return s.groupby([indice.year, indice.month]).last().to_numpy()


def rendimento_finestre(cum: np.ndarray, fini: np.ndarray, lung: int) -> tuple[np.ndarray, np.ndarray]:
    """Rendimento totale delle ultime `lung` sedute alla fine di ogni mese utile. cum: (T, k). Restituisce (posizioni, matrice)."""
    ok = fini[fini >= lung]
    base = np.concatenate([np.ones((1, cum.shape[1])), cum], axis=0)   # base[i] = valore prima della seduta i
    return ok, cum[ok] / base[ok - lung + 1] - 1.0


def quote_vincitrici(rend: np.ndarray) -> np.ndarray:
    """Quota di finestre in cui ciascuna colonna ha il rendimento più alto."""
    v = np.argmax(rend, axis=1)
    return np.bincount(v, minlength=rend.shape[1]) / len(v)


def persistenza(cum: np.ndarray, fini: np.ndarray, lung: int) -> tuple[np.ndarray, np.ndarray]:
    """Per ogni mese t con `lung` sedute prima e dopo: area vincitrice nel passato (usa solo dati fino a t) e nel futuro."""
    base = np.concatenate([np.ones((1, cum.shape[1])), cum], axis=0)
    passato, futuro = [], []
    for e in fini:
        if e - lung + 1 < 0 or e + lung >= len(cum):
            continue
        passato.append(int(np.argmax(cum[e] / base[e - lung + 1])))
        futuro.append(int(np.argmax(cum[e + lung] / cum[e])))
    return np.array(passato), np.array(futuro)


def p_permutazione(passato: np.ndarray, futuro: np.ndarray, n: int, rng) -> tuple[float, float]:
    """Quota di coincidenze osservata e p-value: frazione di permutazioni del futuro con almeno altrettante coincidenze."""
    oss = float(np.mean(passato == futuro))
    sup = 0
    for _ in range(n):
        if np.mean(passato == rng.permutation(futuro)) >= oss - 1e-12:
            sup += 1
    return oss, (sup + 1) / (n + 1)


def volatilita_mobile(r: pd.Series, finestra: int, ga: int) -> pd.Series:
    return r.rolling(finestra).std(ddof=1) * np.sqrt(ga)


def correlazione_mobile(a: pd.Series, b: pd.Series, finestra: int) -> pd.Series:
    return a.rolling(finestra).corr(b)


def bootstrap_diff_sharpe(ra, rb, n: int, blocco: int, ga: int, rng) -> np.ndarray:
    """Differenza di Sharpe (a - b) ricampionando a blocchi le stesse date per entrambe le serie."""
    ra, rb = np.asarray(ra, dtype=float), np.asarray(rb, dtype=float)
    T = len(ra)
    nb = int(np.ceil(T / blocco))
    out = np.empty(n)
    for i in range(n):
        inizi = rng.integers(0, T - blocco + 1, size=nb)
        idx = (inizi[:, None] + np.arange(blocco)[None, :]).ravel()[:T]
        out[i] = sharpe(ra[idx], ga) - sharpe(rb[idx], ga)
    return out


def rendimenti_mensili(r: np.ndarray, fini: np.ndarray) -> np.ndarray:
    """Rendimenti composti per mese: r (T, k); i mesi sono i tratti che finiscono nelle posizioni `fini`."""
    e = np.vstack([np.ones((1, r.shape[1])), np.cumprod(1.0 + r, axis=0)])
    estremi = np.concatenate([[0], fini + 1])
    if estremi[-1] != len(r):            # coda: ultimo mese incompleto, si include
        estremi = np.concatenate([estremi, [len(r)]])
    return e[estremi[1:]] / e[estremi[:-1]] - 1.0


def scimmie_valore_finale(mensili: np.ndarray, n: int, rng) -> np.ndarray:
    """Valore finale di 1 per n scimmie che scelgono a caso l'area (colonna) ogni mese."""
    M, k = mensili.shape
    scelta = rng.integers(0, k, size=(n, M))
    return np.prod(1.0 + mensili[np.arange(M)[None, :], scelta], axis=1)


# --- Dogs of the Dow --------------------------------------------------------------------------------------------------
def rendimento_da_dividendo(div_anno: np.ndarray, chiusura: np.ndarray) -> np.ndarray:
    """Dividendi pagati nell'anno diviso il prezzo di chiusura dell'ultimo giorno dell'anno."""
    return np.asarray(div_anno, dtype=float) / np.asarray(chiusura, dtype=float)


def scegli_alti(rend_div: np.ndarray, disponibili: np.ndarray, k: int, bassi: bool = False) -> np.ndarray:
    """Posizioni dei k titoli disponibili con rendimento da dividendo più alto (o più basso). Parità: ordine di posizione."""
    pos = np.flatnonzero(disponibili)
    ordine = np.argsort(rend_div[pos] if bassi else -rend_div[pos], kind="stable")
    return pos[ordine[:k]]


def rendimenti_giornalieri_pesi_uguali(prezzi: np.ndarray) -> np.ndarray:
    """prezzi: (T+1, n) con la riga 0 = giorno di acquisto. Pesi uguali all'acquisto, poi buy & hold: restituisce T rendimenti giornalieri."""
    valore = (prezzi / prezzi[0]).mean(axis=1)
    return valore[1:] / valore[:-1] - 1.0


def scimmie_annuali(rend_annui: np.ndarray, disponibili: np.ndarray, k: int, n: int, rng) -> np.ndarray:
    """rend_annui (anni, titoli), disponibili (anni, titoli) booleana: valore finale di 1 per n scimmie che ogni anno estraggono k titoli a caso."""
    A = rend_annui.shape[0]
    fin = np.ones(n)
    for a in range(A):
        pos = np.flatnonzero(disponibili[a])
        casuali = rng.random((n, len(pos)))
        scelti = np.argpartition(casuali, k - 1, axis=1)[:, :k]
        fin *= 1.0 + rend_annui[a, pos][scelti].mean(axis=1)
    return fin
