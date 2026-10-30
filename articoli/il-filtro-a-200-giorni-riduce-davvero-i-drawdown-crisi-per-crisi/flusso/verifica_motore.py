"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def ok(nome, cond):
    assert cond, nome
    print(f"ok  {nome}")


c = np.array([10.0, 10, 10, 10, 20, 24, 24, 12, 12, 12])
pos = f.posizione_sma(c, 3)
ok("media su tre giorni: i primi due sono nan", np.isnan(pos[:2]).all())
ok("salto a 20: sopra la media di (10+10+20)/3", pos[4] == 1.0 and pos[3] == 0.0)
rr, bh, p = f.rendimenti_regola(c, pos, 0.0)
# giorni validi: dal giorno 2 (pos[2]) in poi per i rendimenti dei giorni 3..9
ok("lunghezza dei rendimenti validi", len(rr) == 7 and len(bh) == 7)
ok("il rendimento del giorno 5 usa la posizione del giorno 4", abs(rr[2] - (24 / 20 - 1)) < 1e-12)
ok("posizione 0 prima del salto", rr[0] == 0.0 and rr[1] == 0.0)
rc, _, _ = f.rendimenti_regola(c, pos, 0.01)
ok("il costo si paga sul cambio di posizione", abs((rr - rc).sum() - 0.01 * f.n_cambi(p)) < 1e-12)
ok("buy & hold sugli stessi giorni", abs(bh[2] - 0.2) < 1e-12)
ok("drawdown di +10%, -50%", abs(f.max_drawdown(np.array([0.10, -0.50])) - (-0.5)) < 1e-12)
ok("drawdown nullo se sempre su", f.max_drawdown(np.full(10, 0.01)) == 0.0)
ok("CAGR costante", abs(f.cagr(np.full(252, np.log(1.1) / 252 * 1.0), 252) - (np.exp(252 * np.log1p(np.log(1.1) / 252)) - 1)) < 1e-9)
ok("conteggio cambi", f.n_cambi(np.array([0.0, 0, 1, 1, 0])) == 2)

# episodi: +10%, -30% (-> episodio), +50% (nuovo massimo), -5% (non è un episodio)
e = f.episodi(np.array([0.10, -0.10, -0.10, -0.10, 0.80, -0.05]), 0.20)
ok("un solo episodio sopra il 20%: massimo dopo il primo giorno, minimo al quarto", e == [(1, 4)])
e2 = f.episodi(np.array([0.1, -0.3, -0.2, 0.1]), 0.20)
ok("episodio ancora aperto alla fine della serie", e2 == [(1, 3)])
