"""Controlli del motore di simulazione. Usa SOLO dati inventati: nessun numero qui è un risultato.

Si esegue prima del backtest (lo fa anche il flusso su GitHub): se un controllo fallisce, il flusso si ferma.
  1. conti fatti a mano (guadagno, perdita, rotazione, commissione proporzionale, cambio, divisione in parti uguali, minusvalenze);
  2. confronto con una formula indipendente (lordo = prodotto dei rendimenti degli strumenti scelti);
  3. nessun look-ahead: cambiare il futuro non cambia gli ordini già dati;
  4. coerenza tra il motore con serie e senza serie, e proprietà delle scimmie (stessi giorni, stesso numero di ordini).
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


def mat(righe, fx=1.0):
    C = np.array(righe, float)
    return C, np.full(len(C), fx), np.full(len(C), 2020)


print("1. Conti a mano")
# Compro lo strumento 0 alla seduta 1 a 100 e tengo fino alla fine (120). Fissa 2: investo 998, azioni 9,98; incasso 1.197,6;
# netto 1.195,6; plusvalenza 195,6; tassa 50,856; cassa finale 1.144,744.
C, FX, A = mat([[100, 100], [100, 100], [100, 100], [120, 100], [120, 110]])
r = s.simula(C, FX, A, {1: (0,)}, 1, 1000, 2.0, 0.0, 0.26)
verifica("guadagno: cassa finale 1.144,744", uguali(r["valore_finale_eur"], 1144.744), r["valore_finale_eur"])
verifica("guadagno: tassa 50,856", uguali(r["tasse_eur"], 50.856))
verifica("guadagno: 2 ordini da 2 euro", uguali(r["commissioni_eur"], 4.0) and r["n_acquisti"] == 1 and r["n_vendite"] == 1)

# Rotazione: alla seduta 3 passo dallo strumento 0 (a 120) allo strumento 1 (a 100), che alla fine vale 110.
r = s.simula(C, FX, A, {1: (0,), 3: (1,)}, 1, 1000, 2.0, 0.0, 0.26)
cassa3 = 1144.744
inv = cassa3 - 2.0
az = inv / 100
netto = az * 110 - 2.0
atteso = netto - 0.26 * (netto - cassa3)
verifica("rotazione: vendita, acquisto e liquidazione con tassa", uguali(r["valore_finale_eur"], atteso), (r["valore_finale_eur"], atteso))
verifica("rotazione: 2 acquisti e 2 vendite", r["n_acquisti"] == 2 and r["n_vendite"] == 2)
verifica("rotazione: 4 ordini da 2 euro", uguali(r["commissioni_eur"], 8.0))

# Commissione proporzionale 0,1%: investo 1000/1,001.
inv = 1000 / 1.001
lordo = inv / 100 * 120
netto = lordo * (1 - 0.001)
r = s.simula(C, FX, A, {1: (0,)}, 1, 1000, 0.0, 0.001, 0.26)
verifica("commissione proporzionale: cassa finale", uguali(r["valore_finale_eur"], netto - 0.26 * (netto - 1000)), r["valore_finale_eur"])
verifica("commissione proporzionale: costo = 0,1% di acquisto e vendita", uguali(r["commissioni_eur"], 0.001 * inv + 0.001 * lordo))

# Perdita: nessuna tassa, e la minusvalenza compensa una plusvalenza successiva.
Cp, FXp, Ap = mat([[100, 100], [100, 100], [90, 100], [90, 100], [90, 130]])
r = s.simula(Cp, FXp, Ap, {1: (0,)}, 1, 1000, 2.0, 0.0, 0.26)
verifica("perdita: cassa finale = 998/100*90-2 e nessuna tassa", uguali(r["valore_finale_eur"], 9.98 * 90 - 2) and r["tasse_eur"] == 0.0)
r = s.simula(Cp, FXp, Ap, {1: (0,), 3: (1,)}, 1, 1000, 0.0, 0.0, 0.26)
cassa = 1000 * 0.9                       # vendita in perdita a 90: minusvalenza 100, nessuna tassa
fin_lordo = cassa * 130 / 100
tassa = 0.26 * max(0.0, (fin_lordo - cassa) - 100)
verifica("minusvalenza riportata sulla plusvalenza dopo la rotazione", uguali(r["valore_finale_eur"], fin_lordo - tassa), (r["valore_finale_eur"], fin_lordo - tassa))

# Cambio variabile: acquisto con cambio 1,00 e vendita con cambio 1,25 -> perdita da cambio, nessuna tassa.
Cc, _, Ac = mat([[100, 100]] * 3 + [[120, 100]] * 3)
FXc = np.array([1.0, 1.0, 1.0, 1.0, 1.25, 1.25])
r = s.simula(Cc, FXc, Ac, {1: (0,)}, 1, 1000, 2.0, 0.0, 0.26)
verifica("cambio: perdita da cambio, nessuna tassa", uguali(r["valore_finale_eur"], 9.98 * 120 / 1.25 - 2) and r["tasse_eur"] == 0.0, r["valore_finale_eur"])
Cc2, FXc2, Ac2 = mat([[100, 100]] * 3 + [[120, 100]] * 3, fx=1.25)
r = s.simula(Cc2, FXc2, Ac2, {1: (0,)}, 1, 1000, 2.0, 0.0, 0.26)
verifica("cambio costante: stesso risultato in euro", uguali(r["valore_finale_eur"], 1144.744))

# Tre strumenti in parti uguali: 1000 diviso 3, commissione 2 su ogni acquisto.
C3, FX3, A3 = mat([[100, 50, 10]] * 3 + [[110, 50, 20]])
r = s.simula(C3, FX3, A3, {1: (0, 1, 2)}, 1, 1000, 2.0, 0.0, 0.0)
quota = 1000 / 3
fin = sum(((quota - 2) / p0) * p1 - 2 for p0, p1 in [(100, 110), (50, 50), (10, 20)])
verifica("tre strumenti in parti uguali, lordo di tasse", uguali(r["valore_finale_eur"], fin), (r["valore_finale_eur"], fin))
verifica("tre strumenti: 3 acquisti, 3 vendite, 12 euro di commissioni", r["n_acquisti"] == 3 and r["n_vendite"] == 3 and uguali(r["commissioni_eur"], 12.0))

# Rotazione parziale: tengo A e B, cambio C con D. Compra D con il solo ricavato di C.
C4, FX4, A4 = mat([[10, 10, 10, 10]] * 5)
r = s.simula(C4, FX4, A4, {1: (0, 1, 2), 3: (0, 1, 3)}, 1, 900, 0.0, 0.0, 0.0)
verifica("rotazione parziale: 3 acquisti iniziali + 1, 1 vendita + 3 finali", r["n_acquisti"] == 4 and r["n_vendite"] == 4, (r["n_acquisti"], r["n_vendite"]))
verifica("rotazione parziale a prezzi fermi: valore invariato", uguali(r["valore_finale_eur"], 900.0))

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
date = pd.bdate_range("2005-01-03", "2026-10-20")
n = len(date)
m = 9
ret = rng.normal(0.0003, 0.012, (n, m)) + rng.normal(0, 0.004, (n, 1))
C = 100 * np.exp(np.cumsum(ret, axis=0))
FX = 1.1 * np.exp(np.cumsum(rng.normal(0, 0.003, n)))
A = date.year.to_numpy()
colonne = list(range(m))
fm = s.fine_mese(date)
verifica("fine mese: l'ultima seduta di ogni mese e nessun'altra", all(date[t].month != date[t + 1].month for t in fm) and len(fm) == len(set(zip(date.year, date.month))) - 1)
t_min = 252
piano = s.piano_rotazione(C, date, 126, 1, t_min, colonne)
i0 = min(piano)
verifica("la prima esecuzione è il primo giorno dopo il primo fine mese con almeno 252 sedute", date[i0 - 1].month != date[i0].month and i0 - 1 >= t_min)
ok_arg = True
for i, tgt in piano.items():
    t = i - 1
    rend = C[t] / C[t - 126] - 1
    ok_arg &= tgt[0] == int(np.argmax(rend))
verifica("il settore scelto è quello con il rendimento più alto delle ultime 126 sedute alla chiusura di t", ok_arg)
piano3 = s.piano_rotazione(C, date, 126, 3, t_min, colonne)
verifica("la regola a tre settori sceglie i tre migliori", all(set(tgt) == set(np.argsort(-(C[i - 1] / C[i - 1 - 126] - 1))[:3]) for i, tgt in piano3.items()))
r = s.simula(C, FX, A, piano, i0, 1000, 0.0, 0.0, 0.0)
chiavi = sorted(piano)
formula = 1000.0
for a, b in zip(chiavi, chiavi[1:] + [n - 1]):
    c = piano[a][0]
    formula *= (C[b, c] / FX[b]) / (C[a, c] / FX[a])
verifica("rotazione a un settore, lordo = prodotto dei rendimenti in euro", uguali(r["valore_finale_eur"], formula), (r["valore_finale_eur"], formula))
r3 = s.simula(C, FX, A, piano3, i0, 1000, 0.0, 0.0, 0.0)
verifica("equity iniziale = capitale e finale coerente con la cassa", uguali(r3["equity"][0], 1000.0) and uguali(r3["equity"][-1], r3["valore_finale_eur"]))
bh = s.simula(C, FX, A, {i0: (0,)}, i0, 1000, 0.0, 0.0, 0.0)
verifica("buy & hold lordo con cambio variabile", uguali(bh["valore_finale_eur"], 1000 * (C[-1, 0] / FX[-1]) / (C[i0, 0] / FX[i0])))
eq = s.simula(C, FX, A, {i0: tuple(colonne)}, i0, 1000, 0.0, 0.0, 0.0)
atteso = sum((1000 / m) * (C[-1, c] / FX[-1]) / (C[i0, c] / FX[i0]) for c in colonne)
verifica("nove strumenti tenuti in parti uguali, lordo", uguali(eq["valore_finale_eur"], atteso))

con = s.simula(C, FX, A, piano3, i0, 1000, 2.0, 0.001, 0.0)
verifica("commissioni = 2 euro + 0,1% dell'importo, ordine per ordine",
         uguali(con["commissioni_eur"], sum(2.0 + 0.001 * (o["azioni"] * C[o["i"], o["col"]] / FX[o["i"]]) for o in con["operazioni"])))
netto = s.simula(C, FX, A, piano3, i0, 1000, 2.0, 0.001, 0.26)
verifica("con la tassa non si finisce mai sopra il caso senza tassa", netto["valore_finale_eur"] <= con["valore_finale_eur"] + 1e-9)
verifica("il registro delle operazioni quadra con la cassa finale",
         uguali(1000 - sum(o.get("spesa_eur", 0.0) for o in netto["operazioni"]) +
                sum(o.get("incasso_netto_eur", 0.0) - o.get("tassa_eur", 0.0) for o in netto["operazioni"]), netto["valore_finale_eur"]))
snella = s.simula(C, FX, A, piano3, i0, 1000, 2.0, 0.001, 0.26, serie=False)
verifica("motore senza serie = motore con serie",
         uguali(snella["valore_finale_eur"], netto["valore_finale_eur"]) and uguali(snella["commissioni_eur"], netto["commissioni_eur"])
         and uguali(snella["tasse_eur"], netto["tasse_eur"]) and snella["n_acquisti"] == netto["n_acquisti"])

print("3. Nessun look-ahead: cambiare il futuro non cambia gli ordini già dati")
cut = n - 400
C2 = C.copy()
C2[cut:] *= rng.uniform(0.3, 1.7, (n - cut, m))
p2 = s.piano_rotazione(C2, date, 126, 3, t_min, colonne)
prima_a = {i: t for i, t in piano3.items() if i < cut}
prima_b = {i: t for i, t in p2.items() if i < cut}
verifica(f"le {len(prima_a)} decisioni prima della seduta {cut} sono identiche", prima_a == prima_b)
a = s.simula(C, FX, A, piano3, i0, 1000, 2.0, 0.0, 0.26)
b = s.simula(C2, FX, A, p2, i0, 1000, 2.0, 0.0, 0.26)
verifica("l'equity prima della seduta del cambiamento è identica", np.allclose(a["equity"][: cut - i0], b["equity"][: cut - i0]))

print("4. Scimmie: stessi giorni, stesso numero di ordini")
buoni = True
rng2 = np.random.default_rng(3)
for pr in (piano, piano3):
    reale = s.simula(C, FX, A, pr, i0, 1000, 2.0, 0.0, 0.26, serie=False)
    for _ in range(100):
        sc = s.scimmia_piano(pr, colonne, rng2)
        r_m = s.simula(C, FX, A, sc, i0, 1000, 2.0, 0.0, 0.26, serie=False)
        buoni &= (sorted(sc) == sorted(pr) and all(len(set(sc[i])) == len(pr[i]) for i in pr)
                  and r_m["n_acquisti"] == reale["n_acquisti"] and r_m["n_vendite"] == reale["n_vendite"])
verifica("100 scimmie per regola (1 e 3 settori): stessi giorni di ordine, settori distinti, stesso numero di ordini", buoni)
vari = {tuple(s.scimmia_piano(piano, colonne, rng2)[i0]) for _ in range(200)}
verifica("le scimmie scelgono settori diversi tra loro", len(vari) > 5)

print(f"\nTutti i {ok} controlli superati (dati inventati: nessuno di questi numeri è un risultato).")
