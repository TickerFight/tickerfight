"""Controlli delle funzioni dell'esperimento. Usa SOLO dati inventati: nessun numero qui è un risultato.

Si esegue prima del backtest (lo fa anche il flusso su GitHub): se un controllo fallisce, il flusso si ferma.
  1. la ricerca delle finestre su un calendario inventato, con ponti e festivi;
  2. conti fatti a mano;
  3. il motore veloce delle scimmie contro il motore completo (simulazione.py);
  4. la posizione delle scimmie: stessa durata, dentro il blocco.
"""
import numpy as np
import pandas as pd

import finestre as f
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


print("1. Ricerca delle finestre")
# Calendario inventato: giorni feriali, con il 24-25-26 dicembre e l'1 gennaio senza seduta.
giorni = pd.bdate_range("2019-06-01", "2023-03-31")
giorni = giorni[~((giorni.month == 12) & (giorni.day.isin([25, 26]))) & ~((giorni.month == 1) & (giorni.day == 1))]
ent, usc, anni = f.trova_finestre(giorni, 5, 2)
verifica("quattro finestre complete (dicembre 2019, 2020, 2021, 2022 con gennaio seguente)", list(anni) == [2019, 2020, 2021, 2022], list(anni))
for e, x, a in zip(ent, usc, anni):
    dic = [d for d in giorni if d.year == a and d.month == 12]
    gen = [d for d in giorni if d.year == a + 1 and d.month == 1]
    verifica(f"dicembre {a}: entrata alla sesta-ultima seduta, uscita alla seconda di gennaio",
             giorni[e] == dic[-6] and giorni[x] == gen[1] and x - e == 7, f"{giorni[e]} {giorni[x]}")
e0, x0, _ = f.trova_finestre(giorni, 3, 0)
verifica("con zero sedute di gennaio si esce all'ultima seduta di dicembre", all(giorni[x].month == 12 for x in x0) and all(x - e == 3 for e, x in zip(e0, x0)))
corti = giorni[giorni < "2022-12-31"]
verifica("senza il gennaio seguente la finestra non è completa", list(f.trova_finestre(corti, 5, 2)[2]) == [2019, 2020, 2021])

print("2. Conti a mano")
# Prezzi: 100 fino all'entrata, 110 all'uscita. Azioni = 499/100 = 4,99; incasso 548,9 - 1 = 547,9; plusvalenza 47,9;
# tassa 12,454; cassa finale 535,446.
C = np.array([100, 100, 100, 100, 110, 110, 110.0])
fin, tasse = f.finale_veloce(C, np.array([2022]), np.array([1]), np.array([4]), 500, 1.0, 0.26)
verifica("guadagno: cassa finale 535,446", uguali(fin, 535.446), fin)
verifica("guadagno: tassa 12,454", uguali(tasse, 12.454), tasse)
C2 = np.array([100, 100, 100, 100, 90, 90, 90.0])
fin, tasse = f.finale_veloce(C2, np.array([2022]), np.array([1]), np.array([4]), 500, 1.0, 0.26)
verifica("perdita: cassa finale = 499/100*90-1 e nessuna tassa", uguali(fin, 499 / 100 * 90 - 1) and tasse == 0.0, fin)
# Due finestre: prima una perdita (2022), poi un guadagno (2023): la perdita compensa il guadagno.
C3 = np.array([100, 100, 100, 90, 90, 90, 90, 100, 100, 110, 110.0])
fin, tasse = f.finale_veloce(C3, np.array([2022, 2023]), np.array([0, 5]), np.array([3, 9]), 500, 1.0, 0.26)
cassa1 = 499 / 100 * 90 - 1                                   # 448,1
az2 = (cassa1 - 1) / 90                                        # (azioni) comprate a 90 (prezzo C3[5])
netto2 = az2 * 110 - 1
perdita = 500 - cassa1
tassa2 = 0.26 * max(0.0, (netto2 - cassa1) - perdita)
verifica("la minusvalenza del primo anno compensa la plusvalenza del secondo", uguali(fin, netto2 - tassa2) and uguali(tasse, tassa2), f"{fin} {netto2 - tassa2}")

print("3. Motore veloce contro motore completo (dati inventati)")
rng = np.random.default_rng(11)
date = pd.bdate_range("1990-01-01", "2024-12-31")
chiusura = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, len(date))))
ent, usc, anni = f.trova_finestre(date, 5, 2)
stato = np.zeros(len(date), dtype=bool)
for e, x in zip(ent, usc):
    stato[e:x] = True
df = pd.DataFrame({"Open": chiusura, "Close": chiusura, "fx": 1.0, "segnale": np.r_[stato[1:], False]}, index=date)
completo = s.simula(df, int(ent[0]), 500, 1.0, 0.26, "chiusura", True)
veloce, tasse_v = f.finale_veloce(chiusura, date.year.to_numpy()[usc], ent, usc, 500, 1.0, 0.26)
verifica("valore finale uguale", uguali(completo["valore_finale_eur"], veloce), f"{completo['valore_finale_eur']} {veloce}")
verifica("tasse uguali", uguali(completo["tasse_eur"], tasse_v))
verifica("un acquisto e una vendita per finestra", completo["n_acquisti"] == len(ent) and completo["n_vendite"] == len(ent))
lordo = 500 * np.prod(chiusura[usc] / chiusura[ent])
senza_costi, _ = f.finale_veloce(chiusura, date.year.to_numpy()[usc], ent, usc, 500, 0.0, 0.0)
verifica("senza costi né tasse = prodotto dei rendimenti delle finestre", uguali(senza_costi, lordo))
bh = s.simula(df, int(ent[0]), 500, 0.0, 0.0, "chiusura", False)
verifica("buy & hold lordo = chiusura finale / chiusura iniziale", uguali(bh["valore_finale_eur"], 500 * chiusura[-1] / chiusura[ent[0]]))

print("4. Le scimmie")
pos = f.scimmie(chiusura, ent, 7, min(len(date), int(ent[-1]) + 252), 2000, np.random.default_rng(3))
fine = np.r_[ent[1:], min(len(date), int(ent[-1]) + 252)]
verifica("ogni scimmia ha una finestra per anno", pos.shape == (2000, len(ent)))
verifica("ogni finestra sta dentro il suo blocco", bool(np.all(pos >= ent) and np.all(pos + 7 < fine + 1)))
verifica("le finestre non si sovrappongono e restano in ordine", bool(np.all(np.diff(pos, axis=1) >= 7)))
verifica("la finestra reale è raggiungibile", bool(np.any(pos[:, 3] == ent[3])))
verifica("le scimmie coprono tutto il blocco (la media delle posizioni sta a metà)", abs(float(pos[:, 3].mean()) - (ent[3] + (fine[3] - 8 - ent[3]) / 2)) < 15)

print(f"\nTutti i {ok} controlli superati (dati inventati: nessuno di questi numeri è un risultato).")
