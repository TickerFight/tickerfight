"""Parametri dell'articolo bonus - "50 titoli dell'S&P 500, la regola 50/200 e il buy & hold: la classifica".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni
numero dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.
L'articolo è fuori programmazione e fuori catalogo: per questo la cartella si chiama "bonus" e non ha numero.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
DATI_TITOLI = DATI / "titoli"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
TICKER_CAMBIO = "EURUSD=X"            # dollari per un euro
INIZIO_DOWNLOAD = "2020-01-01"        # serve storia per la media a 200 giorni prima dell'inizio del test
FUSO_BORSA = "America/New_York"
FILE_COMPOSIZIONE = DATI / "sp500_composizione.csv"     # elenco dei componenti, salvato al momento del download
FILE_CAMBIO = DATI / "eurusd_giornaliero.csv"
FILE_METADATI = DATI / "metadati.json"
URL_COMPOSIZIONE = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
DESCRIZIONE_DATI = "chiusure e aperture giornaliere di 50 titoli dell'S&P 500 e cambio euro/dollaro"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = ("Open e Close non corretti per i dividendi (già corretti per gli split): "
                "i dividendi non sono considerati, né per la regola né per il buy & hold")

# --- Scelta dei 50 titoli, fissata PRIMA di guardare i risultati ----------
# Dall'elenco dei componenti dell'S&P 500 al momento del download si mescola l'ordine con un seme fisso e si
# prendono i primi 50 che hanno i dati completi (cinque anni di test più i 200 giorni della media lenta).
# Nessun titolo viene scelto o scartato guardando come è andata la regola.
N_TITOLI = 50
SEME = 2026
SEDUTE_MINIME_PRIMA = 300         # sedute di dati richieste prima dell'inizio del test (200 servono alla media)

# --- Scenario dell'investitore (per ciascun titolo) -----------------------
CAPITALE = 500.0          # euro per titolo
COMMISSIONE = 1.0         # euro per ogni ordine, acquisto o vendita
ALIQUOTA = 0.26           # imposta sulle plusvalenze, in euro, pagata a ogni vendita
ANNI_TEST = 5             # il test copre gli ultimi cinque anni disponibili

# --- Regola, scelta a priori e NON ottimizzata ----------------------------
SMA_VELOCE = 50
SMA_LENTA = 200
MODO_PRINCIPALE = "apertura"   # segnale a fine seduta t, ordine all'apertura di t+1
MODO_CONTROLLO = "chiusura"    # controllo di robustezza: ordine alla chiusura di t+1
N_CLASSIFICA = 5               # quanti titoli mostrare in testa e in coda alla classifica

# --- Ipotesi, scritta PRIMA di guardare i risultati -------------------------
IPOTESI = (
    "Su 50 titoli dell'S&P 500 la regola 50/200, dopo commissioni e tasse e misurata in euro, batte il buy & hold "
    "in meno della metà dei casi e la differenza mediana è negativa. Ci aspettiamo che la regola vinca soprattutto "
    "sui titoli che nei cinque anni sono scesi o rimasti fermi, e che perda di più sui titoli che sono saliti "
    "molto. Sulla perdita massima ci aspettiamo un vantaggio medio della regola, ma non sistematico."
)
