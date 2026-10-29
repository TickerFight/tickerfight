"""Parametri dell'articolo n. 282 - "Dogs of the Dow".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero dell'articolo si può
ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

La strategia: l'ultimo giorno di Borsa di ogni anno si calcola il rendimento da dividendo (dividendi pagati nell'anno diviso il prezzo
di chiusura) di ciascun titolo dell'universo e si comprano i dieci con il rendimento più alto, a pesi uguali, tenendoli per tutto
l'anno successivo. Varianti: i cinque più alti, i dieci più bassi. Confronti: l'universo intero a pesi uguali, lo SPY, e "scimmie" che
ogni anno estraggono a caso dieci titoli. Nessun costo e nessuna tassa (dichiarato).
Nessun look-ahead: la scelta di fine anno usa solo dividendi e prezzi fino a quel giorno.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati -----------------------------------------------------------------------------------------------------------
# Universo fissato PRIMA di guardare i dati: i trenta titoli dell'indice Dow Jones Industrial Average come li conosciamo a fine 2024.
# Difetto dichiarato nei limiti: sono società ancora nell'indice oggi (survivorship bias); chi ne è uscito non c'è.
UNIVERSO = ("AAPL AMGN AMZN AXP BA CAT CRM CSCO CVX DIS GS HD HON IBM JNJ JPM KO MCD MMM MRK MSFT NKE NVDA PG SHW TRV UNH V VZ WMT").split()
INDICE = "SPY"
INIZIO_DOWNLOAD = "2004-12-01"
PRIMO_ANNO_FORMAZIONE = 2005     # si sceglie a fine 2005 e si detiene il 2006
NOMI_ESENTI = ("Dow Jones", "Dow", "Dogs of the Dow", "SPY", "Dogs", "Dow Jones Industrial Average")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
FILE_ADJ, FILE_CLOSE, FILE_DIV = DATI / "adj.csv", DATI / "close.csv", DATI / "div.csv"
DESCRIZIONE_DATI = "chiusure giornaliere, chiusure corrette per dividendi e dividendi pagati dei titoli del Dow Jones e dello SPY"
URL_FONTE = "https://finance.yahoo.com/"
GIORNI_ANNO = 252
CAPITALE = 500.0
ANNI_MINIMI = 10

# --- Strategia ------------------------------------------------------------------------------------------------------
K_DOGS = 10          # i classici Dogs of the Dow
K_PICCOLI = 5        # variante: i cinque più alti
MIN_STORIA_GG = 200  # un titolo entra in un anno solo se aveva già prezzi per tutto l'anno di formazione
H4_MIN, H4_MAX = 0.40, 0.60   # ipotesi 4: quota di anni in cui i Dogs battono l'universo

# --- Test statistici ------------------------------------------------------------------------------------------------
SEME = 20261030
N_SCIMMIE = 5000
N_BOOTSTRAP = 2000
BLOCCO_BOOTSTRAP = 21
LIVELLO_CONFIDENZA = 0.95

# --- Ipotesi, scritte PRIMA di guardare i risultati -------------------------------------------------------------------
IPOTESI = (
    "1) Il rendimento annuo composto dei Dogs (dieci titoli) è inferiore a quello dell'universo dei trenta a pesi uguali: il rendimento da dividendo non è un fattore che paga. "
    "2) La perdita massima dei Dogs è meno profonda di quella dell'universo: la fama di strategia difensiva regge. "
    "3) I Dogs rendono meno dello SPY nel periodo comune. "
    "4) I Dogs battono l'universo in una quota di anni compresa tra il 40% e il 60%: nessun vantaggio costante. "
    "5) Il valore finale dei Dogs sta tra il quinto e il novantacinquesimo percentile delle scimmie che estraggono ogni anno dieci titoli a caso: la scelta per dividendo non si distingue dalla sorte. "
    "6) La differenza di Sharpe tra Dogs e universo non si distingue dallo zero: l'intervallo di confidenza al 95% la contiene."
)
