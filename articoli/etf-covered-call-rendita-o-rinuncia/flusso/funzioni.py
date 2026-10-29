"""Funzioni dell'articolo 483: cattura dei mesi di rialzo e di ribasso, portafoglio con la stessa volatilità."""
import numpy as np


def cattura(r_fondo: np.ndarray, r_indice: np.ndarray) -> tuple[float, float]:
    """Cattura dei mesi di rialzo e di ribasso: rendimento medio del fondo diviso quello dell'indice, nei mesi in cui l'indice sale e in cui scende."""
    r_fondo, r_indice = np.asarray(r_fondo, float), np.asarray(r_indice, float)
    su, giu = r_indice > 0, r_indice < 0
    return float(r_fondo[su].mean() / r_indice[su].mean()), float(r_fondo[giu].mean() / r_indice[giu].mean())


def miscela(r_indice: np.ndarray, r_liquidita: np.ndarray, w: float) -> np.ndarray:
    """Rendimenti giornalieri di un portafoglio con peso w nell'indice e 1 - w in liquidità, ribilanciato ogni giorno."""
    return w * np.asarray(r_indice, float) + (1.0 - w) * np.asarray(r_liquidita, float)


def peso_stessa_volatilita(r_indice: np.ndarray, r_liquidita: np.ndarray, vol_obiettivo: float, ga: int) -> float:
    """Peso dell'indice che dà alla miscela la volatilità annua `vol_obiettivo` (bisezione tra 0 e 1; se non raggiungibile, l'estremo)."""
    def vol(w):
        return float(np.std(miscela(r_indice, r_liquidita, w), ddof=1) * np.sqrt(ga))
    lo, hi = 0.0, 1.0
    if vol(hi) <= vol_obiettivo:
        return 1.0
    if vol(lo) >= vol_obiettivo:
        return 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if vol(mid) < vol_obiettivo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2
