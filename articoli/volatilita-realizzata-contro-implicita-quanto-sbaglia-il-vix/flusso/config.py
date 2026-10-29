"""Parametri dell'articolo n. 245 - "Volatilità realizzata contro implicita".

Tutti i parametri dell'analisi stanno qui, scritti prima di guardare i risultati.

Il VIX è la volatilità attesa dal mercato dell'S&P 500 nei successivi trenta giorni di calendario, ricavata dai prezzi delle opzioni (volatilità implicita),
espressa in punti di volatilità annua. La volatilità realizzata è quella che poi si osserva: deviazione standard dei rendimenti giornalieri logaritmici
dell'S&P 500 (indice di prezzo) nelle RV_GIORNI sedute successive alla chiusura del giorno t (circa trenta giorni di calendario), annualizzata e in punti.
Premio = VIX del giorno t meno volatilità realizzata nelle RV_GIORNI sedute successive: positivo quando il VIX ha sovrastimato. Nessun look-ahead nel
confronto: il VIX di t usa solo informazioni di t; la volatilità realizzata «passata» usa solo le RV_GIORNI sedute fino a t.
Le statistiche usano tutte le sedute (descrittive, con finestre sovrapposte); per i conti per mese si usa un campione non sovrapposto, una data ogni RV_GIORNI sedute.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------------------------
INDICI = [
    ("^GSPC", "S&P 500", "USD"),
    ("^VIX", "VIX", "punti"),
]
TICKER_INDICE = "^GSPC"
TICKER_VIX = "^VIX"
INIZIO_DOWNLOAD = "1989-01-01"
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere dell'S&P 500 e del VIX"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = "Si usano solo le chiusure; l'S&P 500 è l'indice di prezzo, senza dividendi"
NOMI_ESENTI = ("S&P 500", "VIX")


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Parametri (fissati prima di guardare i dati) --------------------------------------------
GIORNI_ANNO = 252
RV_GIORNI = 21                                  # sedute della volatilità realizzata (circa un mese)
FASCE = (0.0, 15.0, 20.0, 30.0, 1000.0)         # fasce del VIX per l'ipotesi 3
N_PEGGIORI = 10                                 # mesi peggiori nell'ipotesi 5

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_QUOTA = 0.75                  # ipotesi 1: il VIX supera la volatilità realizzata successiva in almeno il 75% delle sedute
H2_MIN = 2.0                     # ipotesi 2: premio medio tra 2 e 6 punti di volatilità
H2_MAX = 6.0
H5_QUOTA = 0.25                  # ipotesi 5: i 10 mesi peggiori cancellano almeno il 25% di tutto il premio mensile positivo
H6_PENDENZA = 1.0                # ipotesi 6: pendenza della regressione della volatilità realizzata sul VIX sotto 1

IPOTESI = (
    "1) Il VIX è più alto della volatilità realizzata nel mese successivo in almeno il 75% delle sedute. "
    "2) Il premio medio (VIX meno volatilità realizzata successiva) sta tra 2 e 6 punti di volatilità. "
    "3) Il premio medio, in punti di volatilità, è più alto quando il VIX è sopra 30 che quando è sotto 15. "
    "4) Il VIX prevede la volatilità del mese successivo meglio della volatilità realizzata dell'ultimo mese (R quadro più alto). "
    "5) I 10 mesi con il premio più negativo (campione mensile non sovrapposto) cancellano almeno il 25% della somma dei premi mensili positivi. "
    "6) Nella regressione della volatilità realizzata successiva sul VIX la pendenza è sotto 1: quando il VIX sale, la volatilità che segue sale meno."
)
