"""Parametri dell'articolo n. 203 - "Large cap contro small cap: il premio di dimensione, decennio per decennio".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Round di TickerFight: lo sfidante «grandi» è l'S&P 500, gli sfidanti «piccole» sono tre indici di aziende più piccole
(S&P MidCap 400, Russell 2000, S&P SmallCap 600). Si confrontano a coppie, sulla storia in comune, mese per mese,
decennio per decennio e su finestre mobili. Il caso: una scimmia che ogni mese sceglie a caso tra grandi e piccole.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# Indici di prezzo (niente dividendi), in dollari, scelti prima di guardare i dati. La prima voce è il riferimento.
GRANDI = ("^GSPC", "S&P 500 (grandi aziende)", "USD")
PICCOLE = [
    ("^MID", "S&P MidCap 400 (medie aziende)", "USD"),
    ("^RUT", "Russell 2000 (piccole aziende)", "USD"),
    ("^SP600", "S&P SmallCap 600 (piccole aziende)", "USD"),
]
INDICI = [GRANDI] + PICCOLE
INIZIO_DOWNLOAD = "1980-01-01"
NOMI_ESENTI = ("S&P 500", "S&P MidCap 400", "Russell 2000", "S&P SmallCap 600", "S&P", "203", "TickerFight")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere di quattro indici azionari americani (S&P 500, S&P MidCap 400, Russell 2000, S&P SmallCap 600)"
URL_FONTE = "https://finance.yahoo.com/"
MESI_MINIMI = 120            # sotto dieci anni di storia in comune la coppia viene scartata


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


CAPITALE = 10000.0           # capitale iniziale dell'esempio in dollari
FINESTRE = (60, 120)         # finestre mobili in mesi: cinque e dieci anni
DECENNI = (1990, 2000, 2010) # decenni di calendario completi; il 2020 è parziale e si mostra a parte
MESI_DECENNIO_MINIMI = 60    # un decennio entra nella tabella se ha almeno cinque anni di dati della coppia
SOGLIA_QUOTA = (0.45, 0.55)  # ipotesi sulla quota di mesi vinti
SOGLIA_FINESTRE = (0.35, 0.65)

SEME = 20261027
N_BOOTSTRAP = 5000
N_SCIMMIE = 5000
LIVELLO_CONFIDENZA = 0.95

IPOTESI = (
    "1) Il premio di dimensione non ha lo stesso segno in tutti i decenni: per ogni coppia con almeno due decenni valutabili, "
    "c'è almeno un decennio in cui le piccole battono le grandi e almeno uno in cui perdono. "
    "2) Sulla storia in comune, la differenza media mensile tra piccole e grandi non è significativa: l'intervallo di confidenza al "
    "95% (bootstrap per anni) include lo zero in tutte e tre le coppie. "
    "3) Nelle finestre mobili di dieci anni la quota di finestre in cui le piccole battono le grandi sta tra il 35% e il 65% in tutte "
    "e tre le coppie: nessuno dei due vince sempre. "
    "4) La quota di mesi in cui le piccole battono le grandi sta tra il 45% e il 55% in tutte e tre le coppie: il mese singolo è "
    "quasi una moneta."
)
