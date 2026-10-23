"""Parametri dell'articolo n. 4 - "Il look-ahead bias in 10 righe di codice".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: il look-ahead bias è usare nel segnale un'informazione che nel momento dell'operazione non c'era ancora. Il caso
più comune è il più banale: calcolare il segnale con la chiusura di oggi e applicarlo al rendimento di oggi, cioè
comprare ieri sapendo come finirà oggi. Si misura quanto vale questa illusione per tre regole di velocità diversa,
sul S&P 500, e come riconoscerla con un controllo semplice: ritardare il segnale e guardare se il risultato crolla.
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

# --- Le regole (scelte a priori, non ottimizzate) ----------------------------------------------
# Tre regole sempre investite o in cassa, dalla più veloce alla più lenta.
REGOLE = [
    ("un_giorno", "un giorno: la chiusura di oggi è sopra quella di ieri"),
    ("media_20", "media a 20 giorni: la chiusura è sopra la media a 20 giorni"),
    ("medie_50_200", "medie 50/200: la media a 50 giorni è sopra quella a 200"),
]
SMA_BREVE = 20
SMA_VELOCE = 50
SMA_LENTA = 200

# --- Convenzioni di calcolo ---------------------------------------------
INIZIO_TEST_SEDUTE = 300         # le prime sedute servono per le medie; tutte le regole partono dallo stesso giorno
RITARDO_ONESTO = 1               # il segnale della chiusura di ieri decide la posizione di oggi
RITARDI = list(range(0, 11))     # test del ritardo: 0 = look-ahead, 1 = onesto, poi 2, 3 ... 10 sedute
SOTTOPERIODI = [
    ("dall'inizio al 1969", None, "1969-12-31"),
    ("1970-1999", "1970-01-01", "1999-12-31"),
    ("dal 2000 a oggi", "2000-01-01", None),
]
# Griglia di medie per mostrare come cambia l'illusione con la velocità della regola
GRIGLIA_VELOCE = (5, 10, 20, 50, 100)
GRIGLIA_LENTA = (20, 50, 100, 150, 200, 250, 300)
CAPITALE = 500.0                 # solo per dare un'idea: valori lordi, senza commissioni né tasse

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Con il look-ahead il rendimento annuo è più alto che nella versione onesta per tutte e tre le regole. "
    "2) L'illusione cresce con la velocità della regola: è più grande per la regola di un giorno che per la media a 20 giorni, "
    "e più grande per questa che per le medie 50/200. "
    "3) Per le medie 50/200 l'illusione è sotto i due punti percentuali l'anno in ciascuno dei tre sottoperiodi. "
    "4) Nel test del ritardo, per ogni regola il calo più grande del rendimento annuo è quello tra ritardo zero e ritardo uno: "
    "il look-ahead si riconosce perché basta spostare il segnale di un giorno."
)
