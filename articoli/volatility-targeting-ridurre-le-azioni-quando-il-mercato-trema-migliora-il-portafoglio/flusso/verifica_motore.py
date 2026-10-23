"""Controlli del motore del volatility targeting. Usa SOLO dati inventati: nessun numero qui è un risultato.

Si esegue prima del backtest (lo fa anche il flusso su GitHub): se un controllo fallisce, il flusso si ferma.
  1. conti fatti a mano su serie costruite apposta;
  2. assenza di look-ahead: cambiare un prezzo futuro non cambia mai le posizioni passate;
  3. coerenza tra formule: Sharpe da somme contro Sharpe diretto, periodi, bootstrap.
"""
import numpy as np
import pandas as pd

import motore as m

ok = 0
GA = 252


def verifica(nome, condizione, dettaglio=""):
    global ok
    if not condizione:
        raise SystemExit(f"FALLITO: {nome} {dettaglio}")
    ok += 1
    print(f"  ok  {nome}")


def serie(rend, inizio="2020-01-01"):
    idx = pd.bdate_range(inizio, periods=len(rend))
    return pd.Series(100.0 * np.cumprod(1 + np.asarray(rend, dtype=float)), index=idx)


rng = np.random.default_rng(1)
print("1. Conti a mano")
# Rendimenti alternati +1% / -1%: deviazione standard campionaria nota.
alt = np.tile([0.01, -0.01], 200)
c = serie(alt)
v = m.volatilita(m.rendimenti(c), 20, GA).dropna()
atteso = np.std(alt[1:21] if False else np.array([0.01, -0.01] * 10), ddof=1) * np.sqrt(GA)
verifica("volatilità di una serie +1%/-1%", abs(v.iloc[0] - atteso) < 1e-3 * atteso, f"{v.iloc[0]} vs {atteso}")

# Volatilità costante del 20% annuo: il peso obiettivo con obiettivo 10% deve essere 0,5.
sd_g = 0.20 / np.sqrt(GA)
base = np.tile([sd_g, -sd_g], 300)
c = serie(base)
sig = m.segnale_peso(c, 0.10, 20, 1.0, GA).dropna()
verifica("peso = obiettivo / volatilità (0,5, con la correzione n-1)", np.allclose(sig.to_numpy(), 0.5 * np.sqrt(19 / 20), atol=0.003), sig.iloc[:3].tolist())
sig2 = m.segnale_peso(c, 0.30, 20, 1.0, GA).dropna()
verifica("il tetto limita il peso a 1", np.allclose(sig2.to_numpy(), 1.0))
sig3 = m.segnale_peso(c, 0.30, 20, 1.5, GA).dropna()
verifica("con tetto 1,5 il peso è 1,46 (0,30 / 0,20 con la correzione n-1)", np.allclose(sig3.to_numpy(), 0.30 / 0.20 * np.sqrt(19 / 20), atol=0.01))

# Costi: peso costante 0,5 e costo zero => rendimento della strategia = 0,5 * rendimento dell'indice
d0 = m.serie_strategia(c, 0.10, 20, 1.0, GA, 0.0)
verifica("senza costi: rendimento = peso * indice", np.allclose(d0["strategia"], d0["peso"] * d0["r"]))
verifica("la prima seduta ha scambio pari al peso", abs(d0["scambio"].iloc[0] - d0["peso"].iloc[0]) < 1e-12)
d1 = m.serie_strategia(c, 0.10, 20, 1.0, GA, 10.0)
costo_tot = (d0["strategia"] - d1["strategia"]).sum()
verifica("costo totale = 10 punti base * scambi totali", abs(costo_tot - 0.001 * d0["scambio"].sum()) < 1e-12)
verifica("buy & hold paga solo l'acquisto iniziale", abs((d0["buyhold"] - d1["buyhold"]).sum() - 0.001) < 1e-12)

print("2. Nessun look-ahead")
rend = rng.normal(0.0004, 0.01, 1500)
rend[600:700] *= 3
c = serie(rend)
a = m.serie_strategia(c, 0.10, 21, 1.0, GA, 5.0)
for taglio in (900, 1200, 1400):
    r2 = rend.copy()
    r2[taglio:] = rng.normal(0, 0.05, len(r2) - taglio)         # futuro completamente diverso
    b = m.serie_strategia(serie(r2), 0.10, 21, 1.0, GA, 5.0)
    comune = a.index[a.index < c.index[taglio]]
    verifica(f"posizioni identiche fino al giorno {taglio} (futuro cambiato)",
             np.allclose(a.loc[comune, "peso"], b.loc[comune, "peso"], atol=0, rtol=0, equal_nan=True))
# Ritardo: il peso calcolato a fine mese non è mai usato prima di due sedute dopo.
fm = m.fine_mese(c.index)
sig = m.segnale_peso(c, 0.10, 21, 1.0, GA)
pos = m.posizione(sig)
primo_fm = np.flatnonzero(fm & sig.notna().to_numpy())[0]
verifica("il peso nuovo non è usato nelle due sedute dopo la fine del mese",
         pos.iloc[primo_fm + 1] != sig.iloc[primo_fm] or np.isnan(pos.iloc[primo_fm + 1]))
verifica("la posizione compare dopo due sedute", abs(pos.iloc[primo_fm + 2] - sig.iloc[primo_fm]) < 1e-15)
verifica("l'ultima riga non è mai una fine mese", not m.fine_mese(c.index)[-1])

print("3. Coerenza tra formule")
d = m.serie_strategia(c, 0.10, 21, 1.0, GA, 5.0)
verifica("equity finale = prodotto di (1+r)", abs(m.equity(d["strategia"])[-1] - np.prod(1 + d["strategia"])) < 1e-12)
verifica("perdita massima di una serie sempre crescente è zero", m.perdita_massima(np.full(50, 0.01)) == 0.0)
e = m.perdita_massima(np.array([0.10, -0.50, 0.20]))
verifica("perdita massima a mano (-50%)", abs(e - (-0.5)) < 1e-12, str(e))
# Sharpe da somme contro Sharpe diretto
per = d["periodo"].to_numpy()
w = d.groupby("periodo")["peso"].first().to_numpy()
s1 = d.groupby("periodo")["r"].sum().to_numpy()
s2 = d.groupby("periodo")["r"].apply(lambda x: (x ** 2).sum()).to_numpy()
lordo = d["peso"] * d["r"]
verifica("Sharpe da somme = Sharpe diretto", abs(m.sharpe_da_somme(w, s1, s2, len(d), GA) - m.sharpe(lordo, GA)) < 1e-9)
verifica("i periodi sono mensili (circa 21 sedute)", 15 <= len(d) / len(w) <= 25, str(len(d) / len(w)))
perm = np.stack([rng.permutation(w) for _ in range(3)])
verifica("Sharpe da somme accetta più permutazioni", m.sharpe_da_somme(perm, s1, s2, len(d), GA).shape == (3,))
# Bootstrap: due serie identiche => differenza di Sharpe nulla
x = rng.normal(0.0005, 0.01, 800)
bs = m.bootstrap_dsharpe(x, x, 50, 21, GA, np.random.default_rng(3))
verifica("bootstrap su serie identiche dà differenza nulla", np.allclose(bs, 0))
# volatilità e rolling
v2 = m.volvol(pd.Series(rng.normal(0, 0.01, 800)), GA)
verifica("volvol positiva e finita", np.isfinite(v2) and v2 > 0)
print(f"\n{ok} controlli superati.")
