"""Parametri dell'articolo n. 186 - "Equal weight contro market cap".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero dell'articolo si può
ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Due ETF quotati in dollari, con i dividendi reinvestiti (prezzo "Adj Close" di Yahoo Finance): SPY (le 500 maggiori società americane, ognuna pesata per
capitalizzazione) e RSP (le stesse 500 società, tutte con lo stesso peso, ribilanciate ogni trimestre). Si confrontano sul periodo in cui esistono tutti e due
(da maggio 2003). Confronti: rendimento e rischio su tutto il periodo, finestre mobili (3, 5 e 10 anni), tre fasi di crisi fissate in anticipo, persistenza
del vincitore (confronto con il caso) e scimmie (una scelta casuale tra i due ETF ogni mese).
Nessun look-ahead: nel test di persistenza la "previsione" usa solo i rendimenti dei cinque anni che finiscono nel mese t.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: ETF (ticker Yahoo Finance, nome, sigla) ----------------------------------------------------------------
ETF = [
    ("RSP", "Invesco S&P 500 Equal Weight", "RSP"),
    ("SPY", "SPDR S&P 500", "SPY"),
]
INIZIO_DOWNLOAD = "2003-01-01"
NOMI_ESENTI = ("S&P 500", "RSP", "SPY")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere aggiustate di due ETF quotati negli Stati Uniti"
URL_FONTE = "https://finance.yahoo.com/"
COLONNA_PREZZO = "Adj Close"     # prezzo con dividendi reinvestiti
ANNI_MINIMI = 10


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Parametri dell'analisi -----------------------------------------------------------------------------------------
GIORNI_ANNO = 252
CAPITALE = 500.0
FINESTRE_ANNI = [3, 5, 10]
FINESTRA_RIF = 5
H4_MIN = 0.30                    # ipotesi 4: RSP prima su finestre di cinque anni in una quota tra 30% e 60%
H4_MAX = 0.60

# --- Test statistici -----------------------------------------------------------------------------------------------
SEME = 20261029
N_SCIMMIE = 5000
N_PERMUTAZIONI = 5000
N_BOOTSTRAP = 2000
BLOCCO_BOOTSTRAP = 21
LIVELLO_CONFIDENZA = 0.95

# --- Fasi di crisi, fissate a priori (date di calendario) -----------------------------------------------------------
CRISI = [
    ("Crisi finanziaria", "2007-10-09", "2009-03-09"),
    ("Crollo del coronavirus", "2020-02-19", "2020-03-23"),
    ("Rialzo dei tassi del 2022", "2022-01-03", "2022-10-12"),
]

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------------
IPOTESI = (
    "1) Nel periodo comune il rendimento annuo composto di SPY è più alto di quello di RSP. "
    "2) RSP ha una volatilità annua più alta e una perdita massima più profonda di quelle di SPY. "
    "3) La differenza di Sharpe tra RSP e SPY non si distingue dallo zero: l'intervallo di confidenza al 95% la contiene. "
    "4) Su finestre mobili di cinque anni la leadership ruota: RSP è davanti in una quota di finestre compresa tra il 30% e il 60%. "
    "5) L'ETF vincitore nei cinque anni precedenti perde più spesso di quanto vinca nei cinque successivi: la quota di mesi in cui vince ancora è sotto la metà. "
    "6) Nella crisi finanziaria e nel crollo del coronavirus RSP perde più di SPY, mentre nel rialzo dei tassi del 2022 perde meno."
)
