"""Controlli delle funzioni su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np

import funzioni as fx

n_ok = 0


def controlla(nome: str, condizione: bool) -> None:
    global n_ok
    print(("OK   " if condizione else "FAIL ") + nome)
    if not condizione:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


# 1. Prezzi costanti: ogni portafoglio vale sempre 1
anni = np.array([2020] * 5 + [2021] * 5 + [2022] * 5)
P = np.full((15, 4), 50.0)
W = np.array([[1, 0.5], [0, 0.5], [0, 0], [0, 0]], float)
controlla("prezzi costanti: valore 1", np.allclose(fx.curve_portafogli(P, anni, W), 1.0))

# 2. Un solo titolo: il portafoglio è il titolo stesso (nessun effetto del ribilanciamento)
rng = np.random.default_rng(1)
P = 100 * np.cumprod(1 + rng.normal(0.0005, 0.01, (15, 4)), axis=0)
W1 = np.array([[0.0], [1.0], [0.0], [0.0]])
V = fx.curve_portafogli(P, anni, W1)[:, 0]
controlla("un titolo solo = buy & hold del titolo", np.allclose(V, P[:, 1] / P[0, 1]))

# 3. Due titoli, calcolo a mano con ribilanciamento al cambio d'anno
P2 = np.array([[100, 100], [110, 100], [110, 100], [110, 100], [121, 100],   # 2020 (5 giorni)
               [121, 120], [121, 120], [121, 120], [121, 120], [121, 120],   # 2021
               [121, 120], [121, 120], [121, 120], [121, 120], [121, 120]], float)
W2 = np.array([[0.5], [0.5]])
V = fx.curve_portafogli(P2, anni, W2)[:, 0]
v_fine_2020 = 0.5 * 1.21 + 0.5 * 1.00          # = 1,105 con pesi iniziali 50/50
controlla("fine 2020 a mano", np.isclose(V[4], v_fine_2020))
# 2021: si riparte con pesi 50/50 sul valore di fine 2020; il secondo titolo sale da 100 a 120, il primo non si muove
controlla("2021 a mano (ribilanciamento)", np.isclose(V[9], v_fine_2020 * (0.5 * 1.0 + 0.5 * 1.2)))
controlla("2022 senza variazioni: valore costante", np.allclose(V[10:], V[9]))

# 4. Metriche
V = np.array([[1.0], [1.1], [0.9], [1.2]])
controlla("max drawdown a mano", np.isclose(fx.max_drawdown(V)[0], 0.9 / 1.1 - 1))
controlla("CAGR a mano (un anno)", np.isclose(fx.cagr(V, 365.25)[0], 0.2))
controlla("CAGR a mano (due anni)", np.isclose(fx.cagr(V, 730.5)[0], 1.2 ** 0.5 - 1))
S = fx.sharpe(np.array([[1.0], [1.01], [1.0201], [1.030301]]))
controlla("Sharpe con rendimenti costanti: non finito oppure molto grande o nullo", (not np.isfinite(S[0])) or S[0] > 1e6 or S[0] == 0 or np.isnan(S[0]))

# 5. Estrazione dei pesi: k titoli, somma 1, colonne diverse
W = fx.estrai_pesi(30, 7, 50, np.random.default_rng(3))
controlla("pesi: somma 1 per colonna", np.allclose(W.sum(axis=0), 1.0))
controlla("pesi: esattamente k titoli", np.all((W > 0).sum(axis=0) == 7))
controlla("pesi: portafogli diversi tra loro", len({tuple(np.flatnonzero(c)) for c in W.T}) > 45)

# 6. Il rendimento di un portafoglio a pesi uguali sull'anno intero è la media dei rendimenti dei titoli
P3 = np.array([[100, 100, 100], [150, 100, 90], [200, 100, 80]], float)
V = fx.curve_portafogli(P3, np.array([2020, 2020, 2020]), np.full((3, 1), 1 / 3))[:, 0]
controlla("un anno: media dei rendimenti dei titoli", np.isclose(V[-1], (2.0 + 1.0 + 0.8) / 3))

print(f"\nTutti i {n_ok} controlli superati.")
