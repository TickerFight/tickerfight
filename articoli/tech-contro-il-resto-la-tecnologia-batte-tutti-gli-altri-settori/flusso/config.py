"""Parametri dell'articolo n. 363 - "Tech contro il resto".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero dell'articolo si può
ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Tecnologia (XLK) contro il resto: la media, con pesi uguali e ribilanciata ogni giorno, degli altri otto ETF settoriali SPDR
(materiali, energia, finanza, industriali, beni di consumo di base, servizi di pubblica utilità, sanità, beni di consumo
discrezionali). Sono ETF quotati in dollari; si usa la chiusura (rendimenti di prezzo, senza dividendi) dal dicembre 1998, quando
esistono tutti e nove. Confronti: rendimento e rischio su tutto il periodo, finestre mobili (3, 5 e 10 anni), tre fasi di crisi fissate
in anticipo, persistenza del vincitore (confronto con il caso) e scimmie (una scelta casuale tra i due ogni mese).
Nessun look-ahead: nel test di persistenza la "previsione" usa solo i rendimenti dei cinque anni che finiscono nel mese t.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: i nove ETF settoriali (ticker Yahoo Finance, nome, sigla) ---------------------------------------------------
ETF = [
    ("XLB", "materiali", "XLB"),
    ("XLE", "energia", "XLE"),
    ("XLF", "finanza", "XLF"),
    ("XLI", "industriali", "XLI"),
    ("XLK", "tecnologia", "XLK"),
    ("XLP", "beni di consumo di base", "XLP"),
    ("XLU", "servizi di pubblica utilità", "XLU"),
    ("XLV", "sanità", "XLV"),
    ("XLY", "beni di consumo discrezionali", "XLY"),
]
INIZIO_DOWNLOAD = "1998-12-01"
NOMI_ESENTI = ("S&P 500", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere dei nove ETF settoriali SPDR"
URL_FONTE = "https://finance.yahoo.com/"
COLONNA_PREZZO = "Close"         # solo prezzo (dividendi non reinvestiti)
ANNI_MINIMI = 10


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Parametri dell'analisi -----------------------------------------------------------------------------------------
GIORNI_ANNO = 252
CAPITALE = 500.0
FINESTRE_ANNI = [3, 5, 10]
FINESTRA_RIF = 5
H2_DD_PUNTI = 0.20               # ipotesi 2: perdita massima della tecnologia più profonda di quella del resto di almeno 20 punti percentuali
H4_MIN = 0.40                    # ipotesi 4: la tecnologia prima su finestre di cinque anni in una quota tra 40% e 70%
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
    ("Scoppio della bolla dot-com", "2000-03-10", "2002-10-09"),
    ("Crisi finanziaria", "2008-09-01", "2009-03-09"),
    ("Rialzo dei tassi del 2022", "2022-01-03", "2022-10-12"),
]

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------------
IPOTESI = (
    "1) Nel periodo comune il rendimento annuo composto di prezzo della tecnologia è più alto di quello del resto (la media degli altri otto settori). "
    "2) La tecnologia ha una volatilità annua più alta e una perdita massima più profonda di quella del resto di almeno venti punti percentuali. "
    "3) La differenza di Sharpe tra tecnologia e resto non si distingue dallo zero: l'intervallo di confidenza al 95% la contiene. "
    "4) Su finestre mobili di cinque anni la leadership ruota: la tecnologia è davanti in una quota di finestre compresa tra il 40% e il 70%. "
    "5) Il vincitore nei cinque anni precedenti vince anche nei cinque successivi in una quota di mesi non distinguibile dal caso "
    "(la metà): il p-value del test di permutazione è sopra il 5%. "
    "6) Nello scoppio della bolla dot-com e nel rialzo dei tassi del 2022 la tecnologia perde più del resto. "
    "7) Scegliere a caso tra la tecnologia e il resto ogni mese (scimmie) dà un valore finale mediano compreso tra quello della tecnologia e quello del resto."
)
