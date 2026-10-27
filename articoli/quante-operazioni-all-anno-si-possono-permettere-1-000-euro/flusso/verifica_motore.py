"""Controlli del motore sulla regola a cicli. Usa SOLO dati inventati: nessun numero qui è un risultato."""
import numpy as np
import pandas as pd

import simulazione as s

ok = 0


def verifica(nome, cond, det=""):
    global ok
    if not cond:
        raise SystemExit(f"FALLITO: {nome} {det}")
    ok += 1
    print(f"  ok  {nome}")


def uguali(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def serie(chiusure, fx=1.0):
    return pd.DataFrame({"Close": np.array(chiusure, float), "fx": fx, "segnale": True},
                        index=pd.bdate_range("2022-03-01", periods=len(chiusure)))


def agenda(n, i0, L):
    return np.array([(i - i0) % L != L - 1 for i in range(n)])


print("Regola a cicli")
d = serie([100.0] * 12)
ob = agenda(12, 1, 4)           # sedute 1,2,3 dentro, 4 fuori, 5,6,7 dentro, 8 fuori, 9,10,11 dentro
r = s.simula(d, 1, 1000, 2.0, 0.0, 0.26, True, obiettivo=ob)
verifica("ordini: 3 acquisti e 3 vendite (compresa la liquidazione finale)", (r["n_acquisti"], r["n_vendite"]) == (3, 3), (r["n_acquisti"], r["n_vendite"]))
verifica("prezzi fermi: ogni ordine costa 2 euro e la cassa cala di 12 euro", uguali(r["valore_finale_eur"], 988.0) and uguali(r["commissioni_eur"], 12.0), r["valore_finale_eur"])
verifica("nessuna tassa se non ci sono plusvalenze", r["tasse_eur"] == 0.0)
verifica("quota di sedute investite", uguali(r["quota_giorni_investito"], 9 / 11), r["quota_giorni_investito"])

# Prezzo che sale del 10% tra l'acquisto e la prima vendita, poi fermo: 1.000 -> 998 investiti -> 1.097,8 -> 1.095,8 netti
d = serie([100, 100, 100, 110, 110, 110, 110, 110, 110])
ob = np.array([1, 1, 1, 0, 1, 1, 1, 1, 1], bool)
r = s.simula(d, 1, 1000, 2.0, 0.0, 0.26, True, obiettivo=ob)
az = 998 / 100
inc = az * 110 - 2
tassa = 0.26 * (inc - 1000)
verifica("prima plusvalenza tassata alla vendita del ciclo", uguali(r["operazioni"][1]["tassa_eur"], tassa), r["operazioni"][1]["tassa_eur"])

# Nessun look-ahead: l'agenda dipende solo dall'indice, cambiare i prezzi futuri non cambia gli ordini già dati
a = serie(list(np.linspace(100, 120, 30)))
b = a.copy(); b.loc[b.index[20:], "Close"] *= 0.5
ob = agenda(30, 1, 5)
ra = s.simula(a, 1, 1000, 2.0, 0.0, 0.26, True, obiettivo=ob)
rb = s.simula(b, 1, 1000, 2.0, 0.0, 0.26, True, obiettivo=ob)
ia = [(o["i"], o["lato"]) for o in ra["operazioni"] if o["i"] < 20]
ib = [(o["i"], o["lato"]) for o in rb["operazioni"] if o["i"] < 20]
verifica("nessun look-ahead", ia == ib)

# Coerenza con il contabile delle scimmie: stessi blocchi, stesso valore finale
rng = np.random.default_rng(1)
C = 100 * np.cumprod(1 + rng.normal(0.0004, 0.01, 400)); d = serie(C)
ob = agenda(400, 1, 10)
r = s.simula(d, 1, 1000, 2.0, 0.001, 0.26, True, obiettivo=ob)
ia, ib = s.blocchi(r)
fin = s.valuta_blocchi(C, np.ones(400), d.index.year.to_numpy(), ia, ib, 1000, 2.0, 0.001, 0.26)[0]
verifica("motore completo e contabile delle scimmie coincidono", uguali(fin, r["valore_finale_eur"]), (fin, r["valore_finale_eur"]))
for _ in range(50):
    k, D = 7, 120
    x, y = s.scimmia(k, D, 400, rng)
    assert len(x) == k and (y - x).sum() == D and (x[1:] > y[:-1]).all() and x[0] >= 0 and y[-1] < 400
verifica("scimmie: k periodi, durata totale D, senza sovrapposizioni", True)
print(f"Tutti i controlli superati: {ok}")
