"""Controlli delle funzioni su dati inventati. Se uno fallisce, il flusso si ferma."""
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


rng = np.random.default_rng(1)
# 1. Serie sempre in salita: la regola è sempre investita dopo il rodaggio; nessun look-ahead (prima posizione dopo n sedute)
close = pd.Series(100.0 * 1.001 ** np.arange(400))
pos = fx.posizione_sma(close, 50)
controlla("nessuna posizione prima della media + 1 giorno", pos[:50].sum() == 0 and pos[50:].all())

# 2. Look-ahead: cambiare l'ultima chiusura non cambia la posizione dell'ultima seduta
c2 = close.copy(); c2.iloc[-1] = 1.0
controlla("la posizione di oggi non dipende dalla chiusura di oggi", fx.posizione_sma(close, 50)[-1] == fx.posizione_sma(c2, 50)[-1])

# 3. Metriche: sempre investiti, rendimento costante 0,1% al giorno
rend = np.full(504, 0.001)
cg, sh, md = fx.metriche(rend, np.ones((1, 504), dtype=np.int8), 0.0)
controlla("cagr di 0,1% al giorno per 2 anni", np.isclose(cg[0], 1.001 ** 252 - 1))
controlla("nessuna perdita massima in salita", np.isclose(md[0], 0.0))

# 4. Costo: un solo acquisto iniziale costa 0,1% in valore
cg0, _, _ = fx.metriche(rend, np.ones((1, 504), dtype=np.int8), 0.0)
cgc, _, _ = fx.metriche(rend, np.ones((1, 504), dtype=np.int8), 0.001)
controlla("il costo di un acquisto toglie circa 0,05% l'anno", 0 < cg0[0] - cgc[0] < 0.001)

# 5. Perdita massima a mano: +10%, -20%
r = np.array([0.10, -0.20, 0.05])
_, _, md = fx.metriche(r, np.ones((1, 3), dtype=np.int8), 0.0)
controlla("perdita massima a mano = -20%", np.isclose(md[0], -0.20))

# 6. Scimmia a blocchi: stessa quota, stesso numero di cambi, stesse durate (come insieme)
p = np.array([0] * 5 + [1] * 10 + [0] * 3 + [1] * 2 + [0] * 7 + [1] * 8, dtype=np.int8)
val, lung = fx.blocchi(p)
s = fx.scimmia_a_blocchi(val, lung, rng)
controlla("scimmia a blocchi: stessa lunghezza", len(s) == len(p))
controlla("scimmia a blocchi: stessa quota investita", s.sum() == p.sum())
controlla("scimmia a blocchi: stesso numero di cambi", (np.diff(s) != 0).sum() == (np.diff(p) != 0).sum())
controlla("scimmia a blocchi: stesso inizio", s[0] == p[0])

# 7. Scimmia a moneta: quota vicina
m = fx.scimmie_a_moneta(10000, 0.6, 20, rng)
controlla("scimmie a moneta: quota media vicina a 0,6", abs(m.mean() - 0.6) < 0.01)

# 8. Percentile e p
sc = np.arange(100, dtype=float)
b, pv = fx.percentile_e_p(99.5, sc)
controlla("percentile: batte tutte", b == 1.0 and np.isclose(pv, 1 / 101))

# 9. Holm
h = fx.holm({"a": 0.01, "b": 0.02, "c": 0.5})
controlla("Holm: valori attesi", np.isclose(h["a"], 0.03) and np.isclose(h["b"], 0.04) and np.isclose(h["c"], 0.5))

# 10. Su rendimenti i.i.d. senza tendenza la regola non batte sistematicamente le scimmie (p mediano non estremo)
rr = rng.normal(0.0003, 0.01, 6000)
cl = pd.Series(100 * np.cumprod(1 + rr))
ps = fx.posizione_sma(cl, 200)[250:]
rd = rr[250:]
val, lung = fx.blocchi(ps)
sim = np.array([fx.scimmia_a_blocchi(val, lung, rng) for _ in range(200)])
_, shs, _ = fx.metriche(rd, sim, 0.0)
_, shr, _ = fx.metriche(rd, ps, 0.0)
b, _ = fx.percentile_e_p(shr[0], shs)
controlla("serie senza memoria: la regola non domina le scimmie", 0.02 < b < 0.995)

print(f"\n{n_ok} controlli superati")
