"""Controlli delle funzioni su dati inventati. Se uno fallisce, il flusso si ferma."""
import numpy as np
import pandas as pd

import funzioni as fx

n_ok = 0


def controlla(nome, cond):
    global n_ok
    print(("OK   " if cond else "FAIL ") + nome)
    if not cond:
        raise SystemExit(f"Controllo fallito: {nome}")
    n_ok += 1


rng = np.random.default_rng(1)
# 1. rendimenti mensili: 3 mesi finti, l'ultimo (incompleto) è scartato
d = pd.bdate_range("2020-01-01", "2020-04-10")
c = pd.Series(100 * 1.001 ** np.arange(len(d)), index=d)
rm = fx.rendimenti_mensili(c)
controlla("rendimenti mensili: scartato l'ultimo mese incompleto", str(rm.index[-1]) == "2020-03" and len(rm) == 2)
# 2. AR(1) con phi 0,5: il BIC sceglie un ordine con memoria e stima phi vicino a 0,5
a = np.zeros(1500)
e = rng.normal(0, 1, 1500)
for t in range(1, 1500):
    a[t] = 0.5 * a[t - 1] + e[t]
ordine, ris, tab = fx.scegli_ordine(a, 2, 2)
controlla("AR(1): l'ordine scelto ha almeno un parametro AR", ordine[0] >= 1)
controlla("AR(1): phi stimato vicino a 0,5", abs(float(ris.params[list(ris.param_names).index("ar.L1")]) - 0.5) < 0.1)
# 3. rumore bianco: il BIC sceglie (0, 0)
w = rng.normal(0.01, 0.04, 800)
ordine_w, _, _ = fx.scegli_ordine(w, 2, 2)
controlla("rumore bianco: il BIC sceglie (0, 0)", ordine_w == (0, 0))
# 4. previsioni a un passo senza guardare avanti: cambiare un valore futuro non cambia la previsione passata
y = rng.normal(0.01, 0.04, 400)
f1, _, r1, _ = fx.previsioni_rolling(y, 300, 25, 1, 1)
y2 = y.copy()
y2[390] += 1.0
f2, _, _, _ = fx.previsioni_rolling(y2, 300, 25, 1, 1)
controlla("nessun look-ahead: le previsioni fino al mese 389 non cambiano se si altera il mese 390", np.allclose(f1[:90], f2[:90], atol=1e-8))
controlla("le previsioni sono quante i mesi fuori campione", len(f1) == 100 and np.allclose(r1, y[300:]))
# 5. R quadro fuori campione: modello perfetto = 1, modello uguale alla base = 0
r = rng.normal(0, 1, 200)
b = np.zeros(200)
controlla("R quadro fuori campione di un modello perfetto", abs(fx.r2_fuori_campione(r, b, r) - 1) < 1e-12)
controlla("R quadro fuori campione di un modello uguale alla base", abs(fx.r2_fuori_campione(r, b, b)) < 1e-12)
# 6. Clark-West: su rumore bianco il p-value non è piccolo; con un segnale vero lo è
ru = rng.normal(0, 1, 1500)
f_buono = 0.5 * ru + rng.normal(0, 0.1, 1500)   # previsione con vero contenuto
_, p_rum = fx.clark_west(ru, np.zeros(1500), rng.normal(0, 0.05, 1500), 12)
_, p_seg = fx.clark_west(ru, np.zeros(1500), f_buono, 12)
controlla("Clark-West: previsione di puro rumore non rifiuta a 0,001", p_rum > 0.001)
controlla("Clark-West: previsione informativa rifiuta", p_seg < 0.001)
# 7. Newey-West: media nulla -> t piccola; media grande -> t grande
controlla("Newey-West: media vera zero", abs(fx.newey_west_t(rng.normal(0, 1, 3000), 12)) < 4)
controlla("Newey-West: media lontana da zero", fx.newey_west_t(rng.normal(1, 1, 3000), 12) > 10)
# 8. bootstrap stazionario: indici dentro l'intervallo e blocchi consecutivi
idx = next(fx.bootstrap_stazionario(rng, 100, 10, 1))
controlla("bootstrap stazionario: indici validi", idx.min() >= 0 and idx.max() < 100 and len(idx) == 100)
controlla("bootstrap stazionario: contiene blocchi consecutivi", np.mean(np.diff(idx) == 1) > 0.5)
print(f"Tutti i {n_ok} controlli superati.")
