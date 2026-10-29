"""Parametri dell'articolo n. 204 - "Growth contro value".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero dell'articolo si può
ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Due ETF quotati in dollari, con i dividendi reinvestiti (prezzo "Adj Close" di Yahoo Finance): IWF (iShares Russell 1000 Growth, le grandi società americane
«di crescita») e IWD (iShares Russell 1000 Value, le grandi società americane «di valore»). Si confrontano sul periodo in cui esistono tutti e due (da maggio 2000).
Confronti: rendimento e rischio su tutto il periodo, finestre mobili (3, 5 e 10 anni), tre fasi di crisi fissate in anticipo, persistenza del vincitore
(confronto con il caso) e scimmie (una scelta casuale tra i due ETF ogni mese).
Nessun look-ahead: nel test di persistenza la "previsione" usa solo i rendimenti dei cinque anni che finiscono nel mese t.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: ETF (ticker Yahoo Finance, nome, sigla) ----------------------------------------------------------------
ETF = [
    ("IWF", "iShares Russell 1000 Growth", "IWF"),
    ("IWD", "iShares Russell 1000 Value", "IWD"),
]
INIZIO_DOWNLOAD = "2000-01-01"
NOMI_ESENTI = ("IWF", "IWD", "Russell 1000")
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
H4_MIN = 0.40                    # ipotesi 4: IWF prima su finestre di cinque anni in una quota tra 40% e 70%
H4_MAX = 0.70

# --- Test statistici -----------------------------------------------------------------------------------------------
SEME = 20261029
N_SCIMMIE = 5000
N_PERMUTAZIONI = 5000
N_BOOTSTRAP = 2000
BLOCCO_BOOTSTRAP = 21
LIVELLO_CONFIDENZA = 0.95

# --- Fasi di crisi, fissate a priori (date di calendario) -----------------------------------------------------------
CRISI = [
    ("Scoppio della bolla dot-com", "2000-06-01", "2002-10-09"),
    ("Crisi finanziaria", "2007-10-09", "2009-03-09"),
    ("Rialzo dei tassi del 2022", "2022-01-03", "2022-10-12"),
]

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------------
IPOTESI = (
    "1) Nel periodo comune il rendimento annuo composto di IWF (crescita) è più alto di quello di IWD (valore). "
    "2) La perdita massima dal picco di IWF è più profonda di quella di IWD. "
    "3) La differenza di Sharpe tra IWF e IWD non si distingue dallo zero: l'intervallo di confidenza al 95% la contiene. "
    "4) Su finestre mobili di cinque anni la leadership ruota: IWF è davanti in una quota di finestre compresa tra il 40% e il 70%. "
    "5) L'ETF vincitore nei cinque anni precedenti vince anche nei cinque successivi in una quota di mesi non distinguibile dal caso: il p-value del test di permutazione è sopra il 5%. "
    "6) Nello scoppio della bolla dot-com e nel rialzo dei tassi del 2022 IWF perde più di IWD; nella crisi finanziaria perde meno."
)
