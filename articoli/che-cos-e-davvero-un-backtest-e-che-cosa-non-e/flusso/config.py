"""Parametri dell'articolo n. 1 - "Che cos'è davvero un backtest, e che cosa non è?".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: un backtest è una misura su una sola storia, non una previsione. Si costruisce con tre pezzi (segnale, esecuzione,
rendimenti) e si legge sempre contro un termine di paragone. Prendiamo la regola più nota in assoluto, «investito solo
quando la chiusura è sopra la media a 200 giorni», la applichiamo allo SPY (ETF sull'S&P 500) e la confrontiamo con il
buy & hold, con le diverse epoche, con tutte le finestre di dieci anni e con mille calendari casuali.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
TICKER = "SPY"                    # ETF sull'S&P 500, dal 1993
INIZIO_DOWNLOAD = "1993-01-01"
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "spy_giornaliero.csv"
FILE_METADATI = DATI / "spy_metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere dell'ETF SPY (chiusura per il segnale, chiusura corretta per i dividendi per i rendimenti)"
URL_FONTE = "https://finance.yahoo.com/quote/SPY/history/"
NOMI_ESENTI = ("SPY",)

# --- La regola (scelta a priori, non ottimizzata) ---------------------------------------------
# Sempre investiti se la chiusura di ieri è sopra la media a 200 giorni di ieri, altrimenti in cassa (rendimento zero).
SMA = 200
RITARDO_ONESTO = 1               # il segnale della chiusura di ieri decide la posizione di oggi
RITARDO_ESECUZIONE = 2           # variante: l'ordine viene eseguito alla chiusura successiva
INIZIO_TEST_SEDUTE = 250         # le prime sedute servono per la media; regola e buy & hold partono dallo stesso giorno
CAPITALE = 10000.0               # valori lordi, senza commissioni né tasse

# --- Epoche, finestre, caso ---------------------------------------------
SOTTOPERIODI = [
    ("dal 1994 al 2002", None, "2002-12-31"),
    ("dal 2003 al 2012", "2003-01-01", "2012-12-31"),
    ("dal 2013 a oggi", "2013-01-01", None),
]
FINESTRA_SEDUTE = 2520           # circa dieci anni di borsa
PASSO_FINESTRA = 21              # una finestra nuova ogni mese di borsa
N_CASUALI = 1000                 # calendari casuali
SEME = 42
PERCENTILE_ALTO = 95
COSTO_DECIMO = 0.001             # un decimo di punto percentuale per ogni cambio di posizione (solo per dare un'idea)

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Sull'intero periodo, la regola sopra la media a 200 giorni rende meno all'anno del buy & hold sullo SPY (lordo costi). "
    "2) La perdita massima dal picco della regola è minore di quella del buy & hold. "
    "3) Il confronto non ha un verdetto unico: la regola batte il buy & hold in almeno una delle tre epoche e perde in almeno un'altra, "
    "e nelle finestre mobili di dieci anni la quota di finestre in cui vince sta tra il 20% e l'80%. "
    "4) Contro 1.000 calendari casuali con gli stessi periodi dentro e fuori (stessi blocchi, ordine mescolato), la perdita massima della regola "
    "è meno profonda di quella di almeno 95 calendari su 100. "
    "5) Sempre contro i calendari casuali, il rendimento annuo della regola NON supera il 95° percentile: "
    "ciò che la regola migliora è il rischio, non il rendimento."
)
