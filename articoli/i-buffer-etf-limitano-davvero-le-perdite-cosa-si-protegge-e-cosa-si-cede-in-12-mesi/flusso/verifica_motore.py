"""Controlli delle funzioni su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import funzioni as fx

n_ok = 0


def controlla(nome, cond):
    global n_ok
    print(("OK   " if cond else "FAIL ") + nome)
    if not cond:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


idx = pd.bdate_range("2019-01-01", "2021-03-31")
n = len(idx)
spy = pd.Series(100.0 * 1.001 ** np.arange(n), index=idx)
fondo = pd.Series(50.0 * 1.0005 ** np.arange(n), index=idx)
df = pd.DataFrame({"SPY": spy, "FJAN": fondo, "IRX": 2.0}, index=idx)
w = fx.finestre(df, {"FJAN": 1, "FJUL": 7}, 12)
controlla("finestre: un fondo assente è ignorato", set(w["fondo"]) == {"FJAN"})
controlla("finestre: solo finestre complete (gennaio 2019 e gennaio 2020)", list(w["anno_partenza"]) == [2019, 2020])
a, b = w.loc[0, "inizio"], w.loc[0, "fine"]
controlla("finestre: date al primo giorno di borsa di gennaio", a == pd.Timestamp("2019-01-01") and b == pd.Timestamp("2020-01-01"))
controlla("finestre: rendimento del fondo", abs(w.loc[0, "r_fondo"] - (fondo[b] / fondo[a] - 1)) < 1e-12)
controlla("finestre: liquidità al 2% annuo su un anno", abs(w.loc[0, "r_cash"] - 0.02) < 5e-4)
controlla("mix: tutto indice", np.allclose(fx.mix(np.array([0.1]), np.array([0.02]), 1.0), 0.1))
controlla("mix: 80/20", np.allclose(fx.mix(np.array([0.1]), np.array([0.02]), 0.8), 0.084))
print(f"{n_ok} controlli superati")
