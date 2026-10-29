"""Parametri dell'articolo n. 483 - "ETF covered call: rendita o rinuncia?".

Tutti i parametri dell'analisi stanno qui, scritti prima di guardare i risultati.

Due ETF covered call, che vendono ogni mese opzioni call sull'indice e distribuiscono il premio incassato: XYLD (sull'S&P 500) e
QYLD (sul Nasdaq-100). Ognuno si confronta con l'ETF che replica lo stesso indice senza opzioni, SPY e QQQ. Tutti i prezzi sono
«Adj Close» di Yahoo Finance, cioè con i dividendi e le distribuzioni reinvestiti. Periodo: da quando esistono tutti e quattro (da dicembre 2013).
Terzo confronto: un portafoglio di controllo, indice e liquidità (tasso a tre mesi, ^IRX), con il peso dell'indice scelto in modo che la
volatilità sia uguale a quella del covered call.
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
    ("XYLD", "Global X S&P 500 Covered Call", "XYLD"),
    ("QYLD", "Global X Nasdaq 100 Covered Call", "QYLD"),
]
TICKER_LIQUIDITA = "^IRX"
INIZIO_DOWNLOAD = "2013-01-01"
NOMI_ESENTI = ("S&P 500", "Nasdaq-100", "Nasdaq 100", "QQQ", "SPY", "XYLD", "QYLD", "IRX")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere aggiustate di quattro ETF quotati negli Stati Uniti e il tasso a tre mesi"
URL_FONTE = "https://finance.yahoo.com/"
COLONNA_PREZZO = "Adj Close"     # prezzo con dividendi e distribuzioni reinvestiti
ANNI_MINIMI = 8


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Parametri dell'analisi ----------------------------------------------------------------------------------------
GIORNI_ANNO = 252
CAPITALE = 500.0
COPPIE = [("XYLD", "SPY"), ("QYLD", "QQQ")]       # (covered call, indice senza opzioni)
H2_VOL_RIDUZIONE = 0.10          # ipotesi 2: la volatilità del covered call è più bassa di almeno il 10% (relativo) di quella dell'indice
H3_DD_MIN = 0.20                 # ipotesi 3: la perdita massima del covered call resta comunque sopra il 20%
H4_UP_MAX = 0.80                 # ipotesi 4: nei mesi di rialzo il covered call cattura meno dell'80% del rendimento dell'indice
H4_DOWN_MIN = 0.80               # ... e nei mesi di ribasso cattura più dell'80% della perdita

# --- Test statistici -----------------------------------------------------------------------------------------------
SEME = 20261029
N_BOOTSTRAP = 2000
BLOCCO_BOOTSTRAP = 21
LIVELLO_CONFIDENZA = 0.95

# --- Fasi di crisi, fissate a priori (date di calendario) -----------------------------------------------------------
CRISI = [
    ("Crollo del 2020", "2020-02-19", "2020-03-23"),
    ("Rialzo dei tassi del 2022", "2022-01-03", "2022-10-12"),
]

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------------
IPOTESI = (
    "1) Nel periodo comune il rendimento annuo composto di entrambi i covered call, XYLD e QYLD, è più basso di quello dell'indice "
    "corrispondente, SPY e QQQ. "
    "2) La volatilità annua di entrambi i covered call è più bassa di quella dell'indice di almeno il 10% in termini relativi. "
    "3) La perdita massima di entrambi i covered call resta comunque sopra il 20%: l'opzione non protegge dai crolli. "
    "4) Su base mensile, in entrambi i covered call la cattura dei mesi di rialzo dell'indice è sotto l'80% e quella dei mesi di ribasso è sopra l'80%: "
    "si rinuncia ai rialzi ma non si evitano i ribassi. "
    "5) La differenza di Sharpe tra covered call e indice non si distingue dallo zero in nessuna delle due coppie: l'intervallo di "
    "confidenza al 95% la contiene. "
    "6) Un portafoglio di indice e liquidità con la stessa volatilità del covered call ha un rendimento annuo composto più alto del covered call, in entrambe le coppie. "
    "7) Nel crollo del 2020 e nel rialzo dei tassi del 2022 entrambi i covered call perdono meno dell'indice corrispondente."
)
