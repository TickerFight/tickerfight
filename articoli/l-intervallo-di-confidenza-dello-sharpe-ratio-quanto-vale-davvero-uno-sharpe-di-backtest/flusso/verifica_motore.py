"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import math

import numpy as np

import funzioni as f


def ok(nome, cond):
    assert cond, nome
    print(f"ok  {nome}")


rng = np.random.default_rng(1)
x = rng.normal(0.0004, 0.01, 252 * 40)
# 1. Sharpe contro il calcolo diretto
ok("Sharpe annualizzato", abs(f.sharpe(x, 252) - x.mean() / x.std(ddof=1) * math.sqrt(252)) < 1e-12)
# 2. errore standard di Lo con Sharpe nullo: radice di ga / n
z0 = rng.normal(0.0, 0.01, 252 * 40)
ok("errore standard di Lo con media vicina a zero ~ 1/radice(anni)", abs(f.se_lo(z0, 252) - 1 / math.sqrt(40)) < 0.01)
# 3. Mertens uguale a Lo per dati normali
ok("Mertens vicino a Lo su dati normali", abs(f.se_mertens(x, 252) / f.se_lo(x, 252) - 1) < 0.05)
# 4. Mertens più largo di Lo per dati con code molto spesse e Sharpe non piccolo
t = rng.standard_t(3, 252 * 40) * 0.006 + 0.0006
ok("Mertens più largo di Lo con code spesse", f.se_mertens(t, 252) > f.se_lo(t, 252))
# 5. bootstrap sui giorni vicino alla formula su dati indipendenti
lo, hi = f.bootstrap_sharpe(x, 500, 1, 252, 0.95, rng)
se = f.se_lo(x, 252)
ok("bootstrap sui giorni vicino alla formula", abs((hi - lo) / (2 * 1.96 * se) - 1) < 0.2)
# 6. bootstrap a blocchi vicino su dati indipendenti
lb, hb = f.bootstrap_sharpe(x, 500, 21, 252, 0.95, rng)
ok("bootstrap a blocchi vicino su dati indipendenti", abs((hb - lb) / (hi - lo) - 1) < 0.25)
# 7. copertura onesta su dati indipendenti: vicina al nominale
y = rng.normal(0.0003, 0.01, 252 * 200)
c, n = f.copertura_fuori(y, 252 * 10, np.arange(0, len(y) - 252 * 10, 21), 252, 1.959964)
ok("copertura onesta vicina al nominale su dati indipendenti", 0.88 < c <= 1.0 and n > 100)
# 8. anni necessari: Sharpe quasi nullo, semiampiezza 0,1 -> z^2 / 0,01 = 384,2 anni
ok("anni necessari", abs(f.anni_necessari(0.0, 0.1, 1.96, 252) - 1.96 ** 2 / 0.01) < 1e-9)
# 9. regola a media mobile: prezzi crescenti -> sempre investita, stessi rendimenti del buy & hold
c_up = np.arange(1.0, 400.0)
r, bh = f.regola_sma(c_up, 50)
ok("prezzi crescenti: la regola coincide col buy & hold", np.allclose(r, bh) and len(r) == len(c_up) - 51)
# 10. differenza di Sharpe: serie identiche -> zero
lo_d, hi_d = f.differenza_sharpe_bootstrap(x, x, 50, 21, 252, 0.95, rng)
ok("serie identiche: differenza nulla", abs(lo_d) < 1e-9 and abs(hi_d) < 1e-9)
