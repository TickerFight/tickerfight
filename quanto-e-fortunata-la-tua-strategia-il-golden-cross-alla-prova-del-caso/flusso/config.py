"""Parametri dell'articolo n. 21 - "Quanto è fortunata la tua strategia?".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da
questo file, così ogni numero dell'articolo si può ricondurre a una scelta
dichiarata e nessun valore è nascosto dentro il codice.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
TICKER = "^GSPC"          # S&P 500, indice di prezzo (senza dividendi)
INIZIO_DOWNLOAD = "1927-01-01"   # Yahoo restituisce da quando ha i dati
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "gspc_giornaliero.csv"
FILE_METADATI = DATI / "gspc_metadati.json"

# --- Strategia ----------------------------------------------------------
# Regola scelta a priori e NON ottimizzata: è la coppia più citata
# (golden cross / death cross). Nessun'altra coppia è stata provata.
SMA_VELOCE = 50
SMA_LENTA = 200

# --- Convenzioni di calcolo ---------------------------------------------
GIORNI_ANNO_BORSA = 252   # per annualizzare volatilità e Sharpe
GIORNI_ANNO_CALENDARIO = 365.25   # per il rendimento annuo composto (CAGR)
TASSO_SENZA_RISCHIO = 0.0  # semplificazione dichiarata nell'articolo

# --- Test statistici ----------------------------------------------------
SEED = 20261019                 # data di scrittura, per riprodurre i risultati
N_SIMULAZIONI_CASUALI = 10_000  # strategie a timing casuale
N_BOOTSTRAP = 10_000            # ricampionamenti bootstrap
BLOCCO_BOOTSTRAP = 21           # giorni di borsa per blocco (circa un mese)
BLOCCHI_ROBUSTEZZA = (5, 63)    # altre lunghezze di blocco, per controllo
LIVELLO_CONFIDENZA = 0.95

# Sotto-periodi: (etichetta, prima data inclusa, ultima data inclusa)
SOTTOPERIODI = [
    ("dall'inizio al 1969", None, "1969-12-31"),
    ("1970-1999", "1970-01-01", "1999-12-31"),
    ("dal 2000 a oggi", "2000-01-01", None),
]

# Esempio didattico dell'articolo: primo segnale di uscita dopo questa data e successivo rientro
ESEMPIO_DAL = "2007-06-01"
