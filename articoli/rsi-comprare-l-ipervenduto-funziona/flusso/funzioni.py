"""Funzioni di calcolo dell'articolo 146: RSI di Wilder, regola e studio degli eventi."""
import numpy as np


def rsi(close: np.ndarray, n: int = 14) -> np.ndarray:
    """RSI di Wilder: medie esponenziali (alfa = 1/n) di rialzi e ribassi, avviate con la media semplice delle prime n variazioni.
    I primi n elementi sono nan."""
    c = np.asarray(close, float)
    d = np.diff(c)
    up, dn = np.maximum(d, 0.0), np.maximum(-d, 0.0)
    out = np.full(len(c), np.nan)
    if len(d) < n:
        return out
    au, ad = up[:n].mean(), dn[:n].mean()
    out[n] = 100.0 if ad == 0 else 100.0 - 100.0 / (1.0 + au / ad)
    for i in range(n, len(d)):
        au = (au * (n - 1) + up[i]) / n
        ad = (ad * (n - 1) + dn[i]) / n
        out[i + 1] = 100.0 if ad == 0 else 100.0 - 100.0 / (1.0 + au / ad)
    return out


def posizione_regola(r: np.ndarray, entra: float, esce: float) -> np.ndarray:
    """Posizione decisa alla chiusura del giorno t: 1 dopo una chiusura con RSI < entra, resta 1 finché l'RSI non chiude sopra esce."""
    pos = np.zeros(len(r))
    dentro = False
    for t in range(len(r)):
        if np.isnan(r[t]):
            continue
        if not dentro and r[t] < entra:
            dentro = True
        elif dentro and r[t] > esce:
            dentro = False
        pos[t] = 1.0 if dentro else 0.0
    return pos


def rendimenti_regola(rend: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """Rendimento del giorno t = posizione decisa alla chiusura di t-1 per il rendimento di t. rend[0] è nan o 0."""
    p = np.concatenate([[0.0], pos[:-1]])
    return p * rend


def primi_incroci(r: np.ndarray, soglia: float, verso: str) -> np.ndarray:
    """Indici dei giorni in cui l'RSI attraversa la soglia per la prima volta: 'sotto' (ieri >= soglia, oggi < soglia) o 'sopra'."""
    ieri, oggi = r[:-1], r[1:]
    ok = ~np.isnan(ieri) & ~np.isnan(oggi)
    cond = (ieri >= soglia) & (oggi < soglia) if verso == "sotto" else (ieri <= soglia) & (oggi > soglia)
    return np.where(ok & cond)[0] + 1


def rendimenti_avanti(close: np.ndarray, h: int) -> np.ndarray:
    """Rendimento semplice da t a t+h (nan se non c'è)."""
    c = np.asarray(close, float)
    out = np.full(len(c), np.nan)
    out[: len(c) - h] = c[h:] / c[:-h] - 1.0
    return out


def sharpe(x: np.ndarray, ga: int) -> float:
    s = np.std(x, ddof=1)
    return float(np.mean(x) / s * np.sqrt(ga)) if s > 0 else float("nan")


def cagr(x: np.ndarray, ga: int) -> float:
    return float(np.exp(np.mean(np.log1p(x)) * ga) - 1.0)


def sharpe_spostamenti(rend: np.ndarray, pos: np.ndarray, n: int, ga: int, rng: np.random.Generator) -> np.ndarray:
    """Sharpe della stessa posizione ruotata di un numero casuale di giorni, n volte."""
    m = len(pos)
    sh = np.empty(n)
    for k in range(n):
        s = int(rng.integers(1, m))
        sh[k] = sharpe(rendimenti_regola(rend, np.roll(pos, s)), ga)
    return sh


def pval_spostamenti(rend: np.ndarray, pos: np.ndarray, n: int, ga: int, rng: np.random.Generator) -> tuple[float, float]:
    """Quota di spostamenti con Sharpe >= quello osservato (con +1 al numeratore e al denominatore) e Sharpe mediano degli spostamenti."""
    obs = sharpe(rendimenti_regola(rend, pos), ga)
    sh = sharpe_spostamenti(rend, pos, n, ga, rng)
    return float((1 + np.sum(sh >= obs)) / (n + 1)), float(np.median(sh))
