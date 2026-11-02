"""Funzioni dell'articolo 484: reddito dalle distribuzioni e simulazione del prelievo, con e senza tasse."""
import numpy as np


def componenti_mensili(prezzo_close: np.ndarray, prezzo_adj: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rendimento mensile del solo prezzo (p) e quota di reddito (i), con (1+totale) = (1+p)(1+i). Serie a fine mese, lunghezza T+1."""
    c, a = np.asarray(prezzo_close, float), np.asarray(prezzo_adj, float)
    p = c[1:] / c[:-1] - 1.0
    tot = a[1:] / a[:-1] - 1.0
    i = (1.0 + tot) / (1.0 + p) - 1.0
    return p, np.clip(i, 0.0, None)


def prelievo(p: np.ndarray, i: np.ndarray, capitale: float, rata: float, aliquota: float = 0.0) -> dict:
    """Simula un prelievo mensile fisso `rata`. Ogni mese: il prezzo si muove di p, arriva il reddito i (sul valore a fine mese).
    L'imposta sul reddito è pagata subito. Il reddito netto copre la rata; l'eccesso si reinveste, la mancanza si copre vendendo quote
    (con imposta sulla plusvalenza, base di costo medio). Alla fine il guadagno residuo è tassato. Restituisce capitale netto finale
    (0 se il capitale si esaurisce), totale prelevato ed eventuale mese di esaurimento."""
    P, quote, base = 1.0, capitale, capitale          # prezzo, numero di quote, costo totale
    prelevato = 0.0
    for m in range(len(p)):
        P *= 1.0 + p[m]
        reddito_netto = quote * P * i[m] * (1.0 - aliquota)
        if reddito_netto >= rata:
            extra = reddito_netto - rata
            quote += extra / P
            base += extra
        else:
            manca = rata - reddito_netto
            val = quote * P
            g = max(0.0, 1.0 - base / val) if val > 0 else 0.0
            lordo = manca / (1.0 - aliquota * g)
            if lordo >= val:
                return dict(finale=0.0, prelevato=prelevato + reddito_netto + val * (1 - aliquota * g), esaurito=m + 1)
            frazione = lordo / val
            quote *= 1.0 - frazione
            base *= 1.0 - frazione
        prelevato += rata
    val = quote * P
    tasse_fin = aliquota * max(0.0, val - base)
    return dict(finale=val - tasse_fin, prelevato=prelevato, esaurito=0)
