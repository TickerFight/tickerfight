"""Parametri dell'articolo n. 205 - "Azioni contro obbligazioni su orizzonti diversi".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero dell'articolo si può
ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Due fondi indicizzati Vanguard quotati in dollari, con i dividendi e le cedole reinvestiti (prezzo "Adj Close" di Yahoo Finance):
VFINX (Vanguard 500 Index, le azioni americane dell'S&P 500) e VBMFX (Vanguard Total Bond Market Index, le obbligazioni americane
investment grade). Si confrontano sul periodo in cui esistono tutti e due (da fine 1986), che permette finestre fino a 20 anni.
Confronti: rendimento e rischio su tutto il periodo, finestre mobili (5, 10 e 20 anni), tre crolli azionari e il 2022 fissati in anticipo,
scimmie (una scelta casuale tra i due fondi ogni mese).
Nessun look-ahead: sono confronti tra buy & hold; ogni finestra usa solo rendimenti già avvenuti alla sua data finale.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: fondi (ticker Yahoo Finance, nome, sigla) -----------------------------------------------------------------
ETF = [
    ("VFINX", "Vanguard 500 Index (azioni USA)", "AZIONI"),
    ("VBMFX", "Vanguard Total Bond Market Index (obbligazioni USA)", "OBBLIG"),
]
INIZIO_DOWNLOAD = "1986-01-01"
NOMI_ESENTI = ("VFINX", "VBMFX", "AZIONI", "OBBLIG", "S&P 500", "Vanguard 500 Index", "Vanguard Total Bond Market Index")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "i valori giornalieri aggiustati di due fondi indicizzati Vanguard, uno sulle azioni e uno sulle obbligazioni americane"
URL_FONTE = "https://finance.yahoo.com/"
COLONNA_PREZZO = "Adj Close"     # prezzo con dividendi e cedole reinvestiti
ANNI_MINIMI = 25


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Parametri dell'analisi -----------------------------------------------------------------------------------------
GIORNI_ANNO = 252
CAPITALE = 500.0
FINESTRE_ANNI = [5, 10, 20]
FINESTRA_RIF = 10                # finestra mostrata nel grafico
H2_MIN = 0.90                    # ipotesi 2: azioni davanti in almeno il 90% delle finestre di venti anni
H4_SOGLIA = 0.10                 # ipotesi 4: la perdita massima delle obbligazioni supera il 10%

# --- Test statistici -----------------------------------------------------------------------------------------------
SEME = 20261101
N_SCIMMIE = 5000
N_BOOTSTRAP = 2000
BLOCCO_BOOTSTRAP = 21
LIVELLO_CONFIDENZA = 0.95

# --- Fasi, fissate a priori (date di calendario) --------------------------------------------------------------------
CRISI = [
    ("Scoppio della bolla dot-com", "2000-06-01", "2002-10-09"),
    ("Crisi finanziaria", "2007-10-09", "2009-03-09"),
    ("Crollo del Covid", "2020-02-19", "2020-03-23"),
    ("Rialzo dei tassi del 2022", "2022-01-03", "2022-10-12"),
]
N_CROLLI_AZIONARI = 3            # le prime tre fasi sono crolli azionari; la quarta è il rialzo dei tassi

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------------
IPOTESI = (
    "1) La quota di finestre in cui le azioni battono le obbligazioni cresce con l'orizzonte: quota a 5 anni < quota a 10 anni < quota a 20 anni. "
    "2) Su finestre di venti anni le azioni battono le obbligazioni in almeno il 90% dei casi. "
    "3) Il peggior rendimento annuo delle azioni è negativo su finestre di cinque anni ed è positivo su finestre di venti anni. "
    "4) Anche le obbligazioni hanno una perdita massima dal picco superiore al 10%. "
    "5) La differenza di Sharpe tra azioni e obbligazioni non si distingue dallo zero: l'intervallo di confidenza al 95% la contiene. "
    "6) Nei tre crolli azionari (bolla dot-com, crisi finanziaria, Covid) le obbligazioni rendono più delle azioni; nel rialzo dei tassi del 2022 perdono tutte e due."
)
