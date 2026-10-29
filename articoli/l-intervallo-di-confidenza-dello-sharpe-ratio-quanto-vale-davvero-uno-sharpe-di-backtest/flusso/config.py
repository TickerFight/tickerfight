"""Parametri dell'articolo n. 82 - "L'intervallo di confidenza dello Sharpe ratio".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Il rapporto di Sharpe (rendimento medio diviso deviazione standard, annualizzato, tasso privo di rischio zero) è la misura di qualità di una strategia più citata, e di
solito è riportato come un numero. Qui se ne calcola l'incertezza sull'S&P 500 (indice di prezzo, dal 1927, rendimenti semplici giornalieri) con quattro intervalli al 95%:
la formula di Lo (rendimenti indipendenti e normali), la formula di Mertens (corretta per asimmetria e code spesse), il bootstrap sui giorni e il bootstrap a blocchi
circolari di 21 sedute. Si calcolano sull'intero periodo e sugli ultimi 10, 20, 30 e 50 anni. Poi si controlla se la formula è onesta: su finestre che partono da ogni mese, quante
volte l'intervallo della finestra contiene lo Sharpe di tutte le altre sedute (la «copertura»)? Infine: quanti anni servono per restringere l'intervallo, e se lo Sharpe
della regola «investiti sopra la media mobile a 200 sedute» è davvero diverso da quello del buy & hold (bootstrap a blocchi sulla differenza, con le stesse date).
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
NOMI_ESENTI = ("S&P 500", "Lo", "Mertens", "Sharpe")

GIORNI_ANNO = 252
FINESTRE_ANNI = (10, 20, 30, 50)
COPERTURA_ANNI = (5, 10, 20, 30)
MEDIA_REGOLA = 200
Z95 = 1.959964
LIVELLO_IC = 0.95
N_BOOT = 2000
BLOCCO = 21
SEME = 20261030

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_AMPIEZZA = 0.50               # ipotesi 1: intero periodo, ampiezza dell'intervallo di Lo sotto 0,5
H2_AMPIEZZA = 1.00               # ipotesi 2: ultimi 10 anni, ampiezza dell'intervallo di Lo oltre 1,0
H3_DIFF = 0.05                   # ipotesi 3: Mertens e Lo differiscono, in ampiezza, di meno del 5%
H5_COPERTURA = 0.90              # ipotesi 5: copertura onesta con finestre di 10 anni almeno 90%

IPOTESI = (
    "1) Sull'intero periodo l'intervallo di confidenza al 95% dello Sharpe, con la formula di Lo, è largo meno di 0,5. "
    "2) Sugli ultimi 10 anni lo stesso intervallo è largo più di 1,0: un decennio non basta a distinguere uno Sharpe buono da uno mediocre. "
    "3) L'intervallo di Mertens, che tiene conto di asimmetria e code spesse, ha un'ampiezza che differisce da quella di Lo di meno del 5% sull'intero periodo: a frequenza giornaliera la correzione conta poco. "
    "4) Il bootstrap a blocchi dà un intervallo più largo di quello del bootstrap sui giorni, sull'intero periodo. "
    "5) La formula di Lo è onesta: con finestre di 10 anni la copertura onesta (riferimento: lo Sharpe di tutte le altre sedute) è almeno del 90%. "
    "6) Lo Sharpe della regola a media mobile a 200 sedute non si distingue da quello del buy & hold: l'intervallo bootstrap a blocchi della differenza contiene lo zero."
)
