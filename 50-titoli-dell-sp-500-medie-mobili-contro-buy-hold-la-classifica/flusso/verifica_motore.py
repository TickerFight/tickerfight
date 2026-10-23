"""Controlli del motore di simulazione. Usa SOLO dati inventati: nessun numero qui è un risultato.

Si esegue prima del backtest (lo fa anche il flusso su GitHub): se un controllo fallisce, il flusso si ferma.
  1. conti fatti a mano (guadagno, perdita, cambio, compensazione delle minusvalenze);
  2. confronto con una formula indipendente;
  3. coerenza del registro delle operazioni con i prezzi grezzi.
"""
import numpy as np
import pandas as pd

import simulazione as s

ok = 0


def verifica(nome, condizione, dettaglio=""):
    global ok
    if not condizione:
        raise SystemExit(f"FALLITO: {nome} {dettaglio}")
    ok += 1
    print(f"  ok  {nome}")


def uguali(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


print("1. Conti a mano")
# Guadagno: compro a 100, vendo a 120, cambio 1. Azioni = 499/100 = 4,99; incasso 598,8; netto 597,8;
# plusvalenza 97,8; tassa 25,428; cassa finale 572,372.
piccolo = pd.DataFrame({"Open": [100, 100, 100, 120, 120, 120.0], "Close": [100, 100, 110, 120, 120, 120.0],
                        "fx": 1.0, "segnale": [False, True, True, False, False, False]},
                       index=pd.bdate_range("2022-03-01", periods=6))
r = s.simula(piccolo, 1, 500, 1.0, 0.26, "apertura", True)
verifica("guadagno: cassa finale 572,372", uguali(r["valore_finale_eur"], 572.372), r["valore_finale_eur"])
verifica("guadagno: tassa 25,428", uguali(r["tasse_eur"], 25.428))
verifica("guadagno: 2 commissioni", uguali(r["commissioni_eur"], 2.0))

perdita = piccolo.copy()
perdita["Open"] = [100, 100, 110, 110, 90, 90.0]
perdita["Close"] = [100, 100, 110, 100, 90, 90.0]
r = s.simula(perdita, 1, 500, 1.0, 0.26, "apertura", True)
verifica("perdita: cassa finale = 499/110*90-1", uguali(r["valore_finale_eur"], 499 / 110 * 90 - 1), r["valore_finale_eur"])
verifica("perdita: nessuna tassa", r["tasse_eur"] == 0.0)

cambio = piccolo.copy()
cambio["fx"] = 1.25
r = s.simula(cambio, 1, 500, 1.0, 0.26, "apertura", True)
verifica("cambio costante: stesso risultato in euro", uguali(r["valore_finale_eur"], 572.372))

# Con il cambio che cambia tra acquisto e vendita la plusvalenza in euro cambia: compro con cambio 1,00,
# vendo con cambio 1,25 (dollaro più debole -> meno euro): 4,99 azioni * 120 / 1,25 = 479,04; netto 478,04.
cambio_var = piccolo.copy()
cambio_var["fx"] = [1.0, 1.0, 1.0, 1.0, 1.25, 1.25]   # acquisto all'apertura di i=2 con fx[1]=1,00; vendita i=4 con fx[3]=1,00
r = s.simula(cambio_var, 1, 500, 1.0, 0.26, "apertura", True)
verifica("cambio: ordini con il cambio dell'ultima chiusura nota", uguali(r["valore_finale_eur"], 572.372), r["valore_finale_eur"])
cambio_var["fx"] = [1.0, 1.0, 1.0, 1.25, 1.25, 1.25]  # vendita i=4 con fx[3]=1,25
r = s.simula(cambio_var, 1, 500, 1.0, 0.26, "apertura", True)
netto_atteso = 4.99 * 120 / 1.25 - 1                  # 478,04 euro, sotto i 500 spesi: perdita, nessuna tassa
verifica("cambio: perdita da cambio, nessuna tassa", uguali(r["valore_finale_eur"], netto_atteso) and r["tasse_eur"] == 0.0,
         r["valore_finale_eur"])

z = s.Zaino(0.26)
verifica("zaino: perdita non tassata", z.tassa(2022, -100) == 0.0)
verifica("zaino: guadagno 150 dopo perdita 100 -> tassa su 50", uguali(z.tassa(2023, 150), 13.0))
z = s.Zaino(0.26)
z.tassa(2023, -10)
verifica("zaino: perdita scaduta (2023 -> usabile fino al 2027)", uguali(z.tassa(2028, 100), 26.0))
z = s.Zaino(0.26)
z.tassa(2023, -10)
verifica("zaino: perdita ancora valida nel 2027", uguali(z.tassa(2027, 100), 0.26 * 90))

print("2. Confronto con una formula indipendente (dati inventati, cambio 1, senza costi)")
rng = np.random.default_rng(7)
date = pd.bdate_range("2020-01-01", "2026-10-20")
n = len(date)
chiusura = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.018, n)))
apertura = np.r_[chiusura[0], chiusura[:-1]] * (1 + rng.normal(0, 0.004, n))
fx_var = 1.1 * np.exp(np.cumsum(rng.normal(0, 0.003, n)))
titolo = pd.DataFrame({"Open": apertura, "Close": chiusura}, index=pd.Index(date, name="Date"))
cambio_df = pd.DataFrame({"Close": fx_var}, index=pd.Index(date, name="Date"))
piatto = pd.DataFrame({"Close": 1.0}, index=cambio_df.index)
df = s.prepara(titolo, piatto, 50, 200)
i0 = s.indice_data(df, df.index[-1] - pd.DateOffset(years=5))
SEG = df["segnale"].to_numpy(bool)
C = df["Close"].to_numpy()
formula = 500 * np.prod([(C[i + 1] / C[i]) ** SEG[i - 1] for i in range(i0, len(df) - 1)])
r = s.simula(df, i0, 500, 0.0, 0.0, "chiusura", True)
verifica("regola, esecuzione alla chiusura, lordo = prodotto dei rendimenti", uguali(r["valore_finale_eur"], formula),
         f"{r['valore_finale_eur']} contro {formula}")
bh = s.simula(df, i0, 500, 0.0, 0.0, "chiusura", False)
verifica("buy & hold lordo = chiusura finale / chiusura iniziale", uguali(bh["valore_finale_eur"], 500 * C[-1] / C[i0]))
bh_a = s.simula(df, i0, 500, 0.0, 0.0, "apertura", False)
verifica("buy & hold, esecuzione all'apertura = ultima chiusura / prima apertura",
         uguali(bh_a["valore_finale_eur"], 500 * C[-1] / df["Open"].iloc[i0]))
con = s.simula(df, i0, 500, 1.0, 0.0, "apertura", True)
verifica("commissioni = 1 euro per ogni ordine", uguali(con["commissioni_eur"], len(con["operazioni"]) * 1.0))
netto = s.simula(df, i0, 500, 1.0, 0.26, "apertura", True)
verifica("con la tassa non si finisce mai sopra il caso senza tassa",
         netto["valore_finale_eur"] <= con["valore_finale_eur"] + 1e-9)
verifica("il registro delle operazioni quadra con la cassa finale",
         uguali(500 - sum(o["spesa_eur"] for o in netto["operazioni"]) +
                sum(o["incasso_netto_eur"] - o["tassa_eur"] for o in netto["operazioni"]), netto["valore_finale_eur"]))

print("3. Il registro delle operazioni contro i prezzi grezzi (ricerca per data, senza gli array del motore)")
dfv = s.prepara(titolo, cambio_df, 50, 200)
i0v = s.indice_data(dfv, dfv.index[-1] - pd.DateOffset(years=5))
rv = s.simula(dfv, i0v, 500, 1.0, 0.26, "apertura", True)
errori = 0
for o in rv["operazioni"]:
    d = pd.Timestamp(o["data"])
    if o["motivo"] == "liquidazione finale":
        px, fx = titolo.loc[d, "Close"], cambio_df.loc[d, "Close"]
    else:
        prec = cambio_df.index[cambio_df.index.get_loc(d) - 1]
        px, fx = titolo.loc[d, "Open"], cambio_df.loc[prec, "Close"]
    if not (uguali(o["prezzo_usd"], px) and uguali(o["cambio"], fx) and uguali(o["prezzo_eur"], px / fx)):
        errori += 1
verifica(f"{len(rv['operazioni'])} operazioni con prezzo e cambio corretti", errori == 0, f"{errori} errori")

print(f"\nTutti i {ok} controlli superati (dati inventati: nessuno di questi numeri è un risultato).")
