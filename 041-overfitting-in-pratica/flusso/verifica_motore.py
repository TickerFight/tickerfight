"""Controlli delle funzioni dell'esperimento su dati inventati. Se uno fallisce, il flusso si ferma."""
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


def serie(valori, inizio="2000-01-03") -> pd.Series:
    return pd.Series(np.asarray(valori, float), index=pd.bdate_range(inizio, periods=len(valori)))


# 1. Le coppie hanno sempre la media veloce più corta della lenta
cp = fx.coppie((5, 10, 50), (10, 50, 100))
controlla("solo coppie con veloce < lenta", all(f < l for f, l in cp))
controlla("numero di coppie corretto (5/10, 5/50, 5/100, 10/50, 10/100, 50/100)", len(cp) == 6)

# 2. Prezzo che sale dell'1% al giorno: la posizione scatta dopo la media lenta, con un giorno di ritardo; costo solo all'ingresso
c = serie(100 * 1.01 ** np.arange(60))
lr0 = fx.log_rendimenti(c, [(5, 20)], 0.0)[0]
lr1 = fx.log_rendimenti(c, [(5, 20)], 0.001)[0]
primo = int(np.flatnonzero(lr0 != 0)[0])
controlla("prima posizione dopo la media lenta più un giorno di ritardo (20 chiusure + 1)", primo == 20)
controlla("una volta dentro, ogni giorno rende l'1%", np.allclose(lr0[primo:], np.log(1.01), atol=1e-6))
controlla("il costo si paga una volta sola, all'ingresso", np.isclose(lr0[primo] - lr1[primo], np.log1p(0.01) - np.log1p(0.01 - 0.001), atol=1e-6)
          and np.allclose(lr0[primo + 1:], lr1[primo + 1:], atol=1e-7))

# 3. Nessun look-ahead: tagliare il futuro non cambia i rendimenti passati
rng = np.random.default_rng(1)
p = serie(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 900))))
pieno = fx.log_rendimenti(p, [(5, 30), (10, 60), (20, 100)], 0.001)
ok = True
for taglio in (200, 450, 700):
    parz = fx.log_rendimenti(p.iloc[:taglio], [(5, 30), (10, 60), (20, 100)], 0.001)
    ok &= bool(np.allclose(parz, pieno[:, :taglio], atol=1e-7))
controlla("i rendimenti di una seduta non cambiano se si taglia il futuro", ok)

# 4. Le finestre: ottimizzazione prima della prova, prove senza sovrapposizione, tutto dentro i dati
fin = fx.finestre(10000, 401, 2520, 1260, 1260)
controlla("finestre non vuote", len(fin) > 0)
controlla("ottimizzazione e prova contigue e in ordine", all(a < b < c for a, b, c in fin) and all(b == a + 2520 and c == b + 1260 for a, b, c in fin))
controlla("i periodi di prova non si sovrappongono", all(fin[k][2] <= fin[k + 1][1] + 2520 and fin[k][2] == fin[k + 1][2] - 1260 for k in range(len(fin) - 1))
          and all(fin[k][2] - fin[k][1] == 1260 for k in range(len(fin))))
controlla("l'ultima finestra sta dentro i dati e un'altra non ci starebbe", fin[-1][2] <= 10000 < fin[-1][2] + 1260)
controlla("nessuna finestra se i dati sono troppo corti", fx.finestre(3000, 401, 2520, 1260, 1260) == [])

# 5. Il rendimento annuo di una finestra è quello composto
date = pd.bdate_range("2000-01-03", periods=800)
lr = np.full((1, 800), np.log(1.0004), dtype=np.float32)
anni = (date[599] - date[199]).days / 365.25
atteso = np.exp(400 * np.log(1.0004) / anni) - 1
controlla("CAGR della finestra = crescita composta annualizzata", abs(fx.cagr_finestra(lr, date, 200, 600)[0] - atteso) < 1e-6)

# 6. Il migliore di un sottoinsieme
train = np.array([0.01, 0.05, 0.02, 0.04])
test = np.array([0.10, 0.20, 0.30, 0.40])
perm = np.array([[0, 1, 2, 3], [3, 2, 1, 0]])
r = fx.migliore_nei_sottoinsiemi(train, test, perm, (1, 4))
controlla("con tutte le coppie sceglie la migliore in ottimizzazione e ne riporta la prova", np.isclose(r[4][0], 0.05) and np.isclose(r[4][1], 0.20))
controlla("con una coppia sola non sceglie nulla: media dei primi elementi", np.isclose(r[1][0], (0.01 + 0.04) / 2) and np.isclose(r[1][1], (0.10 + 0.40) / 2))

# 7. Sul puro rumore, il migliore in ottimizzazione fa meglio in ottimizzazione che in prova, e sempre di più con più coppie
rng = np.random.default_rng(2)
tr, te = rng.normal(0.05, 0.03, 700), rng.normal(0.05, 0.03, 700)
perm = np.argsort(rng.random((500, 700)), axis=1)
r = fx.migliore_nei_sottoinsiemi(tr, te, perm, (1, 16, 256))
controlla("sul rumore la distanza cresce con la dimensione della griglia", (r[256][0] - r[256][1]) > (r[16][0] - r[16][1]) > (r[1][0] - r[1][1]))
controlla("sul rumore scegliere il migliore in ottimizzazione fa salire molto il rendimento in ottimizzazione", r[256][0] > tr.mean() + 0.03)

print(f"\nVerifica del motore: {n_ok} controlli superati.")
