"""Controlli delle funzioni dell'articolo 61 su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import config
import funzioni as fx

n_ok = 0


def controlla(nome: str, condizione: bool) -> None:
    global n_ok
    print(("OK   " if condizione else "FAIL ") + nome)
    if not condizione:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


def serie(valori, inizio="2000-01-03") -> pd.Series:
    return pd.Series(np.asarray(valori, float), index=pd.bdate_range(inizio, periods=len(valori)))


rng = np.random.default_rng(1)
r = rng.normal(0.0004, 0.01, size=(3, 3000))

# --- Metriche ---
controlla("lo Sharpe non cambia se si dimezzano i rendimenti", np.allclose(fx.sharpe(r), fx.sharpe(r * 0.5)))
controlla("il Sortino non cambia se si dimezzano i rendimenti", np.allclose(fx.sortino(r), fx.sortino(r * 0.5)))
y = np.array([0.01, -0.01, 0.02, 0.0])
controlla("Sharpe a mano su una serie piccola", abs(float(fx.sharpe(y)) - y.mean() / y.std(ddof=1) * np.sqrt(252)) < 1e-9)
x = np.array([0.02, -0.01, 0.03, -0.02])
dd = np.sqrt(np.mean(np.minimum(x, 0) ** 2))
controlla("Sortino a mano: media / radice della media dei quadrati delle perdite", abs(float(fx.sortino(x)) - x.mean() / dd * np.sqrt(252)) < 1e-9)
controlla("Sortino non definito se non ci sono mai perdite", np.isnan(fx.sortino(np.array([0.01, 0.02, 0.0]))))
controlla("Sharpe non definito con rischio zero", np.isnan(fx.sharpe(np.array([0.0, 0.0, 0.0]))))
p = np.array([0.0, 1.0, -0.5, 0.0])        # valore: 1 -> 2 -> 1 -> 1 : perdita massima -50%
controlla("perdita massima: da 2 a 1 vale -50%", abs(float(fx.perdita_massima(p)) + 0.5) < 1e-12)
controlla("perdita massima nulla se il valore sale sempre", float(fx.perdita_massima(np.array([0.01, 0.01]))) == 0.0)
controlla("Calmar non definito senza perdite", np.isnan(fx.calmar(np.array([0.01, 0.01]), 1.0)))
q = np.array([0.1, -0.1, 0.1])             # valore finale 1,1*0,9*1,1 = 1,089 in 2 anni; perdita massima -10%
controlla("rendimento annuo composto a mano", abs(float(fx.cagr(q, 2.0)) - (1.089 ** 0.5 - 1)) < 1e-12)
controlla("Calmar a mano", abs(float(fx.calmar(q, 2.0)) - (1.089 ** 0.5 - 1) / 0.1) < 1e-12)

# --- Classifiche e correlazioni di rango ---
a = np.array([3.0, 1.0, 2.0, 5.0])
controlla("posti: il valore più alto è primo", list(fx.posti(a)) == [2.0, 4.0, 3.0, 1.0])
controlla("posti: parità = posto medio", list(fx.posti([1.0, 1.0, 3.0])) == [2.5, 2.5, 1.0])
controlla("posti: non definito = ultimo", list(fx.posti([1.0, np.nan, 3.0])) == [2.0, 3.0, 1.0])
controlla("Spearman di due classifiche uguali = 1", abs(fx.spearman(a, a * 2) - 1) < 1e-12)
controlla("Spearman di due classifiche opposte = -1", abs(fx.spearman(a, -a) + 1) < 1e-12)
controlla("Kendall di due classifiche uguali = 1", abs(fx.kendall(a, a ** 2) - 1) < 1e-12)
controlla("Kendall di due classifiche opposte = -1", abs(fx.kendall(a, -a) + 1) < 1e-12)
controlla("Kendall a mano: [1,2,3] contro [1,3,2] = 1/3", abs(fx.kendall([1, 2, 3], [1, 3, 2]) - 1 / 3) < 1e-12)
controlla("vincitore ignora i non definiti", fx.vincitore([np.nan, 1.0, 2.0]) == 2)

# --- Regole: nessun look-ahead ---
close = serie(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, 1200))))
for i, (nome, spec) in config.STRATEGIE.items():
    completa = fx.posizione_regola(close, spec)
    tronca = fx.posizione_regola(close.iloc[:800], spec)
    controlla(f"{i}: cambiare il futuro non cambia la posizione passata", np.array_equal(completa.iloc[:800].to_numpy(), tronca.to_numpy()))
    alt = close.copy()
    alt.iloc[900:] *= 3.0
    controlla(f"{i}: la posizione fino al giorno 900 non dipende dai prezzi dopo", np.array_equal(completa.iloc[:901].to_numpy(), fx.posizione_regola(alt, spec).iloc[:901].to_numpy()))
controlla("buy & hold è sempre investito dal secondo giorno", bool((fx.posizione_regola(close, config.STRATEGIE["bh"][1]).iloc[1:] == 1.0).all()))
controlla("la regola a 200 giorni è in cassa nei primi 200 giorni", bool((fx.posizione_regola(close, config.STRATEGIE["sma200"][1]).iloc[:200] == 0.0).all()))
controlla("la quota dimezzata vale sempre 0,5", bool((fx.posizione_regola(close, config.META) == 0.5).all()))

# --- Rendimenti netti ---
pos = pd.Series([0, 0, 1, 1, 0, 0], index=close.index[:6], dtype=float)
cl = serie([100, 100, 110, 121, 121, 121])
rn = fx.rendimenti_netti(cl, pos, 0.01)
controlla("il costo si paga a ogni cambio di quota (due cambi): lordo 0,20 meno 0,02", abs(float(rn.sum()) - 0.18) < 1e-12)
controlla("buy & hold dimezzato rende metà del rendimento giornaliero", np.allclose(fx.rendimenti_netti(close, fx.posizione_regola(close, config.META), 0.0).iloc[1:], 0.5 * close.pct_change().iloc[1:]))

# --- Blocchi, bootstrap, scimmie ---
controlla("blocchi non sovrapposti dentro i dati", fx.blocchi(10, 3) == [(0, 3), (3, 6), (6, 9)])
idx = fx.indici_blocchi_circolari(100, 21, 50, np.random.default_rng(2))
controlla("bootstrap: forma e intervallo degli indici", idx.shape == (50, 100) and idx.min() >= 0 and idx.max() < 100)
controlla("bootstrap: dentro un blocco gli indici sono consecutivi (circolari)", bool((np.diff(idx[:, :21], axis=1) % 100 == 1).all()))
pi = np.array([1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0], dtype=bool)
val, lun = fx.sequenze(pi)
controlla("sequenze: valori e lunghezze", list(val) == [True, False, True, False, True, False] and list(lun) == [2, 3, 1, 1, 3, 2])
ok = True
for s in range(200):
    sc = fx.scimmia(val, lun, np.random.default_rng(s))
    ok &= len(sc) == len(pi) and sc.sum() == pi.sum() and (np.diff(sc.astype(int)) != 0).sum() == (np.diff(pi.astype(int)) != 0).sum() and sc[0] == pi[0]
controlla("scimmie: stessa lunghezza, stesso tempo investito, stessi cambi, stesso stato iniziale", bool(ok))
diverse = {tuple(fx.scimmia(val, lun, np.random.default_rng(s))) for s in range(200)}
controlla("scimmie: le sequenze rimescolate non sono tutte uguali", len(diverse) > 1)

print(f"{n_ok} controlli superati")
