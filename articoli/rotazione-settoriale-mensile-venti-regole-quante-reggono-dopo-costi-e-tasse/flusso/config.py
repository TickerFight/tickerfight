"""Parametri dell'articolo n. 361 - "Rotazione settoriale mensile: venti regole, quante reggono?".

Tutti i parametri dell'analisi stanno qui, scritti PRIMA di guardare qualunque risultato. Gli script numerati li leggono da
questo file: ogni numero dell'articolo si può ricondurre a una scelta dichiarata, e nessun valore è nascosto nel codice.

La regola di rotazione: all'ultima seduta di ogni mese si calcola, per ognuno dei nove ETF settoriali, il rendimento di prezzo
delle ultime L sedute (in dollari) e si scelgono i K settori con il rendimento più alto. L'ordine parte alla chiusura della
prima seduta del mese dopo (segnale a t, ordine a t+1). Si vendono i settori usciti dalla classifica e con il ricavato si
comprano quelli entrati; chi resta in classifica non si tocca.
A differenza dell'articolo 590 (una regola, 1.000 euro, commissione fissa) qui si dichiara in anticipo l'INTERA griglia:
L in {21, 63, 126, 189, 252} sedute e K in {1, 2, 3, 4} settori, cioè venti regole, nessuna scelta a posteriori. La domanda è
quante di queste venti reggono contro i riferimenti, i test multipli e il passare del tempo.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Strumenti (gli stessi dell'articolo 590, scelti a priori) ---------------------------------------------------------
SETTORI = [
    ("XLB", "materiali"),
    ("XLE", "energia"),
    ("XLF", "finanza"),
    ("XLI", "industriali"),
    ("XLK", "tecnologia"),
    ("XLP", "beni di consumo di base"),
    ("XLU", "servizi di pubblica utilità"),
    ("XLV", "sanità"),
    ("XLY", "beni di consumo discrezionali"),
]
BENCHMARK = ("SPY", "ETF sull'S&P 500 (in dollari, convertito in euro)")
TICKER_CAMBIO = "EURUSD=X"
INIZIO_DOWNLOAD = "1998-12-01"
STORIA_MINIMA_ANNI = 8
NOMI_ESENTI = ("S&P 500", "SPDR", "EUR/USD", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "SPY", "361", "590",
               "TickerFight")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere dei nove ETF settoriali SPDR, dell'ETF sull'S&P 500 e del cambio euro-dollaro"
URL_FONTE = "https://finance.yahoo.com/"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_").replace("=", "_") + ".csv")


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").replace("=", "_").lower()


# --- Condizioni -------------------------------------------------------------------------------------------------------
CAPITALE = 10000.0
SCENARI_COSTO = [("0,1%", 0.0, 0.001)]     # commissione proporzionale all'importo di ogni ordine
SCENARIO_PRINCIPALE = 0
ALIQUOTA = 0.26                            # plusvalenze tassate a ogni vendita, minusvalenze riportate fino al quarto anno seguente

# --- La griglia delle regole ----------------------------------------------------------------------------------------------
LOOKBACKS = (21, 63, 126, 189, 252)        # sedute di osservazione (circa 1, 3, 6, 9 e 12 mesi)
N_SETTORI = (1, 2, 3, 4)                   # quanti settori si tengono
CENTRALE = (126, 3)                        # la regola «di mezzo», dichiarata prima, usata per le curve

# --- Test statistici -----------------------------------------------------------------------------------------------------------
SEME = 20261027
N_BOOTSTRAP = 2000
LUNGHEZZA_BLOCCO = 20
LIVELLO_CONFIDENZA = 0.95
SOGLIE = {"ip1_min": 10, "ip2_max": 10, "ip3_top": 5, "ip4_max": 2}

IPOTESI = (
    "1) Al lordo di costi e tasse, almeno dieci delle venti regole hanno un rendimento annuo composto superiore al buy & hold "
    "dell'ETF sull'S&P 500 (è ciò che la letteratura sul momentum di settore lascia attendere). "
    "2) Al netto (commissione dello 0,1% dell'importo e tassa del 26%), meno di dieci delle venti regole battono i nove settori "
    "tenuti in parti uguali: il vantaggio della rotazione sul semplice possesso di tutti i settori non regge ai costi. "
    "3) La regola con il rendimento netto migliore nella prima metà del periodo non è tra le prime cinque nella seconda metà: "
    "la migliore di ieri non è la migliore di domani. "
    "4) Dopo la correzione di Holm sulle venti regole (bootstrap a blocchi della differenza netta giornaliera rispetto ai nove "
    "settori tenuti in parti uguali), al massimo due regole su venti sono significative al cinque per cento."
)
