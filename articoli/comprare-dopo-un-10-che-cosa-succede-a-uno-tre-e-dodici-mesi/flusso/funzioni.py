"""Funzioni di calcolo dell'articolo 151: eventi di calo rapido e rendimenti successivi."""
import numpy as np


def eventi_calo(close: np.ndarray, finestra: int, soglia: float, pausa: int) -> np.ndarray:
    """Indici dei giorni in cui la chiusura è almeno `soglia` sotto il massimo delle `finestra` chiusure precedenti.
    Dopo un evento se ne ignorano altri per `pausa` sedute."""
    c = np.asarray(close, float)
    ev = []
    ultimo = -10**9
    for t in range(finestra, len(c)):
        if t - ultimo < pausa:
            continue
        if c[t] <= (1 - soglia) * c[t - finestra:t].max():
            ev.append(t)
            ultimo = t
    return np.array(ev, int)


def rend_avanti(close: np.ndarray, h: int) -> np.ndarray:
    """Rendimento semplice da t a t+h; nan dove non esiste."""
    c = np.asarray(close, float)
    out = np.full(len(c), np.nan)
    out[: len(c) - h] = c[h:] / c[:-h] - 1.0
    return out


def minimo_avanti(close: np.ndarray, h: int) -> np.ndarray:
    """Variazione minima della chiusura nei `h` giorni successivi rispetto alla chiusura di t (<= 0 se scende; nan se mancano giorni)."""
    c = np.asarray(close, float)
    out = np.full(len(c), np.nan)
    for t in range(len(c) - h):
        out[t] = c[t + 1:t + h + 1].min() / c[t] - 1.0
    return out


def pval_casuali(valori: np.ndarray, osservato: float, n_eventi: int, n: int, rng: np.random.Generator) -> float:
    """Quota di estrazioni casuali di `n_eventi` giorni (senza pausa) con rendimento medio >= osservato (con +1)."""
    v = valori[~np.isnan(valori)]
    cont = 0
    for _ in range(n):
        if v[rng.integers(0, len(v), n_eventi)].mean() >= osservato:
            cont += 1
    return float((1 + cont) / (n + 1))
