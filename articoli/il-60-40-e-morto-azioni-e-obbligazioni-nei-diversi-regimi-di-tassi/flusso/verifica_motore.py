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

# 1-3. Obbligazione sintetica
controlla("tasso fermo: rendimento mensile = tasso/12", abs(fx.rendimento_obbligazione(0.05, 0.05) - 0.05 / 12) < 1e-12)
controlla("tassi in salita: rendimento sotto il carry", fx.rendimento_obbligazione(0.04, 0.05) < 0.04 / 12)
controlla("tassi in discesa: rendimento sopra il carry", fx.rendimento_obbligazione(0.04, 0.03) > 0.04 / 12)
d = (fx.rendimento_obbligazione(0.04, 0.0401) - fx.rendimento_obbligazione(0.04, 0.04)) / 0.0001
controlla("durata: +1 punto base fa perdere circa 8 punti base per ogni punto di tasso", -9.0 < d < -7.0)

# 4-6. Portafoglio
rs = np.random.default_rng(1).normal(0.01, 0.04, 36)
rb = np.random.default_rng(2).normal(0.004, 0.015, 36)
controlla("peso 1 = solo azioni", np.allclose(fx.portafoglio(rs, rb, mesi, 1.0)[0], rs))
controlla("peso 0 = solo obbligazioni", np.allclose(fx.portafoglio(rs, rb, mesi, 0.0)[0], rb))
rc = np.full(36, 0.01)
controlla("stesso rendimento nei due titoli: portafoglio uguale", np.allclose(fx.portafoglio(rc, rc, mesi, 0.6)[0], rc))
rs2, rb2 = np.full(36, 0.01), np.zeros(36)
p = fx.portafoglio(rs2, rb2, mesi, 0.6)[0]
atteso1 = 0.6 * 1.01 ** 12 + 0.4
controlla("primo anno: valore = 0,6 x crescita azioni + 0,4", abs(np.prod(1 + p[:12]) - atteso1) < 1e-12)
controlla("secondo anno dopo ribilanciamento: ripartenza da 60/40", abs(np.prod(1 + p[12:24]) - atteso1) < 1e-12)
pw = fx.portafoglio(rs, rb, mesi, np.array([[0.2, 0.8, 0.5]]))[0]
controlla("un peso per anno: primo anno con peso 0,2", abs(pw[0] - (0.2 * rs[0] + 0.8 * rb[0])) < 1e-12 and abs(pw[12] - (0.8 * rs[12] + 0.2 * rb[12])) < 1e-12)

# 7-10. Statistiche
controlla("perdita massima: +10% poi -50%", abs(fx.perdita_massima(np.array([0.1, -0.5])) - (-0.5)) < 1e-12)
controlla("perdita massima: solo rialzi = 0", fx.perdita_massima(np.full(10, 0.01)) == 0.0)
e = np.array([0.01, -0.01] * 6)
controlla("Sharpe zero se l'eccesso medio è zero", abs(fx.sharpe(e, np.zeros(12))) < 1e-12)
controlla("CAGR di 1% al mese", abs(fx.cagr(np.full(12, 0.01)) - (1.01 ** 12 - 1)) < 1e-12)
controlla("rendimento anno solare", abs(fx.rendimenti_anno_solare(np.full(24, 0.01), mesi[:24]).iloc[0] - (1.01 ** 12 - 1)) < 1e-12)

# 11-13. Regimi, finestre, bootstrap
controlla("regimi", list(fx.regime(np.array([2.0, 3.0, 5.9, 6.0]), 3.0, 6.0)) == ["bassi", "medi", "medi", "alti"])
fm = fx.finestre_mobili(np.full(30, 0.01), 12)
controlla("finestre mobili: numero e valore", len(fm) == 18 and np.allclose(fm, 1.01 ** 12 - 1))
rng = np.random.default_rng(5)
ix = fx.indici_blocchi(100, 12, rng)
controlla("bootstrap a blocchi: lunghezza e intervallo", len(ix) == 100 and ix.min() >= 0 and ix.max() < 100)
s = pd.Series([1.0, 2.0, 3.0], index=pd.to_datetime(["2000-01-03", "2000-01-31", "2000-02-10"]))
controlla("fine mese: ultimo valore", list(fx.fine_mese(s).values) == [2.0, 3.0])
print(f"{n_ok} controlli superati")
