"""Controlli di motore_drawdown.py su dati inventati: se uno fallisce, il flusso si ferma."""
import numpy as np

import motore_drawdown as md


def ok(cond, msg):
    if not cond:
        raise SystemExit(f"CONTROLLO FALLITO: {msg}")
    print("ok:", msg)


c = np.array([100, 110, 99, 90, 95, 110, 120, 108, 130, 100, 105], dtype=float)
dd = md.serie_drawdown(c)
ok(abs(dd[3] - (90 / 110 - 1)) < 1e-12, "drawdown alla seduta 3 = 90/110 - 1")
ok(dd[1] == 0 and dd[5] == 0 and dd[6] == 0, "sul massimo il drawdown è zero")
e = md.episodi(c)
ok(len(e) == 3, "tre episodi (110->90, 120->108, 130->100 aperto)")
ok(e[0]["i_picco"] == 1 and e[0]["i_minimo"] == 3 and e[0]["i_recupero"] == 5, "primo episodio: picco 1, minimo 3, recupero 5")
ok(abs(e[0]["profondita"] - (1 - 90 / 110)) < 1e-12, "profondità del primo episodio")
ok(e[1]["i_recupero"] == 8, "secondo episodio recuperato alla seduta 8 (130 >= 120)")
ok(e[2]["i_recupero"] is None and e[2]["i_minimo"] == 9, "terzo episodio ancora aperto, minimo alla seduta 9")
ok(len(md.episodi(c, 0.15)) == 2, "con soglia 15% restano gli episodi da 18% e 23%")
ok(len(md.episodi(np.array([1.0, 2.0, 3.0]))) == 0, "serie sempre crescente: nessun episodio")
# recupero uguale al picco conta come recupero
ok(md.episodi(np.array([10.0, 8.0, 10.0]))[0]["i_recupero"] == 2, "tornare esattamente al massimo è recupero")
# a -50% serve +100%
x = np.array([100.0, 50.0, 100.0])
ok(abs(md.episodi(x)[0]["profondita"] - 0.5) < 1e-12, "-50% e poi +100% riporta al massimo")
# correlazione di rango
a = np.array([1, 2, 3, 4, 5.0])
ok(abs(md.rango_spearman(a, a ** 2) - 1) < 1e-12, "Spearman = 1 per relazione monotòna")
ok(abs(md.rango_spearman(a, -a) + 1) < 1e-12, "Spearman = -1 per relazione decrescente")
print("Tutti i controlli superati.")
