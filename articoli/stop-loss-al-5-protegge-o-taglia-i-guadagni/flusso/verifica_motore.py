"""Controlli del motore di simulazione. Usa SOLO dati inventati: nessun numero qui è un risultato.

Si esegue prima del backtest (lo fa anche il flusso su GitHub): se un controllo fallisce, il flusso si ferma.
  1. conti fatti a mano (guadagno, perdita, commissione proporzionale, stop loss, rientro dopo lo stop, minusvalenze);
  2. confronto con una formula indipendente;
  3. nessun look-ahead: cambiare il futuro non cambia gli ordini già dati;
  4. coerenza tra il motore completo e quello usato dalle scimmie, e proprietà delle scimmie.
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


def piccolo(chiusure, segnale, fx=1.0):
    return pd.DataFrame({"Close": np.array(chiusure, float), "fx": fx, "segnale": np.array(segnale, bool)},
                        index=pd.bdate_range("2022-03-01", periods=len(chiusure)))


print("1. Conti a mano")
# Compro a 100 (seduta 2), vendo a 120 (seduta 4). Commissione fissa 2: investo 998, azioni 9,98; incasso 1.197,6;
# netto 1.195,6; plusvalenza 195,6; tassa 50,856; cassa finale 1.144,744.
d = piccolo([100, 100, 100, 120, 120, 120], [0, 1, 1, 0, 0, 0])
r = s.simula(d, 1, 1000, 2.0, 0.0, 0.26, True)
verifica("guadagno: cassa finale 1.144,744", uguali(r["valore_finale_eur"], 1144.744), r["valore_finale_eur"])
verifica("guadagno: tassa 50,856", uguali(r["tasse_eur"], 50.856))
verifica("guadagno: 2 ordini da 2 euro", uguali(r["commissioni_eur"], 4.0))

# Commissione proporzionale 0,1%: investo 1000/1,001; ricevo 9,99000999 azioni; incasso lordo 1.198,801199...
inv = 1000 / 1.001
az = inv / 100
lordo = az * 120
netto = lordo * (1 - 0.001)
tassa = 0.26 * (netto - 1000)
r = s.simula(d, 1, 1000, 0.0, 0.001, 0.26, True)
verifica("commissione proporzionale: cassa finale", uguali(r["valore_finale_eur"], netto - tassa), r["valore_finale_eur"])
verifica("commissione proporzionale: costo = 0,1% di acquisto e vendita",
         uguali(r["commissioni_eur"], 0.001 * inv + 0.001 * lordo))

perdita = piccolo([100, 100, 110, 100, 90, 90], [0, 1, 1, 0, 0, 0])
r = s.simula(perdita, 1, 1000, 2.0, 0.0, 0.26, True)
verifica("perdita: cassa finale = 998/110*90-2", uguali(r["valore_finale_eur"], 998 / 110 * 90 - 2), r["valore_finale_eur"])
verifica("perdita: nessuna tassa", r["tasse_eur"] == 0.0)

cambio = piccolo([100, 100, 100, 120, 120, 120], [0, 1, 1, 0, 0, 0], fx=1.25)
r = s.simula(cambio, 1, 1000, 2.0, 0.0, 0.26, True)
verifica("cambio costante: stesso risultato in euro", uguali(r["valore_finale_eur"], 1144.744))
cv = piccolo([100, 100, 100, 120, 120, 120], [0, 1, 1, 0, 0, 0])
cv["fx"] = [1.0, 1.0, 1.0, 1.0, 1.25, 1.25]       # acquisto con cambio 1,00 alla seduta 2; vendita con cambio 1,25 alla seduta 4
r = s.simula(cv, 1, 1000, 2.0, 0.0, 0.26, True)
atteso = 9.98 * 120 / 1.25 - 2                      # 957,2 euro: sotto i 1.000 spesi, perdita da cambio, nessuna tassa
verifica("cambio: perdita da cambio, nessuna tassa", uguali(r["valore_finale_eur"], atteso) and r["tasse_eur"] == 0.0,
         r["valore_finale_eur"])

# Stop loss. Segnale sempre vero: compro alla seduta 1 a 100. Alla chiusura della seduta 3 il prezzo è 94 (sotto 95):
# l'ordine di vendita parte alla seduta 4, al prezzo 94. Poi il segnale resta vero e non si rientra (bloccato).
st = piccolo([100, 100, 100, 94, 94, 100, 100, 100], [1] * 8)
r = s.simula(st, 1, 1000, 2.0, 0.0, 0.26, True, stop=0.05)
verifica("stop: un solo stop, una sola vendita e nessun rientro con il segnale sempre vero",
         r["n_stop"] == 1 and r["n_acquisti"] == 1 and r["n_vendite"] == 1, (r["n_stop"], r["n_acquisti"]))
verifica("stop: cassa finale = 998/100*94-2 = 936,12", uguali(r["valore_finale_eur"], 9.98 * 94 - 2), r["valore_finale_eur"])
verifica("stop: vendita alla seduta successiva a quella dello scatto", r["operazioni"][1]["i"] == 4 and r["operazioni"][1]["motivo"] == "stop loss")
senza = s.simula(st, 1, 1000, 2.0, 0.0, 0.26, True, stop=None)
verifica("senza stop si resta dentro fino alla fine", senza["n_stop"] == 0 and senza["n_vendite"] == 1 and senza["operazioni"][1]["motivo"] == "liquidazione finale")
sol = piccolo([100, 100, 100, 95.01, 95.01, 100, 100, 100], [1] * 8)
r = s.simula(sol, 1, 1000, 2.0, 0.0, 0.26, True, stop=0.05)
verifica("stop: -4,99% non scatta", r["n_stop"] == 0)

# Rientro: il segnale torna falso (seduta 5) e poi vero (seduta 6): si ricompra alla seduta 7.
ri = piccolo([100, 100, 100, 94, 94, 94, 94, 96, 96], [1, 1, 1, 1, 1, 0, 1, 1, 1])
r = s.simula(ri, 1, 1000, 2.0, 0.0, 0.26, True, stop=0.05)
verifica("rientro solo dopo falso e poi vero: 2 acquisti, 1 stop", r["n_acquisti"] == 2 and r["n_stop"] == 1, (r["n_acquisti"], r["n_stop"]))
verifica("rientro: secondo acquisto alla seduta 7", [o["i"] for o in r["operazioni"] if o["lato"] == "acquisto"] == [1, 7])

# Stop e uscita di trend nella stessa seduta: conta come uscita di trend e non blocca il rientro.
co = piccolo([100, 100, 100, 94, 94, 97, 97, 97], [1, 1, 1, 0, 1, 1, 1, 1])
r = s.simula(co, 1, 1000, 2.0, 0.0, 0.26, True, stop=0.05)
verifica("stop e trend nella stessa seduta: nessuno stop, uscita di trend e rientro il giorno dopo",
         r["n_stop"] == 0 and r["n_acquisti"] == 2 and [o["i"] for o in r["operazioni"] if o["lato"] == "acquisto"] == [1, 5], (r["n_stop"], r["n_acquisti"]))

z = s.Zaino(0.26)
verifica("zaino: perdita non tassata", z.tassa(2022, -100) == 0.0)
verifica("zaino: guadagno 150 dopo perdita 100 -> tassa su 50", uguali(z.tassa(2023, 150), 13.0))
z = s.Zaino(0.26)
z.tassa(2023, -10)
verifica("zaino: perdita scaduta (2023 -> usabile fino al 2027)", uguali(z.tassa(2028, 100), 26.0))
z = s.Zaino(0.26)
z.tassa(2023, -10)
verifica("zaino: perdita ancora valida nel 2027", uguali(z.tassa(2027, 100), 0.26 * 90))

print("2. Confronto con una formula indipendente (dati inventati, senza costi né tasse)")
rng = np.random.default_rng(7)
date = pd.bdate_range("2012-01-01", "2026-10-20")
n = len(date)
chiusura = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, n)))
fx_var = 1.1 * np.exp(np.cumsum(rng.normal(0, 0.003, n)))
titolo = pd.DataFrame({"Close": chiusura}, index=pd.Index(date, name="Date"))
cambio_df = pd.DataFrame({"Close": fx_var}, index=pd.Index(date, name="Date"))
df = s.prepara(titolo, None, 200)
i0 = s.primo_indice(df)
verifica("la media a 200 sedute parte dopo 199 sedute", i0 == 200, i0)
SEG = df["segnale"].to_numpy(bool)
C = df["Close"].to_numpy()
formula = 1000 * np.prod([(C[i + 1] / C[i]) ** SEG[i - 1] for i in range(i0, n - 1)])
r = s.simula(df, i0, 1000, 0.0, 0.0, 0.0, True)
verifica("regola di trend, lordo = prodotto dei rendimenti", uguali(r["valore_finale_eur"], formula), f"{r['valore_finale_eur']} contro {formula}")
bh = s.simula(df, i0, 1000, 0.0, 0.0, 0.0, False)
verifica("buy & hold lordo = chiusura finale / chiusura iniziale", uguali(bh["valore_finale_eur"], 1000 * C[-1] / C[i0]))
dfx = s.prepara(titolo, cambio_df, 200)
Cx, Fx = dfx["Close"].to_numpy(), dfx["fx"].to_numpy()
bhx = s.simula(dfx, i0, 1000, 0.0, 0.0, 0.0, False)
verifica("buy & hold con cambio variabile", uguali(bhx["valore_finale_eur"], 1000 * (Cx[-1] / Fx[-1]) / (Cx[i0] / Fx[i0])))
SEGx = dfx["segnale"].to_numpy(bool)
formula_x = 1000 * np.prod([((Cx[i + 1] / Fx[i + 1]) / (Cx[i] / Fx[i])) ** SEGx[i - 1] for i in range(i0, n - 1)])
rx = s.simula(dfx, i0, 1000, 0.0, 0.0, 0.0, True)
verifica("regola di trend con cambio variabile, lordo = prodotto dei rendimenti in euro", uguali(rx["valore_finale_eur"], formula_x))

con = s.simula(dfx, i0, 1000, 2.0, 0.001, 0.0, True, stop=0.05)
verifica("commissioni = 2 euro + 0,1% dell'importo, ordine per ordine",
         uguali(con["commissioni_eur"], sum(2.0 + 0.001 * (o["azioni"] * o["prezzo_eur"]) for o in con["operazioni"]
                                           if o["lato"] == "vendita") +
                sum(2.0 + 0.001 * (o["azioni"] * o["prezzo_eur"]) for o in con["operazioni"] if o["lato"] == "acquisto")))
netto = s.simula(dfx, i0, 1000, 2.0, 0.001, 0.26, True, stop=0.05)
verifica("con la tassa non si finisce mai sopra il caso senza tassa", netto["valore_finale_eur"] <= con["valore_finale_eur"] + 1e-9)
verifica("il registro delle operazioni quadra con la cassa finale",
         uguali(1000 - sum(o["spesa_eur"] for o in netto["operazioni"]) +
                sum(o["incasso_netto_eur"] - o["tassa_eur"] for o in netto["operazioni"]), netto["valore_finale_eur"]))
# Serie costruita a mano: 260 sedute a 100, poi 99 (sotto la media), 112 (sopra la media: segnale), 112, 105, 105, 105...
# Si compra a 112 (seduta 262); a 105 (-6,25%) il prezzo sta ancora sopra la media (circa 100): lo stop deve scattare.
sega = np.r_[np.full(260, 100.0), 99.0, 112.0, 112.0, 105.0, 105.0, 105.0, 105.0, 105.0]
ds = s.prepara(pd.DataFrame({"Close": sega}, index=pd.bdate_range("2020-01-01", periods=len(sega), name="Date")), None, 200)
ns = s.simula(ds, s.primo_indice(ds), 1000, 2.0, 0.001, 0.26, True, stop=0.05)
verifica("lo stop scatta su una serie costruita a mano", ns["n_stop"] == 1, ns["n_stop"])
verifica("acquisto a 112 alla seduta 262, vendita per stop a 105 alla seduta 264",
         [(o["i"], o["lato"], o["prezzo"]) for o in ns["operazioni"]] == [(262, "acquisto", 112.0), (264, "vendita", 105.0)],
         [(o["i"], o["lato"], o["prezzo"]) for o in ns["operazioni"]])
Cs = ds["Close"].to_numpy()
n_ok = all(Cs[o["i"] - 1] <= [x for x in ns["operazioni"] if x["lato"] == "acquisto" and x["i"] < o["i"]][-1]["prezzo"] * 0.95 + 1e-9
           for o in ns["operazioni"] if o["motivo"] == "stop loss")
verifica("ogni stop è preceduto da una chiusura a -5% o peggio sul prezzo di acquisto", n_ok)
senza_s = s.simula(ds, s.primo_indice(ds), 1000, 2.0, 0.001, 0.26, True, stop=None)
verifica("senza stop non scatta nessuno stop e si resta dentro", senza_s["n_stop"] == 0 and senza_s["n_vendite"] == 1 and senza_s["operazioni"][1]["motivo"] == "liquidazione finale")

print("3. Nessun look-ahead: cambiare il futuro non cambia gli ordini già dati")
m = n - 400
corto = dfx.iloc[:m].copy()
lungo = dfx.copy()
lungo.iloc[m:, lungo.columns.get_loc("Close")] *= 0.5                # un crollo dopo la seduta m
lungo["sma"] = lungo["Close"].rolling(200).mean()
lungo["segnale"] = (lungo["Close"] > lungo["sma"]) & lungo["sma"].notna()
a = s.simula(dfx, i0, 1000, 2.0, 0.0, 0.26, True, stop=0.05)
b = s.simula(lungo, i0, 1000, 2.0, 0.0, 0.26, True, stop=0.05)
prima_a = [(o["i"], o["lato"]) for o in a["operazioni"] if o["i"] < m]
prima_b = [(o["i"], o["lato"]) for o in b["operazioni"] if o["i"] < m]
verifica(f"gli {len(prima_a)} ordini prima della seduta {m} sono identici", prima_a == prima_b)
verifica("l'equity prima della seduta m è identica", np.allclose(a["equity"][: m - i0], b["equity"][: m - i0]))

print("4. Motore completo contro motore delle scimmie, e proprietà delle scimmie")
for fissa, perc, aliq, stop in [(0.0, 0.0, 0.0, None), (2.0, 0.0, 0.26, 0.05), (0.0, 0.001, 0.26, None), (2.0, 0.001, 0.26, 0.03)]:
    rr = s.simula(dfx, i0, 1000, fissa, perc, aliq, True, stop=stop)
    aa, bb = s.blocchi(rr)
    anni = dfx.index.year.to_numpy()
    fin, com, tas = s.valuta_blocchi(Cx, Fx, anni, aa, bb, 1000, fissa, perc, aliq)
    verifica(f"valuta_blocchi = simula (fissa {fissa}, perc {perc}, tassa {aliq}, stop {stop})",
             uguali(fin, rr["valore_finale_eur"]) and uguali(com, rr["commissioni_eur"]) and uguali(tas, rr["tasse_eur"]))
rr = s.simula(dfx, i0, 1000, 2.0, 0.0, 0.26, True, stop=0.05)
aa, bb = s.blocchi(rr)
k, D = len(aa), int((bb - aa).sum())
N = n - i0
rng2 = np.random.default_rng(3)
buoni = True
for _ in range(300):
    ia, ib = s.scimmia(k, D, N, rng2)
    buoni &= (len(ia) == k and int((ib - ia).sum()) == D and ia.min() >= 0 and ib.max() <= N - 1
              and bool(np.all(ib > ia)) and bool(np.all(ia[1:] > ib[:-1])))
verifica(f"300 scimmie con {k} periodi e {D} sedute investite: durata totale, limiti e assenza di sovrapposizioni", buoni)
ia, ib = s.scimmia(1, 50, 60, rng2)
verifica("scimmia con un solo periodo", len(ia) == 1 and ib[0] - ia[0] == 50)

print(f"\nTutti i {ok} controlli superati (dati inventati: nessuno di questi numeri è un risultato).")
