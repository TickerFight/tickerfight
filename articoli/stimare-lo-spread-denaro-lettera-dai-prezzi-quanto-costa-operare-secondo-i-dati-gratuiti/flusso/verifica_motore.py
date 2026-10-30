"""Controlli di funzioni.py su dati inventati. Se uno fallisce, l'Action si ferma."""
import numpy as np
import pandas as pd

import funzioni as f


def ok(nome, cond):
    assert cond, nome
    print(f"ok  {nome}")


# 1. Corwin-Schultz: serie con spread vero noto. Prezzo efficiente = random walk; massimo = max(p)*(1+s/2), minimo = min(p)*(1-s/2).
rng = np.random.default_rng(3)
n, S = 4000, 0.004
cl = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
amp = np.abs(rng.normal(0, 0.006, n)) + 0.0005
h = cl * (1 + amp) * (1 + S / 2)
l = cl * (1 - amp) * (1 - S / 2)
est = np.nanmean(f.cs_grezzo(h, l))
ok("spread noto 0,4%: la stima è dello stesso ordine", 0.001 < est < 0.012)
# 2. prezzo fermo, massimo uguale al minimo: la stima è zero
e0 = f.cs_grezzo(np.full(50, 100.0), np.full(50, 100.0))
ok("prezzo fermo: stima zero", abs(np.nanmean(e0)) < 1e-12)
# 3. il primo elemento è nan e la lunghezza è conservata
ok("lunghezza e primo elemento", len(est * np.ones(1)) == 1 and np.isnan(f.cs_grezzo(h, l)[0]) and len(f.cs_grezzo(h, l)) == n)
# 4. Roll: serie con rimbalzo denaro-lettera: p = m + s/2 * q, q = ±1 casuale; la covarianza è -(s/2)^2, quindi lo spread vale s
idx = pd.bdate_range("2020-01-01", periods=500)
q = rng.choice([-1.0, 1.0], 500)
m = np.full(500, 100.0)
s = 0.5
p = pd.Series(m + s / 2 * q, index=idx)
r = f.roll_mensile(p).dropna()
ok("Roll recupera lo spread del rimbalzo (0,5 su 100)", abs(r.mean() - 0.005) < 0.0015)
# 5. Roll su un trend: covarianza positiva -> nan
trend = pd.Series(np.cumsum(1 + 0.5 * np.sin(np.arange(300) / 8.0)) + 100, index=pd.bdate_range("2020-01-01", periods=300))
ok("Roll con covarianza positiva è nan", f.roll_mensile(trend).isna().all())
# 6. medie mensili
ser = pd.Series(np.arange(40.0), index=pd.bdate_range("2020-01-01", periods=40))
mm = f.media_mensile(ser)
ok("media mensile", abs(mm.iloc[0] - ser[:23].mean()) < 1e-9)
