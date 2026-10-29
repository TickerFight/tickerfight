"""Parametri dell'articolo n. 83 - "L'intervallo di confidenza del CAGR".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Il CAGR (rendimento annuo composto) di una storia è una stima: con altri anni sarebbe stato diverso. Qui si misura quanto è incerto, sull'S&P 500
(indice di prezzo, senza dividendi, dal 1927). Tre modi di calcolare l'intervallo di confidenza al 95%: (1) formula, dall'errore standard della media dei rendimenti
logaritmici (σ diviso radice di n); (2) bootstrap sui giorni, pescando i rendimenti con reinserimento; (3) bootstrap a blocchi circolari di 21 sedute, che
conserva i raggruppamenti di volatilità e l'eventuale memoria. Si calcola sull'intero periodo e sugli ultimi 10, 20, 30 e 50 anni. Poi si controlla che l'intervallo
sia onesto: su finestre che partono da ogni mese, quante volte l'intervallo della finestra contiene il CAGR dell'intero periodo (la «copertura»)? Infine: quanti anni
servirebbero per restringere l'intervallo a più o meno uno, due o mezzo punto percentuale?
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

TICKER = "^GSPC"
INIZIO_DOWNLOAD = "1927-01-01"
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "gspc_giornaliero.csv"
FILE_METADATI = DATI / "gspc_metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere dell'indice S&P 500"
URL_FONTE = "https://finance.yahoo.com/quote/%5EGSPC/history/"
NOTA_COLONNA = "Si usano solo le chiusure; i dividendi non sono considerati"
NOMI_ESENTI = ("S&P 500", "CAGR", "σ", "Newey-West")

GIORNI_ANNO = 252
FINESTRE_ANNI = (10, 20, 30, 50)                # ultime N anni di dati, oltre all'intero periodo
COPERTURA_ANNI = (5, 10, 20, 30)               # lunghezze delle finestre per il controllo di copertura
Z95 = 1.959964
LIVELLO_IC = 0.95
N_BOOT = 2000
BLOCCO = 21
SEME = 20261030

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_AMPIEZZA = 0.05               # ipotesi 1: intero periodo, ampiezza dell'intervallo bootstrap sui giorni oltre 5 punti
H2_AMPIEZZA = 0.20               # ipotesi 2: ultimi 10 anni, ampiezza dell'intervallo (formula) oltre 20 punti
H3_RAPPORTO_MIN, H3_RAPPORTO_MAX = 0.90, 1.20   # ipotesi 3: ampiezza a blocchi / ampiezza sui giorni tra 0,9 e 1,2
H4_ANNI = 500                    # ipotesi 4: per un intervallo di più o meno un punto servono oltre 500 anni
H5_COPERTURA = 0.95              # ipotesi 5: con finestre di 20 anni la copertura è sotto il 95%

IPOTESI = (
    "1) Sull'intero periodo l'intervallo di confidenza al 95% del CAGR, calcolato con il bootstrap sui giorni, è largo più di 5 punti percentuali. "
    "2) Sugli ultimi 10 anni l'intervallo (formula) è largo più di 20 punti percentuali: un decennio dice quasi nulla sul rendimento atteso. "
    "3) Il bootstrap a blocchi dà un intervallo di ampiezza tra 0,9 e 1,2 volte quella del bootstrap sui giorni sull'intero periodo: la memoria dei rendimenti giornalieri cambia poco l'incertezza sul CAGR. "
    "4) Per restringere l'intervallo del CAGR a più o meno un punto percentuale servirebbero oltre 500 anni di dati. "
    "5) Su finestre di 20 anni che partono da ogni mese, l'intervallo della finestra contiene il CAGR dell'intero periodo in meno del 95% dei casi: l'intervallo di una sola storia è più ottimista della realtà. "
    "6) Il CAGR degli ultimi 30 anni sta dentro l'intervallo (bootstrap a blocchi) dell'intero periodo."
)
