"""Controlli dei due motori su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import motore_50_righe as m
from motore_ciclo import backtest_ciclo

n_ok = 0


def controlla(nome: str, condizione: bool) -> None:
    global n_ok
    print(("OK   " if condizione else "FAIL ") + nome)
    if not condizione:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


def serie(valori) -> pd.Series:
    return pd.Series(np.asarray(valori, float), index=pd.bdate_range("2020-01-01", periods=len(valori)))


# 1. Crescita costante dell'1% al giorno, sempre investiti dal secondo giorno
c = serie(100 * 1.01 ** np.arange(11))
tutto_vero = pd.Series(True, index=c.index)
bt = m.backtest(c, tutto_vero)
controlla("il primo giorno non si è mai investiti (il segnale è di ieri)", bt["pos"].iloc[0] == 0.0)
controlla("dal secondo giorno si è investiti e il valore cresce dell'1% al giorno", abs(bt["valore"].iloc[-1] - 1.01 ** 10) < 1e-12)

# 2. In cassa il valore resta 1
controlla("in cassa il valore resta 1", (m.backtest(c, ~tutto_vero)["valore"] == 1.0).all())

# 3. Il costo si paga a ogni cambio di posizione
s = pd.Series([True, False, True, False, False, True, False, False, False, False, False], index=c.index)
bt0, bt1 = m.backtest(c, s), m.backtest(c, s, costo=0.01)
n_cambi = int(bt1["pos"].diff().abs().sum())
controlla("il numero di cambi è quello atteso (6)", n_cambi == 6)
controlla("il costo riduce il rendimento di giornata solo nei giorni di cambio",
          bool(((bt0["netto"] - bt1["netto"]).round(12) == (0.01 * bt1["pos"].diff().abs().fillna(0.0)).round(12)).all()))

# 4. Nessun look-ahead: tagliare il futuro non cambia le posizioni passate
rng = np.random.default_rng(6)
close = serie(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 800))))
sig = m.segnale_medie(close, 10, 40)
pieno = m.backtest(close, sig, 0.001)
ok = True
for taglio in (100, 300, 500, 700):
    t = m.backtest(close.iloc[:taglio], m.segnale_medie(close.iloc[:taglio], 10, 40), 0.001)
    ok &= bool(np.allclose(t["valore"].values, pieno["valore"].iloc[:taglio].values, rtol=0, atol=1e-12))
controlla("il valore fino a un giorno non cambia se si taglia il futuro", ok)

# 5. Il motore vettoriale e il ciclo danno lo stesso risultato su tre regole e tre costi
segnali = {"un_giorno": m.segnale_un_giorno(close), "media_20": m.segnale_sopra_media(close, 20), "medie": sig}
for nome, sg in segnali.items():
    for costo in (0.0, 0.001, 0.01):
        a = m.backtest(close, sg, costo)["valore"].to_numpy()
        b = np.array(backtest_ciclo(close.tolist(), sg.tolist(), costo))
        controlla(f"vettoriale e ciclo coincidono: {nome}, costo {costo}", float(np.max(np.abs(a / b - 1.0))) < 1e-9)

# 6. Perdita massima e CAGR
v2 = pd.Series([1.0, 1.2, 0.9, 1.5])
controlla("perdita massima = 0,9/1,2 - 1", abs(m.perdita_massima(v2) - (0.9 / 1.2 - 1)) < 1e-12)
controlla("CAGR su due anni di un raddoppio", abs(m.cagr(pd.Series([1.0, 2.0]), 2.0) - (2 ** 0.5 - 1)) < 1e-12)

# 7. Il segnale medie 50/200 non esiste prima di avere duecento chiusure
s200 = m.segnale_medie(serie(100 + np.arange(300.0)), 50, 200)
controlla("nessun segnale prima di avere la media lenta", not s200.iloc[:199].any())

print(f"\nVerifica del motore: {n_ok} controlli superati.")
