"""Parametri dell'articolo n. 9 - "Esecuzione a chiusura, apertura o prezzo medio".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Un backtest deve dire a che prezzo si eseguono gli ordini. Il segnale si calcola con la chiusura del giorno t; l'ordine si può eseguire (a) alla stessa chiusura
del giorno t (comodo, ma presuppone di conoscere la chiusura prima che esista: la variante «look-ahead morbido» usata da molti codici con lo shift di un giorno),
(b) all'apertura del giorno t+1, (c) al prezzo medio del giorno t+1 (media di apertura, massimo, minimo e chiusura), (d) alla chiusura del giorno t+1.
Si prova sullo SPY (ETF sull'S&P 500, prezzi corretti per i dividendi) con due regole a media mobile semplice sulla chiusura, una lenta (200 sedute) e una veloce
(20 sedute): si resta investiti se la chiusura è sopra la media, altrimenti si sta fermi (rendimento zero). Si misura quanto cambiano rendimento e Sharpe con il
prezzo di esecuzione, quanto pesa il costo per operazione, e quanta parte del rendimento dello SPY avviene di notte (dalla chiusura all'apertura successiva).
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

TICKER = "SPY"
INIZIO_DOWNLOAD = "1993-01-01"
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "spy_ohlc.csv"
FILE_METADATI = DATI / "spy_metadati.json"
DESCRIZIONE_DATI = "le aperture, i massimi, i minimi e le chiusure giornaliere dello SPY, corrette per dividendi e frazionamenti"
URL_FONTE = "https://finance.yahoo.com/quote/SPY/history/"
NOTA_COLONNA = "Prezzi corretti per dividendi (rendimento totale)"
NOMI_ESENTI = ("SPY", "S&P 500", "SMA", "OHLC")

GIORNI_ANNO = 252
MEDIE = (200, 20)                    # lunghezze delle due medie mobili: lenta e veloce
COSTO_BASE = 0.0005                  # 0,05% per ogni cambio di posizione (acquisto o vendita)
COSTI_GRIGLIA = (0.0, 0.0005, 0.001, 0.002, 0.005)
N_BOOT = 2000
BLOCCO = 21
LIVELLO_IC = 0.95
SEME = 20261030

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_PUNTI = 0.01                      # ipotesi 1: regola veloce, vantaggio della stessa chiusura sull'apertura successiva: almeno 1 punto all'anno
H2_PUNTI = 0.01                      # ipotesi 2: regola lenta, scarto massimo tra i quattro prezzi di esecuzione: meno di 1 punto
H4_QUOTA = 0.50                      # ipotesi 4: quota minima del rendimento logaritmico dello SPY che avviene di notte

IPOTESI = (
    "1) Per la regola veloce (20 sedute) eseguire alla stessa chiusura del segnale rende almeno 1 punto percentuale all'anno in più dell'apertura del giorno dopo: il lookahead morbido ha un costo grande. "
    "2) Per la regola lenta (200 sedute) i quattro prezzi di esecuzione danno rendimenti annui composti che differiscono tra loro di meno di 1 punto percentuale: una regola che scambia poco è insensibile al prezzo. "
    "3) Lo scarto tra il miglior e il peggior prezzo di esecuzione è più grande per la regola veloce che per la lenta. "
    "4) Più della metà del rendimento logaritmico totale dello SPY avviene di notte, dalla chiusura all'apertura successiva. "
    "5) Con un costo di 0,05% a ogni cambio di posizione e l'esecuzione all'apertura del giorno dopo, la regola veloce rende meno del buy & hold. "
    "6) La differenza di rendimento giornaliero tra esecuzione all'apertura e alla chiusura del giorno dopo, per la regola veloce, non si distingue dallo zero: l'intervallo di confidenza (bootstrap a blocchi) la contiene."
)
