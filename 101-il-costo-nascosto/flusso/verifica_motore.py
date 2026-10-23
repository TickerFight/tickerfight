"""Controlli delle funzioni dell'articolo 101 su dati inventati. Se uno fallisce, il flusso si ferma."""
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

# --- Regole: nessun look-ahead ---
for i, (nome, spec) in config.STRATEGIE.items():
    completa = fx.posizione_regola(close, spec)
    tronca = fx.posizione_regola(close.iloc[:800], spec)
    controlla(f"{i}: cambiare il futuro non cambia la posizione passata", np.array_equal(completa.iloc[:800].to_numpy(), tronca.to_numpy()))
    alt = close.copy()
    alt.iloc[900:] *= 3.0
    controlla(f"{i}: la posizione fino al giorno 900 non dipende dai prezzi dopo", np.array_equal(completa.iloc[:901].to_numpy(), fx.posizione_regola(alt, spec).iloc[:901].to_numpy()))
controlla("buy & hold è sempre investito dal secondo giorno", bool((fx.posizione_regola(close, config.STRATEGIE["bh"][1]).iloc[1:] == 1.0).all()))

# --- Rendimenti netti: costo a ogni cambio, ingresso iniziale compreso ---
pos = pd.Series([0, 0, 1, 1, 0, 0], index=close.index[:6], dtype=float)
rend = serie([0, 0, 0.10, 0.10, 0, 0])
rn = fx.rendimenti_netti(rend, pos, 0.01)
controlla("due cambi (entrata e uscita): lordo 0,20 meno 0,02", abs(float(rn.sum()) - 0.18) < 1e-12)
pos1 = pd.Series([1, 1, 1], index=close.index[:3], dtype=float)
controlla("partendo già investiti si paga l'ingresso iniziale", abs(float(fx.rendimenti_netti(serie([0, 0, 0]), pos1, 0.01).sum()) + 0.01) < 1e-12)
controlla("a costo zero il rendimento netto è quello lordo", np.allclose(fx.rendimenti_netti(serie([0.01, -0.02, 0.03]), pos1, 0.0), [0.01, -0.02, 0.03]))
controlla("il costo è proporzionale: il doppio del costo, il doppio della perdita", abs(float(fx.rendimenti_netti(rend, pos, 0.02).sum()) - 0.16) < 1e-12)

# --- Ribilanciamento ---
r = np.array([0.10, 0.0, 0.0])
sen = fx.mix_ribilanciato(r, 0.5, 1, 0.0)
controlla("50/50 senza costi: primo giorno rende metà", abs(sen[0] - 0.05) < 1e-12)
# giorno 1, costo 1%: ingresso 0,5% (costo*quota), poi quota derivata 0,5*1,1/1,05 = 0,5238..., scambio 0,0238...
w1 = 0.5 * 1.1 / 1.05
atteso = (1.05 * (1 - 0.01 * 0.5)) * (1 - 0.01 * abs(w1 - 0.5)) - 1
controlla("50/50 giornaliero con costo, giorno 1 a mano", abs(fx.mix_ribilanciato(r, 0.5, 1, 0.01)[0] - atteso) < 1e-12)
controlla("senza ribilanciamenti nel periodo (ogni 10 sedute su 3) il costo è solo l'ingresso", abs(fx.mix_ribilanciato(r, 0.5, 10, 0.01)[0] - (1.05 * 0.995 - 1)) < 1e-12)
rr = rng.normal(0.0004, 0.01, 2000)
cg = {k: np.sum(np.log1p(fx.mix_ribilanciato(rr, 0.5, k, 0.005))) for k in (1, 21, 252)}
cg0 = {k: np.sum(np.log1p(fx.mix_ribilanciato(rr, 0.5, k, 0.0))) for k in (1, 21, 252)}
controlla("il costo del ribilanciamento cala con la frequenza (giornaliero > mensile > annuale)", (cg0[1] - cg[1]) > (cg0[21] - cg[21]) > (cg0[252] - cg[252]) > 0)
controlla("il costo del ribilanciamento annuale è positivo e sotto lo 0,5% del valore all'anno in questi dati", 0 < (cg0[252] - cg[252]) < 0.005 * 2000 / 252)

# --- Scimmie ---
ps = fx.posizioni_scimmie(400, 5000, 0.10, np.random.default_rng(3))
controlla("scimmie: valori 0/1, partono investite", set(np.unique(ps)) <= {0.0, 1.0} and bool((ps[:, 0] == 1.0).all()))
cambi_medi = np.abs(np.diff(ps, axis=1)).sum(axis=1).mean() / 5000
controlla("scimmie: la frequenza dei cambi è vicina alla probabilità", abs(cambi_medi - 0.10) < 0.01)
rs = fx.rendimenti_scimmie(np.full(5000, 0.0), ps, 0.01)
controlla("scimmie: con rendimenti nulli si perde esattamente il costo dei cambi", abs(rs.sum(axis=1).mean() + 0.01 * (np.abs(np.diff(ps, axis=1, prepend=0)).sum(axis=1).mean())) < 1e-9)

# --- Metriche ---
controlla("rendimento annuo composto a mano", abs(float(fx.cagr(np.array([0.1, -0.1, 0.1]), 2.0)) - (1.089 ** 0.5 - 1)) < 1e-12)
controlla("Sharpe a mano su una serie piccola", abs(float(fx.sharpe(np.array([0.01, -0.01, 0.02, 0.0]))) - np.array([0.01, -0.01, 0.02, 0.0]).mean() / np.array([0.01, -0.01, 0.02, 0.0]).std(ddof=1) * np.sqrt(252)) < 1e-9)
controlla("Kendall di due classifiche uguali = 1 e opposte = -1", abs(fx.kendall([1, 2, 3], [4, 5, 9]) - 1) < 1e-12 and abs(fx.kendall([1, 2, 3], [9, 5, 4]) + 1) < 1e-12)
controlla("posti: il valore più alto è primo", list(fx.posti(np.array([3.0, 1.0, 2.0, 5.0]))) == [2.0, 4.0, 3.0, 1.0])

print(f"{n_ok} controlli superati")
