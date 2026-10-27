"""Parametri dell'articolo n. 575 - "Operare solo il lunedì" (rubrica «trading con poco capitale»).

Scritti PRIMA di guardare qualunque risultato.

La regola: si è investiti solo durante la seduta di un giorno della settimana fissato. Si compra alla chiusura della seduta
precedente e si vende alla chiusura di quella seduta (il rendimento incassato è quello del giorno scelto, da chiusura a chiusura).
Se il lunedì è festivo non c'è seduta e quella settimana non si opera. Il giorno è deciso dal calendario: nessun look-ahead.
Si provano i cinque giorni della settimana (il lunedì è l'oggetto dell'articolo, gli altri sono «gli altri giorni»).
Ogni giorno scelto comporta due ordini a settimana (un acquisto e una vendita), circa 104 l'anno, e una quota di sedute investite
di circa un quinto. I dati sono quelli dell'articolo 578 (stessi strumenti, stesso scarico).
Le scimmie: stesso numero di sedute investite, ognuna di un giorno (da chiusura a chiusura), piazzate a caso, valutate prima di
costi e tasse (domanda: il lunedì è speciale?). Il confronto netto con il buy & hold è deterministico (costi e tasse).
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

STRUMENTI = [
    ("SWDA.MI", "ETF azionario mondiale (MSCI World, in euro)", "EUR"),
    ("CSSPX.MI", "ETF sull'S&P 500 (in euro)", "EUR"),
    ("^GSPC", "indice S&P 500 (in dollari, convertito in euro)", "USD"),
]
TICKER_CAMBIO = "EURUSD=X"
INIZIO_DOWNLOAD = "1995-01-01"
STORIA_MINIMA_ANNI = 8
NOMI_ESENTI = ("S&P 500", "MSCI World", "EUR/USD", "buy & hold")
FUSO_BORSA = "Europe/Rome"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere di due ETF quotati a Milano, dell'indice S&P 500 e del cambio euro-dollaro"
URL_FONTE = "https://finance.yahoo.com/"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_").replace("=", "_") + ".csv")


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").replace("=", "_").lower()


CAPITALE = 1000.0
SCENARI_COSTO = [("0 euro", 0.0, 0.0), ("2 euro", 2.0, 0.0), ("0,1%", 0.0, 0.001)]
SCENARIO_PRINCIPALE = 1
ALIQUOTA = 0.26
GIORNI = [("d0", "lunedì", 0), ("d1", "martedì", 1), ("d2", "mercoledì", 2), ("d3", "giovedì", 3), ("d4", "venerdì", 4)]

SEME = 20261027
N_SCIMMIE = 2000
# Prove: 3 strumenti x (buy & hold + 5 giorni) x 4 scenari = 72 simulazioni. Test: scimmie, 3 strumenti x 5 giorni = 15, Holm.

IPOTESI = (
    "1) Il lunedì non è un giorno speciale: dopo la correzione di Holm sui 15 test, il lunedì non batte le scimmie (stesso numero "
    "di sedute investite, scelte a caso) in nessuno strumento. "
    "2) Dopo la correzione di Holm sui 15 test, nessun giorno della settimana batte le scimmie. "
    "3) Con 2 euro a ordine il capitale di 1.000 euro si esaurisce con la regola del lunedì in tutti gli strumenti, perché i circa 104 "
    "ordini l'anno costano circa il 20% del capitale ogni anno. "
    "4) Con la commissione dello 0,1% il rendimento annuo netto della regola del lunedì è negativo in almeno due strumenti su tre. "
    "5) Con commissione zero, ma con la tassa del 26%, nessuno dei cinque giorni batte il buy & hold netto in nessuno strumento. "
    "6) Il giorno migliore (valore finale lordo più alto) non è lo stesso nei tre strumenti."
)
