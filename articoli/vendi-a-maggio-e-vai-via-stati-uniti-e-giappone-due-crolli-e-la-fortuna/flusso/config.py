"""Parametri dell'articolo n. 161 - "Sell in May and go away".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Strategia Halloween: investiti da novembre ad aprile (si compra alla chiusura dell'ultima seduta di ottobre, si vende
alla chiusura dell'ultima seduta di aprile), in cassa da maggio a ottobre. Confronto con il buy & hold sullo stesso
indice, con i dodici "calendari" possibili di sei mesi e con migliaia di scimmie che hanno la stessa dieta
(stesso numero di ordini e stessa durata di ogni periodo investito, ma piazzati a caso dentro ogni anno).
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: tre indici americani e il Nikkei (ticker Yahoo Finance, nome, valuta) ----------------------------------
# Scelti a priori, prima di guardare i dati. Sono tutti indici di prezzo (i dividendi non sono contati, né per la strategia
# né per il buy & hold). Se Yahoo non restituisce abbastanza storia l'indice viene scartato e l'articolo lo dichiara.
INDICI = [
    ("^GSPC", "S&P 500 (Stati Uniti)", "USD"),
    ("^DJI", "Dow Jones (Stati Uniti)", "USD"),
    ("^IXIC", "Nasdaq Composite (Stati Uniti)", "USD"),
    ("^N225", "Nikkei 225 (Giappone)", "JPY"),
]
INIZIO_DOWNLOAD = "1950-01-01"
NOMI_ESENTI = ("S&P 500", "Nikkei 225")   # nomi di indici con cifre: non sono dati dell'analisi
FUSO_BORSA = "America/New_York"
STAGIONI_MINIME = 15        # sotto questa soglia l'indice viene scartato
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere di tre indici azionari americani e del Nikkei"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = ("Si usano solo le chiusure. I valori sono nella valuta locale di ciascun indice, senza cambio: "
                "capitale e commissione sono espressi in quella valuta")


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Scenario dell'investitore (come gli articoli precedenti) -------------------
CAPITALE = 500.0
COMMISSIONE = 1.0
ALIQUOTA = 0.26
MODO = "chiusura"

# --- La strategia -------------------------------------------------------------------
MESI_INVESTITI = (11, 12, 1, 2, 3, 4)       # novembre-aprile
DATA_PUBBLICAZIONE = 2002                    # anno dell'articolo di Bouman e Jacobsen: prima/dopo
# Maberly e Pierce (2004) attribuiscono il risultato americano a due eventi: il crollo di ottobre 1987 e la crisi di LTCM
# dell'agosto 1998. Sono due stagioni di maggio-ottobre: quelle che iniziano con l'ultima seduta di ottobre del 1986 e del 1997.
STAGIONI_ESCLUSE = (1986, 1997)             # anno di inizio (ottobre) delle due stagioni da togliere
H4_FRAZIONE = 0.75                           # ipotesi 4: la differenza senza le due stagioni è al massimo questa frazione di quella con

# --- Test statistici -------------------------------------------------------------------
SEME = 20261029
N_SCIMMIE = 5000
N_BOOTSTRAP = 5000
LIVELLO_CONFIDENZA = 0.95

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) In almeno tre indici su quattro il rendimento medio del semestre novembre-aprile è più alto di quello del semestre "
    "maggio-ottobre. "
    "2) Dopo costi e tasse la strategia batte il buy & hold in al massimo un indice su quattro, perché sta fuori dal mercato "
    "metà del tempo. "
    "3) Dopo la correzione di Holm, in al massimo un indice su quattro la strategia batte le scimmie con la stessa dieta con "
    "una significatività del cinque per cento: l'effetto stagionale, preso da solo, non si distingue dalla fortuna. "
    "4) Tolte le due stagioni di maggio-ottobre con il crollo dell'ottobre 1987 e la crisi di LTCM dell'agosto 1998, la "
    "differenza media tra i due semestri scende ad al massimo tre quarti di quella con tutte le stagioni, in ogni indice "
    "che le contiene."
)
