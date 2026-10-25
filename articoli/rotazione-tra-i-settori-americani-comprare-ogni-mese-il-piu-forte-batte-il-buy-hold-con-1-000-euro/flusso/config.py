"""Parametri dell'articolo n. 590 - "Rotazione tra ETF settoriali americani" (rubrica «trading con poco capitale»).

Tutti i parametri dell'analisi stanno qui, scritti PRIMA di guardare qualunque risultato. Gli script numerati li leggono da
questo file: ogni numero dell'articolo si può ricondurre a una scelta dichiarata, e nessun valore è nascosto nel codice.

La regola di rotazione (nessuna ottimizzazione, parametri classici scritti prima): all'ultima seduta di ogni mese si
calcola, per ognuno dei nove ETF settoriali, il rendimento di prezzo delle ultime L sedute (in dollari); si scelgono i K
settori con il rendimento più alto (a parità conta l'ordine dell'elenco). L'ordine parte alla chiusura della prima seduta
del mese dopo (segnale a t, ordine a t+1: nessun look-ahead). Si vendono i settori usciti dalla classifica e con il
ricavato si comprano quelli entrati; i settori che restano in classifica non si toccano (nessun ordine). Si è sempre
investiti, a parte la cassa che resta tra una vendita e un acquisto nella stessa seduta.
La combinazione principale è L = 126 sedute (circa sei mesi) con K = 1 (un solo settore: è l'unica che ha senso con 1.000 euro
e una commissione fissa). Come controlli di robustezza sono dichiarate in anticipo tutte le combinazioni di L in
{63, 126, 252} e K in {1, 3}: sei regole in tutto, nessuna scelta a posteriori.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Strumenti (scelti a priori, prima di guardare i dati) ---------------------------------------------------------
# I nove ETF settoriali SPDR (Select Sector SPDR), quotati negli Stati Uniti in dollari, esistenti da fine 1998.
# I settori «comunicazioni» e «immobiliare» nascono dopo: non entrano, per avere lo stesso universo per tutto il periodo.
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
TICKER_CAMBIO = "EURUSD=X"          # dollari per un euro
INIZIO_DOWNLOAD = "1998-12-01"
STORIA_MINIMA_ANNI = 8
NOMI_ESENTI = ("S&P 500", "SPDR", "EUR/USD", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "SPY",
               "Moskowitz e Grinblatt (1999)", "Jegadeesh e Titman (1993)")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere dei nove ETF settoriali SPDR, dell'ETF sull'S&P 500 e del cambio euro-dollaro"
URL_FONTE = "https://finance.yahoo.com/"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_").replace("=", "_") + ".csv")


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").replace("=", "_").lower()


# --- Condizioni della rubrica -----------------------------------------------------------------------------------
CAPITALE = 1000.0
# Tre scenari di commissione per ordine, scritti prima: (nome, parte fissa in euro, parte proporzionale all'importo)
SCENARI_COSTO = [
    ("0 euro", 0.0, 0.0),
    ("2 euro", 2.0, 0.0),
    ("0,1%", 0.0, 0.001),
]
SCENARIO_PRINCIPALE = 1      # indice in SCENARI_COSTO: il caso «2 euro» è quello delle tabelle principali
ALIQUOTA = 0.26              # tassa sulle plusvalenze, minusvalenze riportate fino al quarto anno seguente

# --- La regola ------------------------------------------------------------------------------------------------------
LOOKBACKS = (63, 126, 252)   # sedute di osservazione (circa 3, 6 e 12 mesi)
N_SETTORI = (1, 3)           # quanti settori si tengono
PRINCIPALE = (126, 1)
SECONDARIA_SCIMMIE = (126, 3)    # la seconda regola sottoposta ai test (scimmie e bootstrap)

# --- Test statistici -------------------------------------------------------------------------------------------------
SEME = 20261025
N_SCIMMIE = 2000
N_BOOTSTRAP = 5000
LUNGHEZZA_BLOCCO = 20        # sedute per blocco nel bootstrap a blocchi della differenza di rendimento giornaliero
LIVELLO_CONFIDENZA = 0.95
# Numero dichiarato di prove: 6 regole di rotazione + 2 riferimenti (buy & hold dell'S&P 500 e i nove settori tenuti in
# parti uguali) x 4 scenari (lordo e tre commissioni). I test di ipotesi sono 4 (scimmie e bootstrap, per le due regole
# con L = 126) e sono corretti con il metodo di Holm.

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------------------------------
IPOTESI = (
    "1) Al lordo di costi e tasse, la rotazione principale (un settore, sei mesi) ha un rendimento annuo composto superiore "
    "al buy & hold dell'ETF sull'S&P 500 (è il risultato che la letteratura sul momentum di settore lascia attendere). "
    "2) Al netto (commissione fissa di 2 euro e tassa del 26%), la rotazione principale NON supera il buy & hold. "
    "3) La rotazione a tre settori fa più ordini all'anno di quella a un settore, con lo stesso periodo di osservazione. "
    "4) Dopo la correzione di Holm, la rotazione principale non batte in modo significativo le scimmie (stessi giorni di "
    "ordine e stesso numero di ordini, ma settore scelto a caso), nello scenario con commissione fissa. "
    "5) Il passaggio dal lordo al netto costa alla rotazione principale più punti di rendimento annuo di quanto costi al buy & hold. "
    "6) La rotazione resta sotto il buy & hold, al netto, in almeno quattro delle sei combinazioni di periodo di osservazione e numero di settori."
)
