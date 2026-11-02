"""Controlli su dati inventati: se uno fallisce, il flusso si ferma."""
import numpy as np

import funzioni as f
import motore as m

# 1) rendimento costante 1% al giorno per 252 giorni
r = np.full(252, 0.01)
assert abs(m.cagr(r, 252) - (1.01 ** 252 - 1)) < 1e-9
# 2) componenti: reddito pari al 1% ogni mese, prezzo fermo
close = np.ones(13)
adj = 1.01 ** np.arange(13)
p, i = f.componenti_mensili(close, adj)
assert np.allclose(p, 0) and np.allclose(i, 0.01)
# 3) prezzo fermo, nessun reddito, nessuna tassa: dopo 12 mesi di rata 10 restano 1000 - 120
p0, i0 = np.zeros(12), np.zeros(12)
ris = f.prelievo(p0, i0, 1000.0, 10.0, 0.0)
assert abs(ris["finale"] - 880.0) < 1e-9 and abs(ris["prelevato"] - 120.0) < 1e-9
# 4) reddito 1% al mese, rata 10 su 1000: la rata è coperta dal reddito, nessuna vendita; il capitale non cala
ris = f.prelievo(p0, np.full(12, 0.01), 1000.0, 10.0, 0.0)
assert ris["finale"] >= 1000.0 - 1e-9
# 5) con tassa 26% sul reddito 1%: reddito netto 7,4 < rata 10, si vendono quote (senza plusvalenza)
ris = f.prelievo(np.zeros(1), np.full(1, 0.01), 1000.0, 10.0, 0.26)
assert abs(ris["finale"] - 997.4) < 1e-9
# 6) esaurimento
ris = f.prelievo(np.full(12, -0.5), np.zeros(12), 100.0, 50.0, 0.0)
assert ris["esaurito"] > 0 and ris["finale"] == 0.0
# 7) con tassa: guadagno finale tassato (prezzo raddoppia in un mese, nessun prelievo possibile: rata 0)
ris = f.prelievo(np.array([1.0]), np.zeros(1), 100.0, 0.0, 0.26)
assert abs(ris["finale"] - (200.0 - 0.26 * 100.0)) < 1e-9
print("verifica_motore: tutti i controlli superati")
