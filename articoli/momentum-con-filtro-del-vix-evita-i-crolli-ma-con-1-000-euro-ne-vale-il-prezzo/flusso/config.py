"""Parametri dell'articolo n. 595 - "Momentum con filtro del VIX" (rubrica «trading con poco capitale»).

Tutti i parametri dell'analisi stanno qui, scritti PRIMA di guardare qualunque risultato. Gli script numerati li leggono da
questo file: ogni numero dell'articolo si può ricondurre a una scelta dichiarata, e nessun valore è nascosto nel codice.

La regola di base (momentum mensile, nessuna ottimizzazione, parametri classici scritti prima): all'ultima seduta di ogni mese
si calcola, per ognuno dei nove ETF settoriali, il rendimento di prezzo delle ultime L sedute (in dollari); si scelgono i
K = 3 settori con il rendimento più alto (a parità conta l'ordine dell'elenco) e si comprano in parti uguali. L'ordine parte
alla chiusura della prima seduta del mese dopo (segnale a t, ordine a t+1: nessun look-ahead).
Il filtro: alla stessa chiusura di fine mese si legge il VIX (l'indice di volatilità implicita dell'S&P 500, chiusura
ufficiale). Se supera la soglia, la regola non sceglie nessun settore: il giorno dopo vende tutto e resta in liquidità
(che non rende nulla) fino al fine mese in cui il VIX è tornato sotto la soglia. Altrimenti si comporta come la regola di base.
Regole dichiarate in anticipo: L in {126, 252} sedute, base senza filtro e filtro con soglia in {20, 25, 30}: otto regole,
più il buy & hold dell'ETF sull'S&P 500. Regola principale: L = 126, soglia 25. Seconda regola sottoposta ai test: L = 252, soglia 25.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Strumenti (scelti a priori, prima di guardare i dati) ---------------------------------------------------------
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
TICKER_VIX = "^VIX"
TICKER_CAMBIO = "EURUSD=X"          # dollari per un euro
INIZIO_DOWNLOAD = "1998-12-01"
STORIA_MINIMA_ANNI = 8
NOMI_ESENTI = ("S&P 500", "SPDR", "EUR/USD", "VIX", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "SPY",
               "Barroso e Santa-Clara (2015)", "Daniel e Moskowitz (2016)", "Moreira e Muir (2017)")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere dei nove ETF settoriali SPDR, dell'ETF sull'S&P 500, del VIX e del cambio euro-dollaro"
URL_FONTE = "https://finance.yahoo.com/"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_").replace("=", "_") + ".csv")


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").replace("=", "_").lower()


# --- Condizioni della rubrica -----------------------------------------------------------------------------------
CAPITALE = 1000.0
SCENARI_COSTO = [
    ("0 euro", 0.0, 0.0),
    ("2 euro", 2.0, 0.0),
    ("0,1%", 0.0, 0.001),
]
SCENARIO_PRINCIPALE = 1      # indice in SCENARI_COSTO: il caso «2 euro» è quello delle tabelle principali
ALIQUOTA = 0.26              # tassa sulle plusvalenze, minusvalenze riportate fino al quarto anno seguente

# --- La regola ------------------------------------------------------------------------------------------------------
LOOKBACKS = (126, 252)       # sedute di osservazione (circa 6 e 12 mesi)
K_SETTORI = 3                # settori tenuti dalla regola di base
SOGLIE_VIX = (20, 25, 30)    # il filtro porta in liquidità se il VIX di fine mese supera la soglia
PRINCIPALE = (126, 25)       # (L, soglia)
SECONDA = (252, 25)

# --- Test statistici -------------------------------------------------------------------------------------------------
SEME = 20261031
N_SCIMMIE = 2000
N_BOOTSTRAP = 5000
LUNGHEZZA_BLOCCO = 20
LIVELLO_CONFIDENZA = 0.95
# Numero dichiarato di prove: 8 regole + il buy & hold = 9 x 4 scenari (lordo e tre commissioni) = 36 simulazioni complete.
# Test di ipotesi: 4 (scimmie e bootstrap, per le due regole filtrate a soglia 25), corretti con il metodo di Holm.
# La scimmia di questo articolo tiene la stessa scelta dei settori della regola di base, ma sceglie a caso, tra i fine mese,
# lo stesso numero di mesi da passare in liquidità che il filtro ne ha scelti: isola il valore del VIX dal solo fatto di stare fuori.

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------------------------------
IPOTESI = (
    "1) Al lordo, la regola filtrata principale (6 mesi, soglia 25) ha una perdita massima dal picco più piccola della stessa regola senza filtro. "
    "2) Al lordo, il filtro non toglie rendimento: il rendimento annuo composto della regola filtrata principale è almeno pari a quello senza filtro "
    "(è ciò che la letteratura sul momentum gestito per volatilità lascia attendere). "
    "3) Il filtro fa più ordini all'anno della regola senza filtro, perché aggiunge vendite e riacquisti. "
    "4) Al netto (commissione fissa di 2 euro e tassa del 26%), il filtro non porta più di un punto di rendimento annuo in più della regola senza filtro. "
    "5) Dopo la correzione di Holm, le regole filtrate non battono in modo significativo le scimmie (stesso numero di mesi in liquidità, ma scelti a caso), "
    "nello scenario con commissione fissa."
)
