"""Funzioni dell'articolo 243: episodi di VIX sopra soglia, rendimenti a orizzonti fissi, scimmie."""
import numpy as np


def episodi(vix: np.ndarray, soglia: float, quiete: int) -> np.ndarray:
    """Posizioni (nel vettore del VIX) della prima chiusura sopra la soglia dopo almeno `quiete` chiusure consecutive non sopra."""
    sopra = vix > soglia
    out = []
    for i in range(quiete, len(vix)):
        if sopra[i] and not sopra[i - quiete:i].any():
            out.append(i)
    return np.array(out, dtype=int)


def rendimenti_forward(c: np.ndarray, entrate: np.ndarray, h: int) -> np.ndarray:
    """Rendimento da chiusura a chiusura da ciascuna entrata a h sedute dopo; le entrate senza h sedute davanti sono escluse."""
    e = entrate[entrate + h < len(c)]
    return c[e + h] / c[e] - 1.0


def minimo_successivo(c: np.ndarray, entrate: np.ndarray, h: int) -> np.ndarray:
    """Per ciascuna entrata: peggior chiusura nelle h sedute successive, rispetto al prezzo d'entrata (meno uno)."""
    e = entrate[entrate + h < len(c)]
    return np.array([c[x + 1:x + h + 1].min() / c[x] - 1.0 for x in e])


def entrate_generiche(n: int, h: int, prima: int) -> np.ndarray:
    """Tutte le possibili entrate con h sedute davanti, a partire da `prima`."""
    return np.arange(prima, n - h)


def scimmie_medie(c: np.ndarray, validi: np.ndarray, k: int, h: int, n_scimmie: int, rng) -> np.ndarray:
    """Rendimento medio a h sedute di k entrate scelte a caso (senza ripetizioni) tra le entrate `validi`."""
    r = c[validi + h] / c[validi] - 1.0
    out = np.empty(n_scimmie)
    for j in range(n_scimmie):
        out[j] = r[rng.choice(len(r), size=k, replace=False)].mean()
    return out
