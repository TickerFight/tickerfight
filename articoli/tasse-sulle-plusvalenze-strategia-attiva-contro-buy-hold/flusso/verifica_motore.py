"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def uguale(a, b, tol=1e-9, nome=""):
    assert abs(a - b) < tol, f"{nome}: {a} != {b}"
    print(f"ok  {nome}")


anni = np.array([2000] * 10)
# 1. buy & hold sempre investito: imposta solo alla fine, sulla plusvalenza
lr = np.full(10, np.log(1.1) / 10)             # capitale lordo finale 1,1
r = f.simula_fisco(lr, np.ones(10, dtype=int), anni, 0.26)
uguale(r["capitale"], 1.1 - 0.26 * 0.1, nome="buy & hold: imposta alla fine")
# 2. aliquota zero: capitale lordo
r0 = f.simula_fisco(lr, np.ones(10, dtype=int), anni, 0.0)
uguale(r0["capitale"], 1.1, nome="aliquota zero")
# 3. un'uscita con guadagno: imposta subito, poi in liquidità
lr3 = np.array([np.log(1.2), 0.0, np.log(2.0)])
pos3 = np.array([1, 0, 0])
r3 = f.simula_fisco(lr3, pos3, np.array([2000, 2000, 2000]), 0.26)
uguale(r3["capitale"], 1.2 - 0.26 * 0.2, nome="uscita in guadagno, poi liquidità")
# 4. minusvalenza compensa la plusvalenza successiva: perdita di 0,1 poi guadagno
lr4 = np.array([np.log(0.9), 0.0, 0.0, np.log(1.5), 0.0])
pos4 = np.array([1, 0, 0, 1, 0])
r4 = f.simula_fisco(lr4, pos4, np.array([2000, 2000, 2001, 2001, 2001]), 0.26)
# dopo la perdita w = 0.9; rientra a 0.9; sale a 1.35; esce: guadagno 0.45, credito 0.1 -> imposta 0.26*0.35
uguale(r4["capitale"], 1.35 - 0.26 * 0.35, nome="compensazione della minusvalenza")
# 5. credito scaduto: la perdita del 2000 non vale nel 2005
anni5 = np.array([2000, 2000, 2005, 2005, 2005])
r5 = f.simula_fisco(lr4, pos4, anni5, 0.26)
uguale(r5["capitale"], 1.35 - 0.26 * 0.45, nome="credito scaduto dopo il quarto anno")
# 6. costo: un cambio costa lo 0,1% del capitale
r6 = f.simula_fisco(np.array([0.0, 0.0]), np.array([1, 0]), np.array([2000, 2000]), 0.26, costo=0.001)
uguale(r6["capitale"], 1 - 0.001, nome="costo del cambio")
print("Tutti i controlli superati.")
