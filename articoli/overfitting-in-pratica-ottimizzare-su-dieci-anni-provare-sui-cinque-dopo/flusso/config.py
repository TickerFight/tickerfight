"""Parametri dell'articolo n. 41 - "Overfitting in pratica".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: si sceglie la migliore coppia di medie mobili su dieci anni (periodo di ottimizzazione) e la si usa nei cinque anni
successivi (periodo di prova, mai visto). Si ripete facendo avanzare le finestre. Poi si misura quanto crolla il
rendimento e come cresce l'illusione quando si provano più coppie.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
TICKER = "^GSPC"                  # S&P 500, indice di prezzo (senza dividendi), dal 1927
INIZIO_DOWNLOAD = "1927-01-01"
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "gspc_giornaliero.csv"
FILE_METADATI = DATI / "gspc_metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere dell'indice S&P 500"
URL_FONTE = "https://finance.yahoo.com/quote/%5EGSPC/history/"
NOTA_COLONNA = "Si usano solo le chiusure; i dividendi non sono considerati"

# --- La famiglia di regole: medie mobili veloce/lenta ---------------------------------------------
# Il segnale della chiusura di ieri decide la posizione di oggi (nessun look-ahead, come nell'articolo 4).
# Il "pool" contiene tutte le coppie con media veloce da 5 a 100 giorni (passo 5) e media lenta da 50 a 400 giorni
# (passo 10), con veloce < lenta. La "griglia principale" è un sottoinsieme che un analista userebbe davvero.
POOL_VELOCE = tuple(range(5, 101, 5))
POOL_LENTA = tuple(range(50, 401, 10))
GRIGLIA_VELOCE = (5, 10, 20, 30, 40, 50, 75, 100)
GRIGLIA_LENTA = (50, 100, 150, 200, 250, 300)
COPPIA_FISSA = (50, 200)          # la regola scelta a priori, mai ottimizzata, come riferimento

# --- Finestre ---------------------------------------------------------------------------------------
INIZIO_TEST_SEDUTE = 401          # le prime sedute servono per la media più lenta; tutte le coppie partono dallo stesso giorno
SEDUTE_OTTIMIZZAZIONE = 2520      # dieci anni di borsa
SEDUTE_PROVA = 1260               # cinque anni di borsa
PASSO = 1260                      # le finestre avanzano di cinque anni: i periodi di prova non si sovrappongono
COSTO_CAMBIO = 0.001              # 0,1% del valore a ogni acquisto o vendita; nessuna tassa, la cassa non rende

# --- Esperimento sulla dimensione della griglia --------------------------------------------------------
DIMENSIONI = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512)
N_ESTRAZIONI = 2000               # sottoinsiemi casuali del pool per ogni finestra e dimensione
SEME = 20261021
N_BOOTSTRAP = 5000
LIVELLO_CONFIDENZA = 0.95

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Fuori campione il rendimento annuo della coppia ottimizzata è più basso di quello in campione in almeno quattro "
    "finestre su cinque. "
    "2) La coppia ottimizzata batte la media delle coppie della griglia (cioè una coppia scelta a caso) fuori campione in meno "
    "di due finestre su tre: ottimizzare aggiunge poco. "
    "3) Più coppie si provano, più cresce la distanza tra il rendimento in campione e quello fuori campione del migliore: "
    "la distanza con 256 coppie è più grande di quella con 16, e questa più grande di quella con una sola coppia. "
    "4) La coppia ottimizzata batte il buy & hold fuori campione in meno della metà delle finestre."
)
