"""Parametri dell'articolo bonus - "500 euro su Apple con le medie mobili: cinque anni, commissioni e tasse".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni
numero dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.
L'articolo è fuori programmazione e fuori catalogo: per questo la cartella si chiama "bonus" e non ha numero.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
TICKER = "AAPL"                       # Apple, quotata al Nasdaq in dollari
TICKER_CAMBIO = "EURUSD=X"            # dollari per un euro
INIZIO_DOWNLOAD = "2003-01-01"        # serve storia per la media a 200 giorni e per le finestre mobili
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "aapl_giornaliero.csv"
FILE_CAMBIO = DATI / "eurusd_giornaliero.csv"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure e aperture giornaliere di Apple (AAPL) e cambio euro/dollaro"
URL_FONTE = "https://finance.yahoo.com/quote/AAPL/history/"
NOTA_COLONNA = ("Open e Close non corretti per i dividendi (già corretti per gli split): "
                "i dividendi non sono considerati, né per la regola né per il buy & hold")

# --- Scenario dell'investitore ------------------------------------------
CAPITALE = 500.0          # euro
COMMISSIONE = 1.0         # euro per ogni ordine, acquisto o vendita
ALIQUOTA = 0.26           # imposta sulle plusvalenze, in euro, pagata a ogni vendita
ANNI_TEST = 5             # il test copre gli ultimi cinque anni disponibili

# --- Regola, scelta a priori e NON ottimizzata ----------------------------
# Stessa coppia dell'articolo n. 21 (golden cross / death cross). Nessun'altra coppia è stata provata.
SMA_VELOCE = 50
SMA_LENTA = 200
MODO_PRINCIPALE = "apertura"   # segnale a fine seduta t, ordine all'apertura di t+1
MODO_CONTROLLO = "chiusura"    # controllo di robustezza: ordine alla chiusura di t+1

# --- Finestre mobili (robustezza rispetto alla data di partenza) ----------
INIZIO_FINESTRE = "2005-01-01"   # prima data di partenza ammessa; una partenza al mese

# --- Convenzioni ----------------------------------------------------------
GIORNI_ANNO_CALENDARIO = 365.25

# --- Ipotesi, scritta PRIMA di guardare i risultati -------------------------
IPOTESI = (
    "Dopo commissioni e tasse la regola 50/200 non batte il buy & hold in euro su Apple negli ultimi cinque "
    "anni: a ogni uscita con guadagno si paga la tassa e il capitale che rientra è più piccolo, mentre il buy & "
    "hold rimanda l'imposta alla fine. Ci aspettiamo però che la regola riduca la perdita massima."
)
