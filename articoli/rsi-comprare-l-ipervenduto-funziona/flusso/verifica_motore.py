"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np

import funzioni as f


def ok(nome, cond):
    assert cond, nome
    print(f"ok  {nome}")


up = np.arange(1.0, 40.0)
r = f.rsi(up, 14)
ok("prezzi sempre in rialzo: RSI cento dopo il periodo iniziale", np.isnan(r[:14]).all() and np.allclose(r[14:], 100.0))
ok("prezzi sempre in ribasso: RSI zero", np.allclose(f.rsi(up[::-1], 14)[14:], 0.0))
# un caso a mano: n = 2, prezzi 10, 11, 10, 12 -> variazioni +1, -1, +2. Medie iniziali: up 0,5 down 0,5 -> RSI(t=2) = 50. Poi up = (0,5*1+2)/2 = 1,25; down = (0,5*1+0)/2 = 0,25 -> RSI(t=3) = 100 - 100/(1+5) = 83,333
r2 = f.rsi(np.array([10.0, 11, 10, 12]), 2)
ok("RSI calcolato a mano", abs(r2[2] - 50.0) < 1e-9 and abs(r2[3] - (100 - 100 / 6)) < 1e-9)
# posizione con isteresi: RSI 40, 25, 35, 45, 55, 40, 20
rr = np.array([40.0, 25, 35, 45, 55, 40, 20])
pos = f.posizione_regola(rr, 30.0, 50.0)
ok("isteresi: entra a 25, resta fino a 55, rientra a 20", list(pos) == [0, 1, 1, 1, 0, 0, 1])
# il rendimento usa la posizione del giorno prima
rend = np.array([0.0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
ok("posizione ritardata di un giorno", np.allclose(f.rendimenti_regola(rend, pos), [0, 0, 0.1, 0.1, 0.1, 0, 0]))
# incroci
ok("prima discesa sotto 30", list(f.primi_incroci(np.array([40.0, 25, 20, 35, 29]), 30.0, "sotto")) == [1, 4])
ok("prima salita sopra 70", list(f.primi_incroci(np.array([60.0, 75, 80, 65, 71]), 70.0, "sopra")) == [1, 4])
ok("rendimento avanti", abs(f.rendimenti_avanti(np.array([100.0, 110, 121]), 1)[0] - 0.1) < 1e-12 and np.isnan(f.rendimenti_avanti(np.array([100.0, 110, 121]), 1)[2]))
# spostamenti: posizione sempre uguale -> p-value 1
rng = np.random.default_rng(0)
x = rng.normal(0.0005, 0.01, 300)
p, _ = f.pval_spostamenti(x, np.ones(300), 50, 252, rng)
ok("posizione costante: p-value uno", p == 1.0)
