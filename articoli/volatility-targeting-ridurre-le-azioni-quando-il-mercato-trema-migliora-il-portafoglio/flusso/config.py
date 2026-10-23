"""Parametri dell'articolo n. 241 - "Volatility targeting".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Strategia: a fine mese si misura la volatilità degli ultimi 21 giorni di borsa; il peso in azioni del mese successivo
è obiettivo / volatilità annualizzata, con tetto a 1 (nessuna leva), il resto in cassa (che non rende).
Confronto con il buy & hold sullo stesso indice, con un portafoglio a peso costante e con migliaia di scimmie che
usano gli stessi pesi, ma in mesi a caso.

Regola anti look-ahead: il peso calcolato con la chiusura dell'ultima seduta del mese t viene scambiato alla chiusura
della seduta successiva e comincia a lavorare sul rendimento della seduta ancora dopo (segnale di ieri, posizione di oggi).
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: indici azionari (ticker Yahoo Finance, nome, valuta) -------------------
# Scelti a priori, prima di guardare i dati: sono indici di prezzo (senza dividendi), nella valuta locale.
# Il confronto è sempre fatto dentro lo stesso indice. Se Yahoo non restituisce abbastanza storia, l'indice è scartato.
INDICI = [
    ("^GSPC", "S&P 500 (Stati Uniti)", "USD"),
    ("^IXIC", "Nasdaq Composite (Stati Uniti)", "USD"),
    ("^GDAXI", "DAX (Germania)", "EUR"),
    ("^FTSE", "FTSE 100 (Regno Unito)", "GBP"),
    ("^FCHI", "CAC 40 (Francia)", "EUR"),
    ("^N225", "Nikkei 225 (Giappone)", "JPY"),
]
INDICE_PRINCIPALE = "^GSPC"          # quello dei grafici di dettaglio
INIZIO_DOWNLOAD = "1960-01-01"
NOMI_ESENTI = ("S&P 500", "Nasdaq Composite", "FTSE 100", "CAC 40", "Nikkei 225")
FUSO_BORSA = "America/New_York"
ANNI_MINIMI = 15            # sotto questa soglia l'indice viene scartato
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere di sei indici azionari"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = "Si usano solo le chiusure, in valuta locale, senza dividendi"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- La strategia (parametri fissati prima di guardare i dati) ------------------------------
OBIETTIVO_VOL = 0.10        # volatilità annua obiettivo
FINESTRA = 21               # giorni di borsa per misurare la volatilità
GIORNI_ANNO = 252
TETTO_PESO = 1.0            # nessuna leva
COSTO_BP = 5.0              # costo di ogni scambio, in punti base sul valore scambiato (solo dato di scenario)
CAPITALE = 500.0            # per tradurre i rendimenti in euro nell'articolo

# --- Varianti di robustezza: si riportano TUTTE, nessuna è scelta a posteriori ----------------------------
VARIANTI = [
    # (etichetta, obiettivo, finestra, tetto)
    ("base", 0.10, 21, 1.0),
    ("obiettivo 8%", 0.08, 21, 1.0),
    ("obiettivo 15%", 0.15, 21, 1.0),
    ("finestra 63", 0.10, 63, 1.0),
    ("tetto 1,5 (con leva, finanziamento a costo zero)", 0.10, 21, 1.5),
]

# --- Test statistici -------------------------------------------------------------------
SEME = 20261023
N_SCIMMIE = 5000
N_BOOTSTRAP = 2000
BLOCCO_BOOTSTRAP = 21       # giorni per blocco
LIVELLO_CONFIDENZA = 0.95

# --- Finestre di crisi, fissate a priori (date di calendario) ------------------------------------
CRISI = [
    ("Crisi finanziaria", "2008-09-01", "2009-03-09"),
    ("Crollo del Covid", "2020-02-19", "2020-03-23"),
]

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) In tutti gli indici la volatilità realizzata della strategia è più bassa di quella del buy & hold e varia meno "
    "nel tempo (deviazione standard della volatilità a un anno più bassa). "
    "2) In tutti gli indici la perdita massima della strategia è più piccola di quella del buy & hold. "
    "3) Dopo i costi il rendimento annuo della strategia è più basso di quello del buy & hold in almeno quattro indici su sei, "
    "perché con il tetto a 1 e la cassa a rendimento zero si è in media meno esposti; l'indice di Sharpe invece non è "
    "più alto in modo significativo: l'intervallo di confidenza della differenza contiene lo zero in almeno quattro indici su sei. "
    "4) Le scimmie (stessi pesi, mesi a caso) hanno un Sharpe più alto di quello della strategia in meno del cinque per cento "
    "dei casi in almeno metà degli indici: il momento in cui si riduce l'esposizione conta, non solo quanto si riduce."
)
