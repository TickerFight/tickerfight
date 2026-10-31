"""Controlli delle funzioni su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import funzioni as fx

n_ok = 0


def controlla(nome: str, condizione: bool) -> None:
    global n_ok
    print(("OK   " if condizione else "FAIL ") + nome)
    if not condizione:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


mesi = pd.period_range("2000-01", periods=36, freq="M")
rng = np.random.default_rng(1)
R = rng.normal(0.006, 0.03, (36, 4))

controlla("peso 1 sul primo asset = quell'asset", np.allclose(fx.portafoglio(R, mesi, [1, 0, 0, 0])[0], R[:, 0]))
controlla("pesi uguali su asset identici = l'asset", np.allclose(fx.portafoglio(np.repeat(R[:, :1], 4, axis=1), mesi, [.25] * 4)[0], R[:, 0]))
Rc = np.zeros((36, 4)); Rc[:, 0] = 0.01
p = fx.portafoglio(Rc, mesi, [.25] * 4)[0]
atteso = 0.25 * 1.01 ** 12 + 0.75
controlla("primo anno: 0,25 x crescita + 0,75", abs(np.prod(1 + p[:12]) - atteso) < 1e-12)
controlla("secondo anno dopo il ribilanciamento: stessa ripartenza", abs(np.prod(1 + p[12:24]) - atteso) < 1e-12)
P = fx.portafoglio(R, mesi, np.array([[1, 0, 0, 0], [0, 1, 0, 0]]))
controlla("due portafogli insieme", np.allclose(P[0], R[:, 0]) and np.allclose(P[1], R[:, 1]))
Wy = np.zeros((1, 3, 4)); Wy[0, 0, 0] = 1; Wy[0, 1, 1] = 1; Wy[0, 2, 2] = 1
pw = fx.portafoglio(R, mesi, Wy)[0]
controlla("un peso per anno", np.allclose(pw[:12], R[:12, 0]) and np.allclose(pw[12:24], R[12:24, 1]) and np.allclose(pw[24:], R[24:, 2]))
controlla("perdita massima: +10% poi -50%", abs(fx.perdita_massima(np.array([0.1, -0.5])) - (-0.5)) < 1e-12)
controlla("perdita massima: solo rialzi = 0", fx.perdita_massima(np.full(10, 0.01)) == 0.0)
controlla("mesi sott'acqua: -10% poi +1% x3 = 4", fx.mesi_sott_acqua(np.array([0.01, -0.10, 0.01, 0.01, 0.01])) == 4)
controlla("mesi sott'acqua: solo rialzi = 0", fx.mesi_sott_acqua(np.full(5, 0.01)) == 0)
e = np.array([0.01, -0.01] * 6)
controlla("Sharpe zero se l'eccesso medio è zero", abs(fx.sharpe(e, np.zeros(12))) < 1e-12)
controlla("CAGR di 1% al mese", abs(fx.cagr(np.full(12, 0.01)) - (1.01 ** 12 - 1)) < 1e-12)
controlla("rendimento anno solare", abs(fx.rendimenti_anno_solare(np.full(24, 0.01), mesi[:24]).iloc[0] - (1.01 ** 12 - 1)) < 1e-12)
ix = fx.indici_blocchi(100, 12, np.random.default_rng(5))
controlla("bootstrap a blocchi: lunghezza e intervallo", len(ix) == 100 and ix.min() >= 0 and ix.max() < 100)
s = pd.Series([1.0, 2.0, 3.0], index=pd.to_datetime(["2000-01-03", "2000-01-31", "2000-02-10"]))
controlla("fine mese: ultimo valore", list(fx.fine_mese(s).values) == [2.0, 3.0])
print(f"{n_ok} controlli superati")
