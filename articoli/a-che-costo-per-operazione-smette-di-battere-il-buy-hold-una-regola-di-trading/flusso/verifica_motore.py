"""Controlli delle funzioni dell'articolo 102 su dati inventati. Se uno fallisce, il flusso si ferma."""
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
close = serie(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, 1200))))

for i, (nome, spec) in config.STRATEGIE.items():
    completa = fx.posizione_regola(close, spec)
    alt = close.copy()
    alt.iloc[900:] *= 3.0
    controlla(f"{i}: la posizione fino al giorno 900 non dipende dai prezzi dopo", np.array_equal(completa.iloc[:901].to_numpy(), fx.posizione_regola(alt, spec).iloc[:901].to_numpy()))

pos = pd.Series([0, 0, 1, 1, 0, 0], index=close.index[:6], dtype=float)
rend = serie([0, 0, 0.10, 0.10, 0, 0])
controlla("due cambi: lordo 0,20 meno 0,02", abs(float(fx.rendimenti_netti(rend, pos, 0.01).sum()) - 0.18) < 1e-12)
pos1 = pd.Series([1, 1, 1], index=close.index[:3], dtype=float)
controlla("l'ingresso iniziale si paga", abs(float(fx.rendimenti_netti(serie([0, 0, 0]), pos1, 0.01).sum()) + 0.01) < 1e-12)

# costo di pareggio: funzioni lineari note
c, st = fx.costo_pareggio(lambda c: 1.0 - 100 * c, lambda c: 0.5, 0.05)
controlla("pareggio lineare: 1 - 100c = 0,5 -> c = 0,005", st == "normale" and abs(c - 0.005) < 1e-9)
c, st = fx.costo_pareggio(lambda c: 0.4 - c, lambda c: 0.5, 0.05)
controlla("già sotto a costo zero -> costo 0", st == "gia_sotto" and c == 0.0)
c, st = fx.costo_pareggio(lambda c: 2.0 - c, lambda c: 0.5, 0.05)
controlla("sopra anche al massimo -> oltre", st == "oltre" and c == 0.05)

# pareggio con una regola vera: sul rendimento annuo il pareggio coincide con il costo che azzera la differenza
ret = close.pct_change().fillna(0.0)
p50 = fx.posizione_regola(close, ("sopra_media", 50))
anni = 4.0
f_r = lambda c: float(fx.cagr(fx.rendimenti_netti(ret, p50, c).to_numpy(), anni))
f_b = lambda c: float(fx.cagr(fx.rendimenti_netti(ret, fx.posizione_regola(close, ("bh",)), c).to_numpy(), anni))
c, st = fx.costo_pareggio(f_r, f_b, 0.05)
if st == "normale":
    controlla("al costo di pareggio le due misure coincidono", abs(f_r(c) - f_b(c)) < 1e-9)
else:
    controlla("pareggio: stato valido su dati inventati", st in ("gia_sotto", "oltre"))

controlla("Spearman: ordine opposto = -1", abs(fx.spearman([1, 2, 3, 4], [9, 7, 5, 1]) + 1) < 1e-12)
controlla("Spearman: stesso ordine = 1", abs(fx.spearman([1, 2, 3, 4], [1, 5, 6, 9]) - 1) < 1e-12)
ps = fx.posizioni_scimmie(400, 5000, 0.04, np.random.default_rng(3))
controlla("scimmie: frequenza dei cambi vicina alla probabilità", abs(np.abs(np.diff(ps, axis=1)).sum(axis=1).mean() / 5000 - 0.04) < 0.005)
controlla("Sharpe a mano", abs(float(fx.sharpe(np.array([0.01, -0.01, 0.02, 0.0]))) - np.array([0.01, -0.01, 0.02, 0.0]).mean() / np.array([0.01, -0.01, 0.02, 0.0]).std(ddof=1) * np.sqrt(252)) < 1e-9)
print(f"{n_ok} controlli superati")
