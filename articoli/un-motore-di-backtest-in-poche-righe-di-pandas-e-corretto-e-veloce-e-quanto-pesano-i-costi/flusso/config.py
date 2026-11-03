"""Parametri dell'articolo n. 6 - "Un motore di backtest vettoriale da zero".

Tutti i parametri dell'analisi stanno qui, scritti prima di guardare i risultati.

Idea: un motore di backtest serio si scrive in poche righe di pandas. Qui ne scriviamo uno (segnale, shift di un giorno,
costi, curva del capitale) e lo mettiamo alla prova: dà gli stessi numeri di un ciclo scritto giorno per giorno?
Quanto è più veloce? Quanto costa, sul S&P 500, aggiungere i costi di transazione a tre regole semplici?
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

# --- Le regole (scelte a priori, non ottimizzate) --------------------------------------------
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
COSTO_BASE = 0.001               # costo per ogni cambio di posizione: 0,1% del capitale (spread e commissioni)
COSTI = [0.0, 0.0005, 0.001, 0.0025, 0.005]   # griglia dei costi per cambio di posizione
RIPETIZIONI_TEMPO = 7            # si misura il tempo più veloce su questo numero di esecuzioni
SOGLIA_RIGHE = 50                # il motore vettoriale deve stare in 50 righe di codice
SOGLIA_VELOCITA = 5              # il motore vettoriale deve essere almeno 5 volte più veloce del ciclo
SOGLIA_DIFFERENZA = 1e-9         # differenza relativa massima accettata tra i due motori
SOGLIA_COSTO_LENTA = 0.002       # le medie 50/200 devono perdere meno di 0,2 punti l'anno con il costo base
SOGLIA_COSTO_VELOCE = 0.05       # la regola di un giorno deve perdere più di 5 punti l'anno con il costo base
CAPITALE = 500.0                 # solo per dare un'idea

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Il motore vettoriale sta in 50 righe di codice o meno. "
    "2) Il motore vettoriale e il ciclo giorno per giorno danno lo stesso valore finale, con una differenza relativa sotto un miliardesimo, "
    "per tutte e tre le regole e con costi di transazione. "
    "3) Il motore vettoriale è almeno 5 volte più veloce del ciclo. "
    "4) Con un costo dello 0,1% per ogni cambio di posizione, le medie 50/200 perdono meno di 0,2 punti di rendimento annuo, "
    "mentre la regola di un giorno ne perde più di 5. "
    "5) Il motore, anche corretto, non rende una regola vincente: le medie 50/200 restano sotto il buy & hold in rendimento annuo, "
    "ma con una perdita massima più bassa."
)
