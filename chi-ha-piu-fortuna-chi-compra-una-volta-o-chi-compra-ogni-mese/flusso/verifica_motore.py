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


B, R = 1200.0, 12

# 1. Prezzo costante: lump e PAC valgono il budget
p = np.full(40, 100.0)
controlla("prezzo costante: lump = budget", np.allclose(fx.valore_lump(p, 12, B, 0.0), B))
controlla("prezzo costante: PAC = budget", np.allclose(fx.valore_pac(p, 12, B, R, 0.0), B))

# 2. Prezzo che sale di 1 al mese (p = 100, 101, ...): confronto con calcolo a mano per la partenza 0, orizzonte 12
p = 100.0 + np.arange(40)
a_mano_lump = B * p[12] / p[0]
a_mano_pac = sum((B / R) * p[12] / p[k] for k in range(12))
controlla("calcolo a mano del lump", np.isclose(fx.valore_lump(p, 12, B, 0.0)[0], a_mano_lump))
controlla("calcolo a mano del PAC", np.isclose(fx.valore_pac(p, 12, B, R, 0.0)[0], a_mano_pac))
controlla("mercato in rialzo: il lump batte il PAC in ogni partenza",
          np.all(fx.valore_lump(p, 12, B, 0.0) > fx.valore_pac(p, 12, B, R, 0.0)))

# 3. Mercato in calo: vince il PAC
q = 200.0 - np.arange(40)
controlla("mercato in calo: il PAC batte il lump in ogni partenza",
          np.all(fx.valore_pac(q, 12, B, R, 0.0) > fx.valore_lump(q, 12, B, 0.0)))

# 4. Commissioni: 2 euro a ordine tolgono 2 al lump e 24 al PAC
controlla("commissione lump = 2 euro", np.allclose(fx.valore_lump(p, 12, B, 0.0) - fx.valore_lump(p, 12, B, 2.0), 2.0))
controlla("commissione PAC = 24 euro", np.allclose(fx.valore_pac(p, 12, B, R, 0.0) - fx.valore_pac(p, 12, B, R, 2.0), 24.0))

# 5. Numero di partenze
controlla("numero di partenze = mesi - orizzonte", len(fx.valore_lump(p, 24, B, 0.0)) == 16)

# 6. Orizzonte più corto delle rate: errore
try:
    fx.valore_pac(p, 6, B, R, 0.0)
    controlla("orizzonte < rate rifiutato", False)
except ValueError:
    controlla("orizzonte < rate rifiutato", True)

# 7. Prezzi del primo giorno di Borsa del mese
idx = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-02-03", "2020-02-04", "2020-03-02"])
pm = fx.prezzi_mensili(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx))
controlla("primo giorno di Borsa del mese", list(pm.values) == [1.0, 3.0, 5.0])

# 8. Scimmie su prezzo costante valgono il budget; con tutte le rate al primo mese valgono il lump (rate=1 -> come lump)
rng = np.random.default_rng(1)
controlla("scimmie su prezzo costante = budget", np.allclose(fx.valore_scimmia(np.full(40, 50.0), 12, B, R, 5, rng), B))
sm = fx.valore_scimmia(p, 12, B, 1, 3, rng)
controlla("una sola rata: la scimmia coincide con il lump", np.allclose(sm[:, 0], fx.valore_lump(p, 12, B, 0.0)))

# 9. Rimescolamento: stesso prezzo iniziale e finale, stessa somma dei rendimenti
r = fx.serie_rimescolata(p, rng)
controlla("rimescolata: stesso inizio e fine", np.isclose(r[0], p[0]) and np.isclose(r[-1], p[-1]))
controlla("rimescolata: stessi rendimenti ordinati", np.allclose(np.sort(np.diff(np.log(r))), np.sort(np.diff(np.log(p)))))

# 10. Holm
h = fx.holm({"a": 0.01, "b": 0.02, "c": 0.5})
controlla("Holm: valori attesi", np.isclose(h["a"], 0.03) and np.isclose(h["b"], 0.04) and np.isclose(h["c"], 0.5))

# 11. Rimescolate su mercato sempre in salita (nessun margine di ordine): lump vince sempre
qq = fx.quota_lump_rimescolate(100.0 * 1.01 ** np.arange(40), 12, B, R, 5, rng)
controlla("rendimenti costanti: il rimescolamento non cambia nulla (lump vince sempre)", np.allclose(qq, 1.0))

print(f"\n{n_ok} controlli superati")
