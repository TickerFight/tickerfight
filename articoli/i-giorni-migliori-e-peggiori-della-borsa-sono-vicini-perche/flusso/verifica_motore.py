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


# 1. Estremi
r = np.zeros(200)
r[10], r[50] = -0.10, 0.08
r[11], r[120] = -0.09, 0.07
pe, mi = fx.posizioni_estreme(r, 0.01)
controlla("k = 2 su 200 sedute", len(pe) == 2 and len(mi) == 2)
controlla("peggiori = {10, 11}", list(pe) == [10, 11])
controlla("migliori = {50, 120}", list(mi) == [50, 120])

# 2. Distanza dal più vicino
d = fx.distanza_vicino(np.array([10, 11]), np.array([50, 120]))
controlla("distanze dal più vicino = 40 e 39", list(d) == [40, 39])
d2 = fx.distanza_vicino(np.array([5, 100]), np.array([0, 98, 200]))
controlla("distanze da entrambi i lati", list(d2) == [5, 2])
controlla("b prima di a e dopo", list(fx.distanza_vicino(np.array([30]), np.array([10, 33]))) == [3])

# 3. Statistiche di vicinanza
st = fx.statistiche_vicinanza(r, 0.01, 10)
controlla("mediana 39,5", np.isclose(st["mediana_peggiori_migliori"], 39.5))
controlla("nessun giorno peggiore ha un migliore entro 10", st["quota_peggiori_con_migliore"] == 0.0)
r2 = r.copy(); r2[12] = 0.09
st2 = fx.statistiche_vicinanza(r2, 0.01, 10)
controlla("un migliore a 1-2 sedute dai peggiori: quota 1", st2["quota_peggiori_con_migliore"] == 1.0)

# 4. Anni
anni = np.repeat(np.arange(2000, 2010), 20)
rr = np.zeros(200); rr[[0, 1, 2, 3]] = [-0.1, -0.09, 0.1, 0.09]
controlla("tutti gli estremi in un anno: quota 1", np.isclose(fx.quota_anni_top(rr, anni, 0.01, 1), 1.0))

# 5. Volatilità di ieri: nessun look-ahead
x = np.zeros(100); x[50] = 0.5
v = fx.vol_ewma_ieri(x, 0.94, 10)
controlla("EWMA: la seduta 50 non conosce il proprio shock", np.isclose(v[50], v[49]) and v[51] > v[50])
m = fx.vol_mobile_ieri(x, 20)
controlla("vol mobile: il giorno 50 è escluso, il 51 lo include", np.isclose(m[50], 0.0) and m[51] > 0)
controlla("vol mobile: NaN all'inizio", np.isnan(m[10]))

# 6. Quintili
vol = np.arange(1, 101, dtype=float)
q = fx.quote_per_quintile(vol, np.array([0, 99, 99, 50]))
controlla("quintili: 1 nel più basso, 2 nel più alto, 1 al centro", np.allclose(q, [0.25, 0, 0.25, 0, 0.5]))
controlla("le quote dei quintili sommano a 1", np.isclose(q.sum(), 1.0))

# 7. Filtro: mercato calmo, un periodo agitato -> liquidità solo nel periodo agitato, nessun look-ahead
rng = np.random.default_rng(3)
y = rng.normal(0, 0.005, 1500); y[1000:1030] = rng.normal(0, 0.05, 30)
liq = fx.segnale_filtro(y, 20, 0.8, 500)
controlla("filtro: mai in liquidità prima della storia minima", not liq[:500].any())
controlla("filtro: in liquidità durante il periodo agitato (dopo i primi giorni)", liq[1005:1030].mean() > 0.8)
y2 = y.copy(); y2[1200:] = 99.0
controlla("filtro: cambiare il futuro non cambia il passato", np.array_equal(fx.segnale_filtro(y2, 20, 0.8, 500)[:1200], liq[:1200]))

# 8. Rendimenti del filtro e costi
liq3 = np.array([False, False, True, True, False])
rf = fx.rendimenti_filtro(np.full(5, 0.01), liq3, 0.001)
controlla("liquidità vale zero; costo a ogni cambio (2 cambi)", np.allclose(rf, [0.01, 0.01, -0.001, 0.0, 0.01 - 0.001]))

# 9. CAGR e scimmie
controlla("CAGR: +10% in un anno", np.isclose(fx.cagr(np.array([0.10]), 1.0), 0.10))
sc = fx.cagr_scimmie(np.full(100, 0.001), 0, 1.0, 3, rng)
controlla("scimmie senza sedute fuori = buy & hold", np.allclose(sc, fx.cagr(np.full(100, 0.001), 1.0)))
sc2 = fx.cagr_scimmie(np.full(100, 0.001), 100, 1.0, 3, rng)
controlla("scimmie sempre fuori = 0", np.allclose(sc2, 0.0))

# 10. Rendimenti
s = pd.Series([100.0, 110.0, 99.0], index=pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]))
controlla("rendimenti semplici", np.allclose(fx.rendimenti(s).values, [0.10, -0.10]))

# 11. Rimescolamento di dati i.i.d.: nessuna vicinanza oltre il caso
iid = np.random.default_rng(7).standard_t(4, 6000) * 0.01
a = fx.statistiche_vicinanza(iid, 0.01, 10)["quota_peggiori_con_migliore"]
controlla("dati i.i.d.: quota di vicinanza vicina a quella attesa dal caso", 0.05 < a < 0.35)

# 12. Holm
h = fx.holm({"a": 0.01, "b": 0.02, "c": 0.5})
controlla("Holm: valori attesi", np.isclose(h["a"], 0.03) and np.isclose(h["b"], 0.04) and np.isclose(h["c"], 0.5))

print(f"\n{n_ok} controlli superati")
