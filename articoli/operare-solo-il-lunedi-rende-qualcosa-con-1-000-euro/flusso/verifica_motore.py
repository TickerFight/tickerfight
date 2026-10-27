"""Controlli del motore sulla regola «un giorno della settimana». Usa SOLO dati inventati: nessun numero qui è un risultato."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

import simulazione as s

spec = importlib.util.spec_from_file_location("bt", Path(__file__).resolve().parent / "02_backtest_e_test.py")
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)
ok = 0


def verifica(nome, cond, det=""):
    global ok
    if not cond:
        raise SystemExit(f"FALLITO: {nome} {det}")
    ok += 1
    print(f"  ok  {nome}")


def uguali(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


idx = pd.bdate_range("2022-03-07", periods=15)          # parte da un lunedì: tre settimane intere
C = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114], float)
d = pd.DataFrame({"Close": C, "fx": 1.0, "segnale": True}, index=idx)
ob = bt.obiettivo(idx, 0)
verifica("il lunedì: si compra alla chiusura del venerdì prima", [bool(ob[i]) for i in range(15)] == [False, False, False, False, True] * 2 + [False] * 5, ob.tolist())
r = s.simula(d, 1, 1000, 0.0, 0.0, 0.0, True, obiettivo=ob)
# acquisti alle sedute 4 e 9 (venerdì), vendite alle 5 e 10 (lunedì successivi)
verifica("ordini: due acquisti e due vendite", (r["n_acquisti"], r["n_vendite"]) == (2, 2), (r["n_acquisti"], r["n_vendite"]))
atteso = 1000 * (105 / 104) * (110 / 109)
verifica("rendimento: solo i due lunedì", uguali(r["valore_finale_eur"], atteso), r["valore_finale_eur"])
verifica("quota investita: due sedute su quattordici", uguali(r["quota_giorni_investito"], 2 / 14), r["quota_giorni_investito"])
# Costi: 4 ordini da 2 euro, prezzi tali che il guadagno lordo sia nullo
d2 = pd.DataFrame({"Close": [100.0] * 15, "fx": 1.0, "segnale": True}, index=idx)
r2 = s.simula(d2, 1, 1000, 2.0, 0.0, 0.26, True, obiettivo=ob)
verifica("prezzi fermi: quattro ordini da 2 euro", uguali(r2["valore_finale_eur"], 992.0) and r2["tasse_eur"] == 0.0, r2["valore_finale_eur"])
# Lunedì festivo: la settimana senza seduta del lunedì non si opera
idx3 = idx.delete(5)                                   # toglie il secondo lunedì
ob3 = bt.obiettivo(idx3, 0)
verifica("lunedì festivo: nessun ordine in quella settimana", int(ob3.sum()) == 1, int(ob3.sum()))
# Scimmie con blocchi da una seduta
rng = np.random.default_rng(2)
for _ in range(30):
    a, b = s.scimmia(40, 40, 400, rng)
    assert len(a) == 40 and ((b - a) == 1).all() and (a[1:] > b[:-1]).all()
verifica("scimmie: blocchi da una seduta senza sovrapposizioni", True)
print(f"Tutti i controlli superati: {ok}")
