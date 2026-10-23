"""Parametri dell'articolo n. 163 - "Il Santa Claus rally".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Finestra: investiti dalla chiusura della sesta-ultima seduta di dicembre (cioè per le ultime cinque sedute dell'anno) fino
alla chiusura della seconda seduta di gennaio (cioè per le prime due sedute del nuovo anno): sette sedute in tutto.
Il calendario è noto in anticipo: nessun look-ahead. Il resto dell'anno si sta in cassa (che non rende).
Confronto con il buy & hold sullo stesso indice, con finestre di sette sedute qualunque (generiche) e con migliaia di
scimmie che hanno la stessa dieta (una finestra di sette sedute per anno, piazzata a caso dentro il suo anno).
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: indici azionari (ticker Yahoo Finance, nome, valuta) ---------------------------------------------------
# Scelti a priori, prima di guardare i dati: tre indici americani e quattro tra Europa e Giappone. Sono tutti indici di
# prezzo (i dividendi non sono contati, né per la strategia né per il buy & hold). Se Yahoo non restituisce abbastanza
# storia l'indice viene scartato e l'articolo lo dichiara.
INDICI = [
    ("^GSPC", "S&P 500 (Stati Uniti)", "USD"),
    ("^DJI", "Dow Jones (Stati Uniti)", "USD"),
    ("^IXIC", "Nasdaq Composite (Stati Uniti)", "USD"),
    ("^GDAXI", "DAX (Germania)", "EUR"),
    ("^FTSE", "FTSE 100 (Regno Unito)", "GBP"),
    ("^FCHI", "CAC 40 (Francia)", "EUR"),
    ("^N225", "Nikkei 225 (Giappone)", "JPY"),
]
INIZIO_DOWNLOAD = "1950-01-01"
NOMI_ESENTI = ("S&P 500", "FTSE 100", "CAC 40", "Nikkei 225")   # nomi di indici con cifre: non sono dati dell'analisi
FUSO_BORSA = "America/New_York"
ANNI_MINIMI = 15           # sotto questa soglia di finestre complete l'indice viene scartato
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere di sette indici azionari"
URL_FONTE = "https://finance.yahoo.com/"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Scenario dell'investitore (come gli articoli precedenti) -------------------
CAPITALE = 500.0
COMMISSIONE = 1.0
ALIQUOTA = 0.26
MODO = "chiusura"

# --- La finestra del Santa Claus rally -----------------------------------------------------------------------------
SEDUTE_DICEMBRE = 5        # ultime sedute di dicembre incluse nella finestra
SEDUTE_GENNAIO = 2         # prime sedute di gennaio incluse nella finestra
ANNO_DIVISIONE = 2000      # "prima" = finestre che iniziano a dicembre fino al 1999; "dopo" = dal dicembre 2000
# Griglia di varianti, solo per misurare quanto il risultato dipende dalla definizione della finestra
GRIGLIA_DICEMBRE = (3, 4, 5, 6, 7)
GRIGLIA_GENNAIO = (0, 1, 2, 3, 4)

# --- Test statistici -------------------------------------------------------------------
SEME = 20261022
N_SCIMMIE = 5000
N_BOOTSTRAP = 5000
LIVELLO_CONFIDENZA = 0.95

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) In almeno cinque indici su sette il rendimento medio della finestra di sette sedute è positivo e più alto di quello "
    "medio di una finestra di sette sedute qualunque. "
    "2) Dopo costi e tasse la strategia chiude sotto il buy & hold in tutti gli indici, perché sta sul mercato sette sedute "
    "all'anno e il resto del tempo resta in cassa. "
    "3) Dopo la correzione di Holm, in meno della metà degli indici la finestra batte le scimmie con la stessa dieta con una "
    "significatività del cinque per cento: con una sola finestra di sette sedute all'anno e pochi decenni di dati, l'effetto "
    "si distingue dalla fortuna meno di quanto si racconta. "
    "4) Dopo il 1999 il rendimento medio della finestra è più basso di prima in almeno metà degli indici."
)
