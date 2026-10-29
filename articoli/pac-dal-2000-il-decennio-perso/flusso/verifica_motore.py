"""Controlli delle funzioni su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import config
import funzioni as fx

n_ok = 0


def controlla(nome, cond):
    global n_ok
    print(("OK   " if cond else "FAIL ") + nome)
    if not cond:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


M, V, C, T = config.MESI, config.VERSAMENTO, config.COMMISSIONE, config.ALIQUOTA
rng = np.random.default_rng(3)

# prezzo costante: nessuna plusvalenza, restano versato meno le commissioni
p = np.full(M + 30, 100.0)
pac, ls = fx.piani(p)
atteso_pac = (M * (V - C) - C) / (M * V) - 1
controlla("prezzo costante: il PAC perde le sole commissioni", np.allclose(pac, atteso_pac))
atteso_ls = (M * V - 2 * C) / (M * V) - 1
controlla("prezzo costante: il lump sum perde le sole commissioni", np.allclose(ls, atteso_ls))
controlla("numero di partenze = mesi disponibili meno la durata", len(pac) == len(p) - M)

# prezzo che raddoppia con un salto: il lump sum fa +100% lordo, il PAC meno
p2 = np.r_[np.full(M, 100.0), np.full(30, 200.0)]
pac2, ls2 = fx.piani(p2)
lordo_ls = (M * V - C) / 100 * 200
atteso_ls2 = (lordo_ls - C - T * (lordo_ls - M * V - C)) / (M * V) - 1
controlla("raddoppio: rendimento netto del lump sum con tassa", np.isclose(ls2[0], atteso_ls2))
controlla("raddoppio: il PAC (comprato sempre a 100) rende come il lump sum", np.isclose(pac2[0], atteso_ls2, atol=0.05))

# tassa solo sulla plusvalenza
controlla("nessuna tassa se si perde", np.isclose(fx.valore_netto(np.array([900.0]), 1000.0)[0], 900.0 - C))
controlla("tassa del 26% sulla plusvalenza netta", np.isclose(fx.valore_netto(np.array([1200.0]), 1000.0)[0], 1200.0 - C - T * (200.0 - C)))

# crollo a metà piano: il PAC fa meglio del lump sum
p3 = np.r_[np.full(1, 100.0), np.full(M // 2, 100.0), np.full(M // 2 + 29, 50.0)]
pac3, ls3 = fx.piani(p3)
controlla("crollo a metà piano: il PAC perde meno del lump sum", pac3[0] > ls3[0])

# curva del piano coerente con il rendimento finale
pp = 100 * np.exp(np.cumsum(rng.normal(0.005, 0.04, M + 40)))
a, b, c = fx.curva_piano(pp, 5)
controlla("curva: il versato arriva a quello totale", np.isclose(c[-1], M * V) and len(a) == M + 1)
pacx, lsx = fx.piani(pp)
lordo = a[-1]
netto = fx.valore_netto(np.array([lordo]), M * V)[0]
controlla("curva e piani danno lo stesso valore finale", np.isclose(netto / (M * V) - 1, pacx[5]))

# prezzi mensili: prima seduta di ogni mese, mese parziale iniziale scartato
idx = pd.bdate_range("2000-01-20", "2001-03-31")
close = pd.Series(np.arange(1, len(idx) + 1, dtype=float), index=idx)
pm = fx.prezzi_mensili(close)
controlla("prezzi mensili: il primo mese parziale è scartato", str(pm.index[0]) == "2000-02")
controlla("prezzi mensili: chiusura della prima seduta del mese", pm.iloc[0] == close["2000-02-01":].iloc[0])

# rimescolamento: stesso prodotto dei rendimenti, stesso inizio e fine
s = fx.serie_rimescolata(pp, rng)
controlla("rimescolata: stessi estremi", np.isclose(s[0], pp[0]) and np.isclose(s[-1], pp[-1]))
controlla("rimescolata: ordine diverso", not np.allclose(s, pp))
print(f"{n_ok} controlli superati")
