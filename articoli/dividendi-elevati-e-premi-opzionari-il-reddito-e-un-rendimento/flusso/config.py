"""Parametri dell'articolo n. 484 - "Dividendi elevati e premi opzionari: reddito non significa rendimento".

Tutti i parametri dell'analisi stanno qui, scritti prima di guardare i risultati.

Sei ETF «da reddito» quotati negli Stati Uniti, confrontati con SPY (l'S&P 500) e QQQ (Nasdaq-100):
  - quattro a dividendo elevato: SCHD, VYM, HDV, SPYD (azioni che pagano dividendi alti);
  - due che vendono opzioni call e distribuiscono il premio: XYLD (S&P 500) e QYLD (Nasdaq-100).
Prezzi: «Close» (solo prezzo) e «Adj Close» (con le distribuzioni reinvestite) di Yahoo Finance. Periodo: da quando esistono tutti.
Il «reddito» di un ETF è la parte del rendimento che arriva come distribuzione, cioè la differenza tra Adj Close e Close.
Simulazione del prelievo: chi vive di rendita ritira ogni mese una somma fissa. Con il tasso di prelievo uguale per tutti,
gli ETF a reddito (che pagano da sé) si confrontano con SPY, da cui si vendono quote per coprire la differenza.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: (ticker Yahoo Finance, nome, sigla) ---------------------------------------------------------------------
ETF = [
    ("SPY", "SPDR S&P 500", "SPY"),
    ("QQQ", "Invesco QQQ Trust (Nasdaq-100)", "QQQ"),
    ("SCHD", "Schwab US Dividend Equity", "SCHD"),
    ("VYM", "Vanguard High Dividend Yield", "VYM"),
    ("HDV", "iShares Core High Dividend", "HDV"),
    ("SPYD", "SPDR Portfolio S&P 500 High Dividend", "SPYD"),
    ("XYLD", "Global X S&P 500 Covered Call", "XYLD"),
    ("QYLD", "Global X Nasdaq 100 Covered Call", "QYLD"),
]
TICKER_LIQUIDITA = None           # nessuna liquidità in questo articolo
INIZIO_DOWNLOAD = "2013-01-01"
NOMI_ESENTI = ("S&P 500", "Nasdaq-100", "Nasdaq 100", "QQQ", "SPY", "XYLD", "QYLD", "SCHD", "VYM", "HDV", "SPYD")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "prezzi giornalieri, con e senza le distribuzioni, di otto ETF quotati negli Stati Uniti"
URL_FONTE = "https://finance.yahoo.com/"
ANNI_MINIMI = 8


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Parametri dell'analisi ----------------------------------------------------------------------------------------
GIORNI_ANNO = 252
MESI_ANNO = 12
REDDITO = ["SCHD", "VYM", "HDV", "SPYD", "XYLD", "QYLD"]       # gli ETF «da reddito»
DIVIDENDO = ["SCHD", "VYM", "HDV", "SPYD"]
PREMIO = ["XYLD", "QYLD"]
INDICE = "SPY"
CAPITALE = 10000.0              # euro iniziali nella simulazione del prelievo (importi in dollari, ma letti come unità di conto)
PRELIEVO_ANNUO = 0.04           # prelievo fisso: 4% del capitale iniziale all'anno, in rate mensili uguali
ALIQUOTA = 0.26                 # imposta sostitutiva italiana su dividendi e plusvalenze
H3_PREZZO_MAX = 0.0             # ipotesi 3: il solo prezzo dei due ETF a premio non cresce (rendimento annuo composto <= 0)

# --- Test statistici -----------------------------------------------------------------------------------------------
SEME = 20261102
N_BOOTSTRAP = 2000
BLOCCO_BOOTSTRAP = 21
LIVELLO_CONFIDENZA = 0.95

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------------
IPOTESI = (
    "1) Tutti e sei gli ETF da reddito distribuiscono ogni anno una quota del loro valore più alta di quella di SPY. "
    "2) Nessuno dei sei ha un rendimento annuo composto totale (distribuzioni reinvestite) più alto di quello di SPY nel periodo comune. "
    "3) Per i due ETF a premio opzionario, XYLD e QYLD, il solo prezzo (senza distribuzioni) non cresce: il rendimento annuo composto del prezzo è zero o negativo. "
    "4) In una simulazione di prelievo fisso del 4% annuo del capitale iniziale, senza tasse, nessun ETF da reddito finisce con più capitale di SPY. "
    "5) Con la stessa simulazione dopo la tassa del 26% (sui dividendi quando incassati, sulle plusvalenze quando si vendono quote, e sul guadagno residuo alla fine), nessun ETF da reddito finisce con più capitale netto di SPY. "
    "6) La differenza di Sharpe tra ciascuno dei quattro ETF a dividendo elevato e SPY non si distingue dallo zero: l'intervallo di confidenza al 95% la contiene."
)
