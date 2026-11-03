"""Lo stesso motore scritto alla vecchia maniera: un ciclo, una seduta alla volta. Serve da prova del nove e da termine di paragone.

Le stesse convenzioni del motore vettoriale: il segnale di ieri decide la posizione di oggi, il costo si paga a ogni cambio.
"""


def backtest_ciclo(chiusure: list[float], segnale: list[bool], costo: float = 0.0) -> list[float]:
    valore, v, prec_pos, prec_close = [], 1.0, 0.0, None
    for t, c in enumerate(chiusure):
        rend = 0.0 if prec_close is None else c / prec_close - 1.0
        pos = float(segnale[t - 1]) if t > 0 else 0.0
        v *= 1.0 + pos * rend - costo * abs(pos - prec_pos)
        valore.append(v)
        prec_pos, prec_close = pos, c
    return valore
