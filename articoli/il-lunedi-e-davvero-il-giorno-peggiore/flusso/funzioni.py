"""Funzioni dell'articolo 506: statistiche per giorno della settimana, test di permutazione, strategia senza lunedì."""
import numpy as np


def medie_per_gruppo(r: np.ndarray, g: np.ndarray, k: int = 5) -> np.ndarray:
    """Media di r per ciascun gruppo 0..k-1 (g: etichetta intera)."""
    somme = np.bincount(g, weights=r, minlength=k)
    conta = np.bincount(g, minlength=k)
    return somme / conta


def p_permutazione(r: np.ndarray, g: np.ndarray, n: int, rng, k: int = 5) -> tuple[float, np.ndarray]:
    """P-value della differenza tra la media massima e minima per gruppo, mescolando le etichette. Restituisce anche la distribuzione simulata."""
    m = medie_per_gruppo(r, g, k)
    oss = float(m.max() - m.min())
    sim = np.empty(n)
    gg = g.copy()
    for i in range(n):
        rng.shuffle(gg)
        mm = medie_per_gruppo(r, gg, k)
        sim[i] = mm.max() - mm.min()
    return float((np.sum(sim >= oss) + 1) / (n + 1)), sim


def costo_pareggio(lr_giorni: np.ndarray) -> float:
    """Costo per operazione che azzera il vantaggio di stare fuori nei giorni `lr_giorni` (log-rendimenti dei giorni saltati).
    Ogni giorno saltato richiede due operazioni (vendere prima, ricomprare dopo). Vale 0 se saltare quei giorni non conviene nemmeno senza costi."""
    n = len(lr_giorni)
    s = float(np.sum(lr_giorni))
    if s >= 0 or n == 0:
        return 0.0
    return float(1.0 - np.exp(s / (2 * n)))
