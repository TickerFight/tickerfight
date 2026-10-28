"""Controlli del motore. Usa SOLO dati inventati: nessun numero qui è un risultato."""
import numpy as np
import pandas as pd

import motore as m

ok = 0


def verifica(nome, cond, dett=""):
    global ok
    if not cond:
        raise SystemExit(f"FALLITO: {nome} {dett}")
    ok += 1
    print(f"  ok  {nome}")


def serie(rend, inizio="2020-01-01"):
    idx = pd.bdate_range(inizio, periods=len(rend))
    return pd.Series(100.0 * np.cumprod(1 + np.asarray(rend, dtype=float)), index=idx)


rng = np.random.default_rng(3)
print("1. Percentile")
v = pd.Series([10.0, 20.0, 15.0, 30.0, 5.0, 25.0], index=pd.bdate_range("2020-01-01", periods=6))
p = m.percentile_crescente(v, 3)
verifica("primi giorni non definiti", p.iloc[:2].isna().all())
verifica("percentile del terzo giorno (15 su 10,20,15 = 2/3)", abs(p.iloc[2] - 2 / 3) < 1e-12)
verifica("massimo storico ha percentile 1", abs(p.iloc[3] - 1.0) < 1e-12)
verifica("minimo storico: 1/5", abs(p.iloc[4] - 1 / 5) < 1e-12)
v2 = v.copy(); v2.iloc[5] = 1000.0
verifica("cambiare il futuro non cambia il passato", np.allclose(m.percentile_crescente(v2, 3).iloc[:5].fillna(-1), p.iloc[:5].fillna(-1)))

print("2. Regole e costi")
n = 900
close = serie(rng.normal(0.0004, 0.01, n))
vix = pd.Series(15 + 10 * np.abs(np.sin(np.arange(n) / 40.0)) + rng.normal(0, 1, n), index=close.index)
d = m.tabella_base(close, vix, 100)
a = m.serie_regola(d, "A", 0.8, 0.0)
b = m.serie_regola(d, "B", 0.8, 0.0)
verifica("A e B complementari con la stessa soglia", np.allclose(a["peso"] + b["peso"], 1.0))
verifica("senza costi: rendimento = peso * indice", np.allclose(a["strategia"], a["peso"] * a["r"]))
a1 = m.serie_regola(d, "A", 0.8, 10.0)
verifica("costo totale = 10 punti base * scambi", abs((a["strategia"] - a1["strategia"]).sum() - 0.001 * a["scambio"].sum()) < 1e-12)
verifica("buy & hold paga solo l'acquisto iniziale", abs((a["buyhold"] - a1["buyhold"]).sum() - 0.001) < 1e-12)

print("3. Nessun look-ahead")
close2 = close.copy(); close2.iloc[-50:] *= 3
vix2 = vix.copy(); vix2.iloc[-50:] *= 3
d2 = m.tabella_base(close2, vix2, 100)
k = len(d) - 60
verifica("cambiare gli ultimi 50 giorni non cambia le posizioni precedenti",
         np.allclose(m.serie_regola(d, "A", 0.8, 0)["peso"].iloc[:k], m.serie_regola(d2, "A", 0.8, 0)["peso"].iloc[:k]))
fm = m.fine_mese(close.index)
primo_giorno = d.index[0]
verifica("la posizione inizia almeno due sedute dopo un fine mese",
         close.index.get_loc(primo_giorno) >= 2 and fm[close.index.get_loc(primo_giorno) - 2])

print("4. Statistiche")
x = rng.normal(size=300); y = x + rng.normal(size=300)
rho, pv = m.spearman_permutazione(x, y, 2000, rng)
verifica("correlazione positiva e p-value piccolo su dati legati", rho > 0.5 and pv < 0.01, (rho, pv))
rho0, pv0 = m.spearman_permutazione(x, rng.normal(size=300), 2000, rng)
verifica("p-value non piccolo su dati indipendenti", pv0 > 0.01, (rho0, pv0))
verifica("quintili", list(m.quintili(np.array([0.0, 0.19, 0.2, 0.99, 1.0]), 5)) == [0, 0, 1, 4, 4])
ms = m.mesi(d, 252)
verifica("giorni dei mesi sommano alle sedute", ms["giorni"].sum() <= len(d) and ms["giorni"].sum() >= len(d) - 25)
g = d.groupby("periodo")
s1 = g["r"].sum().to_numpy(); s2 = g["r"].apply(lambda z: (z ** 2).sum()).to_numpy()
sd_somme = float(m.sharpe_da_somme(np.ones(len(s1)), s1, s2, len(d), 252))
verifica("sharpe da somme = sharpe diretto", abs(sd_somme - m.sharpe(d["r"], 252)) < 1e-9, (sd_somme, m.sharpe(d["r"], 252)))
print(f"Tutti i {ok} controlli superati.")
