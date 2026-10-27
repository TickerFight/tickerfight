"""Controlli del motore del piano di accumulo su dati inventati. Se uno fallisce, il flusso si ferma."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

spec = importlib.util.spec_from_file_location("backtest", Path(__file__).resolve().parent / "02_backtest_e_test.py")
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)

ERRORI = []


def controlla(nome: str, condizione: bool) -> None:
    print(("ok    " if condizione else "FALLITO"), nome)
    if not condizione:
        ERRORI.append(nome)


def serie(valori, inizio="2000-01-03"):
    idx = pd.bdate_range(inizio, periods=len(valori))
    return pd.Series(valori, index=idx, dtype=float)


# 1) prezzo costante: tutti i giorni identici, nessuna plusvalenza, nessuna tassa
s = serie(np.full(1200, 100.0))
prezzo, IDX, mesi, ultima = bt.indici_acquisto(s)
q = bt.quote_per_giorno(prezzo[IDX])
v = bt.valore_netto(q, len(mesi), float(prezzo[ultima]))
controlla("prezzo costante: tutti i giorni valgono uguale", np.allclose(v, v[0]))
versato = len(mesi) * config.VERSAMENTO
controlla("prezzo costante: valore finale = versato - commissioni - commissione finale",
          abs(v[0] - (versato - (len(mesi) + 1) * config.COMMISSIONE)) < 1e-6)

# 2) prezzo che sale ogni giorno: comprare prima nel mese è sempre meglio
s = serie(100 * 1.001 ** np.arange(1200))
prezzo, IDX, mesi, ultima = bt.indici_acquisto(s)
v = bt.valore_netto(bt.quote_per_giorno(prezzo[IDX]), len(mesi), float(prezzo[ultima]))
controlla("prezzo crescente: il giorno 1 batte il giorno 28", v[0] > v[-1])
controlla("prezzo crescente: il valore scende (quasi) sempre col giorno", bool(np.all(np.diff(v) <= 1e-9)))

# 3) prezzo che scende: nessuna tassa e il giorno 28 batte il giorno 1
s = serie(100 * 0.999 ** np.arange(1200))
prezzo, IDX, mesi, ultima = bt.indici_acquisto(s)
v = bt.valore_netto(bt.quote_per_giorno(prezzo[IDX]), len(mesi), float(prezzo[ultima]))
controlla("prezzo decrescente: il giorno 28 batte il giorno 1", v[-1] > v[0])
lordo = bt.quote_per_giorno(prezzo[IDX]) * prezzo[ultima] - config.COMMISSIONE
controlla("perdita: nessuna tassa (netto = lordo - commissione finale)", np.allclose(v, lordo))

# 4) tassa su una plusvalenza nota
q = np.array([1.0])
netto = bt.valore_netto(q, 10, 200.0)[0]       # versati 1000, valore 200 -> perdita, nessuna tassa
controlla("tassa: nessuna imposta con perdita", abs(netto - (200.0 - config.COMMISSIONE)) < 1e-9)
q = np.array([20.0])
netto = bt.valore_netto(q, 10, 100.0)[0]       # lordo 2000, versato 1000
atteso = 2000 - config.COMMISSIONE - config.ALIQUOTA * (2000 - 1000 - config.COMMISSIONE)
controlla("tassa: 26% sulla plusvalenza al netto della commissione finale", abs(netto - atteso) < 1e-9)

# 5) scelta della seduta: prima seduta con giorno >= d
s = serie(np.arange(1, 1201, dtype=float))
prezzo, IDX, mesi, ultima = bt.indici_acquisto(s)
giorni_ok = all(s.index[IDX[m, d - 1]].day >= d for m in range(len(mesi)) for d in (1, 15, 28))
controlla("acquisto: la seduta scelta ha giorno >= giorno richiesto", giorni_ok)
dentro = all(s.index[IDX[m, 5]].to_period("M") == mesi[m] for m in range(len(mesi)))
controlla("acquisto: la seduta resta dentro il mese", dentro)
controlla("mesi: il primo mese parziale e l'ultimo in corso sono esclusi",
          mesi[0] > s.index[0].to_period("M") and mesi[-1] < s.index[-1].to_period("M"))

# 6) Holm
ph = bt.holm({"a": 0.01, "b": 0.04, "c": 0.5})
controlla("Holm: valori attesi", abs(ph["a"] - 0.03) < 1e-9 and abs(ph["b"] - 0.08) < 1e-9 and abs(ph["c"] - 0.5) < 1e-9)

if ERRORI:
    raise SystemExit(f"{len(ERRORI)} controlli falliti")
print("Tutti i controlli superati.")
