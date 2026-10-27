"""Controlli delle funzioni su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import motore_vettoriale as m

n_ok = 0


def controlla(nome: str, condizione: bool) -> None:
    global n_ok
    print(("OK   " if condizione else "FAIL ") + nome)
    if not condizione:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


def serie(valori) -> pd.Series:
    return pd.Series(np.asarray(valori, float), index=pd.bdate_range("2020-01-01", periods=len(valori)))


# 1. Esempio da manuale: +10% e poi -10% non riporta al punto di partenza
c = serie([100.0, 110.0, 99.0])
r, l = m.rend_sempl(c), m.rend_log(c)
controlla("due rendimenti per tre chiusure", len(r) == 2 and len(l) == 2)
controlla("+10% e -10% fanno -1%", abs((1 + r).prod() - 1 - (-0.01)) < 1e-12)
controlla("la media semplice è zero ma il capitale è sceso", abs(r.mean()) < 1e-12 and c.iloc[-1] < c.iloc[0])
controlla("la media dei logaritmi è negativa", l.mean() < 0)

# 2. I logaritmi si sommano, i rendimenti semplici si compongono
rng = np.random.default_rng(5)
close = serie(100 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, 800))))
rs, ls = m.rend_sempl(close), m.rend_log(close)
controlla("somma dei logaritmi = log del rapporto tra ultima e prima chiusura", abs(ls.sum() - np.log(close.iloc[-1] / close.iloc[0])) < 1e-9)
controlla("prodotto dei fattori = rapporto tra ultima e prima chiusura", abs((1 + rs).prod() - close.iloc[-1] / close.iloc[0]) < 1e-9)
controlla("log(1 + r) = rendimento logaritmico", np.allclose(np.log1p(rs), ls))

# 3. Il rendimento semplice è sempre maggiore del logaritmico (tranne a zero)
controlla("semplice >= logaritmico in ogni seduta", bool((rs >= ls - 1e-15).all()))

# 4. Media semplice e media logaritmica: il divario è circa metà della varianza
x = pd.Series(rng.normal(0.0004, 0.012, 200000))
lx = np.log1p(x)
div = m.media_annua(x, 252) - m.media_annua(lx, 252)
mezza = m.varianza_annua(x, 252) / 2
controlla("divario tra media semplice e logaritmica = mezza varianza (errore sotto 0,05 punti)", abs(div - mezza) < 0.0005)
controlla("la media semplice supera sempre quella logaritmica", div > 0)

# 5. Rendimento composto
anni = 800 / 252
controlla("CAGR da rendimenti = CAGR da prezzi", abs(m.cagr_da_rend(rs, anni) - ((close.iloc[-1] / close.iloc[0]) ** (1 / anni) - 1)) < 1e-9)
controlla("e alla media log annua meno uno = CAGR", abs(np.expm1(ls.mean() * len(ls) / anni) - m.cagr_da_rend(rs, anni)) < 1e-9)

# 6. Rendimento costante: nessuna volatilità, nessun divario
costante = serie(100 * 1.001 ** np.arange(300))
rc, lc = m.rend_sempl(costante), m.rend_log(costante)
controlla("con rendimento costante la varianza è zero e semplice e logaritmico quasi coincidono",
          m.varianza_annua(rc, 252) < 1e-20 and m.media_annua(rc, 252) - m.media_annua(lc, 252) < 0.001)

print(f"\nVerifica del motore: {n_ok} controlli superati.")
