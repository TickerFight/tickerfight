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


# 1. Scelta con il senno di poi
R = np.array([[0.10, 0.02, -0.05], [0.01, 0.30, 0.00], [-0.10, -0.20, -0.02]])
idx, best = fx.migliore_ex_post(R)
controlla("il migliore di ogni periodo", list(idx) == [0, 1, 2] and np.allclose(best, [0.10, 0.30, -0.02]))

# 2. CAGR e curva
controlla("cagr di due anni al 21% e 0% = 10%", abs(fx.cagr(np.array([0.21, 0.0]), 2) - (1.21 ** 0.5 - 1)) < 1e-12)
controlla("curva di capitale", np.allclose(fx.curva_capitale(np.array([0.1, 0.1]), 100), [110, 121]))

# 3. Regola realizzabile: nessun look-ahead
v = fx.vincitore_precedente(R)
controlla("vincitore precedente: anno 2 usa il settore 0 (vinse l'anno 1)", np.allclose(v, [0.01, 0.00 - 0.0 + R[2, 1]]))
r2 = R.copy()
r2[2] = [9.0, 9.0, 9.0]
controlla("cambiare l'ultimo anno non cambia la scelta fatta per l'ultimo anno", fx.vincitore_precedente(r2)[0] == v[0])
rg = fx.rango_vincitore_precedente(R)
controlla("rango del vincitore dell'anno prima", list(rg) == [2, 3])

# 4. Scimmie: con un solo settore il risultato è fisso; con settori identici pure
Rf = np.full((5, 4), 0.05)
s = fx.scimmie(Rf, 10, 5, np.random.default_rng(1))
controlla("scimmie con settori identici = 5%", np.allclose(s, 0.05))
rng = np.random.default_rng(2)
Rr = rng.normal(0.08, 0.2, size=(27, 9))
sc = fx.scimmie(Rr, 5000, 27, np.random.default_rng(3))
media_lr = np.expm1(np.mean(np.log1p(Rr)))
controlla("la scimmia mediana sta vicino alla media dei settori", abs(np.median(sc) - media_lr) < 0.03)
_, bb = fx.migliore_ex_post(Rr)
controlla("il senno di poi batte tutte le scimmie", fx.cagr(bb, 27) > sc.max())

# 5. Tasse e costi
net = fx.capitale_netto_rotazione(np.array([0.2, 0.2]), 1000, 0.0, 0.26)
atteso = 1000 * (1 + 0.2 * 0.74)
atteso = atteso * (1 + 0.2 * 0.74)
controlla("rotazione senza costi: tassa a ogni anno", abs(net - atteso) < 1e-9)
net2 = fx.capitale_netto_rotazione(np.array([-0.2, 0.3]), 1000, 0.0, 0.26)
# anno 1: -200 (credito 200), capitale 800; anno 2: +240, imponibile 40, tassa 10,4
controlla("minusvalenza riportata", abs(net2 - (800 + 240 - 0.26 * 40)) < 1e-9)
bh = fx.capitale_netto_buy_hold(np.array([0.2, 0.2]), 1000, 0.0, 0.26)
controlla("buy & hold: tassa solo alla fine", abs(bh - (1440 - 0.26 * 440)) < 1e-9)
cc = fx.capitale_netto_rotazione(np.array([0.0]), 1000, 0.001, 0.26)
controlla("costi: un acquisto e una vendita", abs(cc - 1000 * 0.999 * 0.999) < 1e-9)

# 6. Periodi: anni solari da prezzi giornalieri
d = pd.bdate_range("1998-12-01", "2001-12-31")
p = pd.DataFrame({"A": np.linspace(100, 200, len(d)), "B": np.linspace(100, 150, len(d))}, index=d)
ra = fx.rendimenti_periodo(p, "YE", 1999, 2000)
controlla("due anni solari completi", list(ra.index.year) == [1999, 2000])
val_1999 = p["A"][p.index <= "1999-12-31"].iloc[-1] / p["A"][p.index <= "1998-12-31"].iloc[-1] - 1
controlla("rendimento 1999 = ultimo 1999 / ultimo 1998", abs(ra.loc[ra.index.year == 1999, "A"].iloc[0] - val_1999) < 1e-12)

# 7. Holm
h = fx.holm({"a": 0.01, "b": 0.04})
controlla("Holm", abs(h["a"] - 0.02) < 1e-12 and abs(h["b"] - 0.04) < 1e-12)
print(f"\n{n_ok} controlli superati")
