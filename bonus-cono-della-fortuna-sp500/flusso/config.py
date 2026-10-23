"""Parametri dell'articolo bonus - "Il cono della fortuna: la regola 50/200 sull'S&P 500 contro la scimmia".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni
numero dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.
L'articolo è fuori programmazione e fuori catalogo: per questo la cartella si chiama "bonus" e non ha numero.

Idea: il risultato della regola 50/200 è merito del timing o di un po' di fortuna? Si confronta con migliaia di
"scimmie" che hanno la stessa dieta della regola (stessi giorni investiti, stesso numero di ordini, stessi
periodi di permanenza sul mercato) ma entrano ed escono a caso.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
TICKER = "^GSPC"                      # indice S&P 500, in dollari. Si assume uno strumento che lo replica, negoziabile in euro
TICKER_CAMBIO = "EURUSD=X"            # dollari per un euro
INIZIO_DOWNLOAD = "2015-01-01"        # serve storia per la media a 200 giorni prima dell'inizio del test
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "sp500_giornaliero.csv"
FILE_CAMBIO = DATI / "eurusd_giornaliero.csv"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure e aperture giornaliere dell'indice S&P 500 e cambio euro/dollaro"
URL_FONTE = "https://finance.yahoo.com/quote/%5EGSPC/history/"
NOTA_COLONNA = ("Open e Close non corretti per i dividendi: l'indice è un indice di prezzo, i dividendi non sono "
                "considerati, né per la regola né per il buy & hold")

# --- Scenario dell'investitore (identico agli articoli precedenti) ----------
CAPITALE = 500.0
COMMISSIONE = 1.0
ALIQUOTA = 0.26
ANNI_TEST = 10            # dieci anni: abbastanza ordini della regola perché il confronto con il caso abbia senso
SMA_VELOCE = 50
SMA_LENTA = 200
MODO_PRINCIPALE = "apertura"   # segnale a fine seduta t, ordine all'apertura di t+1

# --- La scimmia: timing casuale con la stessa dieta della regola -----------------
# Stessi giorni investiti, stesso numero di acquisti e di vendite, stessa durata di ogni periodo di permanenza
# sul mercato: cambia solo DOVE i periodi cadono nel tempo.
N_PERCORSI = 10000
SEME = 2026
PASSO_CAMPIONE = 5        # per i grafici si conserva il valore di ogni quinta seduta (una a settimana)
BIN_VALORE = 70           # fasce di valore per la superficie 3D

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Il valore finale della regola cade dentro il cono: almeno il 5% dei percorsi casuali fa altrettanto o meglio "
    "(il timing non è dimostrabilmente meglio della fortuna). "
    "2) Il giorno del punto più basso del buy & hold la regola sta sopra la mediana dei percorsi casuali: nei crolli il "
    "timing aiuta. "
    "3) Il buy & hold chiude sopra la mediana dei percorsi casuali, perché è sempre investito e in dieci anni di rialzo "
    "stare sul mercato conta più del timing."
)
