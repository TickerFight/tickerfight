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


B, H = 12000.0, 60

# 1. Prezzo costante: lump e PAC valgono il budget, per ogni lunghezza
p = np.full(100, 100.0)
controlla("prezzo costante: lump = budget", np.allclose(fx.valore_lump(p, H, B), B))
for r in (3, 12, 36):
    controlla(f"prezzo costante: PAC a {r} rate = budget", np.allclose(fx.valore_pac(p, H, B, r), B))

# 2. Calcolo a mano su un prezzo che sale di 1 al mese
p = 100.0 + np.arange(100)
controlla("calcolo a mano del lump", np.isclose(fx.valore_lump(p, H, B)[0], B * p[H] / p[0]))
a_mano = sum((B / 12) * p[H] / p[k] for k in range(12))
controlla("calcolo a mano del PAC a 12 rate", np.isclose(fx.valore_pac(p, H, B, 12)[0], a_mano))
a_mano_s = sum((B / 12) * p[H + 5] / p[5 + k] for k in range(12))
controlla("calcolo a mano del PAC, partenza 5", np.isclose(fx.valore_pac(p, H, B, 12)[5], a_mano_s))

# 3. Mercato in rialzo: il lump batte il PAC; in calo: il PAC batte il lump
controlla("mercato in rialzo: il lump batte il PAC in ogni partenza", np.all(fx.valore_lump(p, H, B) > fx.valore_pac(p, H, B, 12)))
q = 300.0 - np.arange(100)
controlla("mercato in calo: il PAC batte il lump in ogni partenza", np.all(fx.valore_pac(q, H, B, 12) > fx.valore_lump(q, H, B)))

# 4. Una sola rata = lump sum
controlla("PAC a 1 rata = lump sum", np.allclose(fx.valore_pac(p, H, B, 1), fx.valore_lump(p, H, B)))

# 5. Numero di partenze
controlla("numero di partenze = mesi - orizzonte", len(fx.valore_lump(p, H, B)) == 40)

# 6. Rate più lunghe dell'orizzonte: errore
try:
    fx.valore_pac(p, 6, B, 12)
    controlla("orizzonte < rate rifiutato", False)
except ValueError:
    controlla("orizzonte < rate rifiutato", True)

# 7. Prezzi del primo giorno di Borsa del mese
idx = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-02-03", "2020-02-04", "2020-03-02"])
pm = fx.prezzi_mensili(pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx))
controlla("primo giorno di Borsa del mese", list(pm.values) == [1.0, 3.0, 5.0])

# 8. Scimmie
rng = np.random.default_rng(1)
controlla("scimmie su prezzo costante = budget", np.allclose(fx.valore_scimmia(np.full(100, 50.0), H, B, 12, 5, rng), B))
sm = fx.valore_scimmia(p, H, B, 1, 3, rng)
controlla("una sola rata: la scimmia coincide con il lump", np.allclose(sm[:, 0], fx.valore_lump(p, H, B)))

# 9. Partenze ai massimi: massimo corrente senza look-ahead
pp = np.array([100.0, 110.0, 105.0, 104.0, 120.0, 90.0])
vicino = fx.vicino_ai_massimi(pp, 0.03)
controlla("ai massimi: [sì, sì, no, no, sì, no]", list(vicino) == [True, True, False, False, True, False])
pp2 = np.array([100.0, 99.0, 96.0, 200.0])
controlla("ai massimi: il massimo futuro non conta", list(fx.vicino_ai_massimi(pp2, 0.03)[:3]) == [True, True, False])

# 10. Decenni
controlla("decennio 1927 -> 1920", fx.decennio(pd.Timestamp("1927-12-30")) == 1920 and fx.decennio(pd.Timestamp("2010-01-04")) == 2010)

print(f"\n{n_ok} controlli superati")
