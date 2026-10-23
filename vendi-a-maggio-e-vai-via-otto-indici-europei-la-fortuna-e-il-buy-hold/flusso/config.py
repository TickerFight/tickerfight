"""Parametri dell'articolo n. 171 - "Halloween indicator in Europa".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Strategia Halloween: investiti da novembre ad aprile (si compra alla chiusura dell'ultima seduta di ottobre, si vende
alla chiusura dell'ultima seduta di aprile), in cassa da maggio a ottobre. Confronto con il buy & hold sullo stesso
indice, con i dodici "calendari" possibili di sei mesi e con migliaia di scimmie che hanno la stessa dieta
(stesso numero di ordini e stessa durata di ogni periodo investito, ma piazzati a caso dentro ogni anno).
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: indici azionari europei (ticker Yahoo Finance, nome, valuta) --------
# Scelti a priori, prima di guardare i dati. Se Yahoo non restituisce abbastanza storia l'indice viene scartato e
# l'articolo lo dichiara. Il DAX è un indice "total return" (include i dividendi), gli altri sono indici di prezzo:
# il confronto è sempre fatto dentro lo stesso indice, quindi la differenza di costruzione non cambia il confronto.
INDICI = [
    ("^GDAXI", "DAX (Germania)", "EUR"),
    ("^FTSE", "FTSE 100 (Regno Unito)", "GBP"),
    ("^FCHI", "CAC 40 (Francia)", "EUR"),
    ("^SSMI", "SMI (Svizzera)", "CHF"),
    ("^IBEX", "IBEX 35 (Spagna)", "EUR"),
    ("^AEX", "AEX (Paesi Bassi)", "EUR"),
    ("^STOXX50E", "Euro Stoxx 50", "EUR"),
    ("FTSEMIB.MI", "FTSE MIB (Italia)", "EUR"),
]
INIZIO_DOWNLOAD = "1980-01-01"
NOMI_ESENTI = ("FTSE 100", "CAC 40", "IBEX 35", "Euro Stoxx 50")   # nomi di indici con cifre: non sono dati dell'analisi
FUSO_BORSA = "Europe/Berlin"
STAGIONI_MINIME = 15        # sotto questa soglia l'indice viene scartato
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere di otto indici azionari europei"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = ("Si usano solo le chiusure. I valori sono nella valuta locale di ciascun indice, senza cambio: "
                "capitale e commissione sono espressi in quella valuta")


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Scenario dell'investitore (come gli articoli precedenti) -------------------
CAPITALE = 500.0
COMMISSIONE = 1.0
ALIQUOTA = 0.26
MODO = "chiusura"

# --- La strategia -------------------------------------------------------------------
MESI_INVESTITI = (11, 12, 1, 2, 3, 4)       # novembre-aprile
DATA_PUBBLICAZIONE = 2002                    # anno dell'articolo di Bouman e Jacobsen: prima/dopo

# --- Test statistici -------------------------------------------------------------------
SEME = 20261021
N_SCIMMIE = 5000
N_BOOTSTRAP = 5000
LIVELLO_CONFIDENZA = 0.95

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) In almeno sei indici su otto il rendimento medio del semestre novembre-aprile è più alto di quello del semestre "
    "maggio-ottobre. "
    "2) Dopo costi e tasse la strategia Halloween batte il buy & hold in meno della metà degli indici, perché sta fuori "
    "dal mercato metà del tempo. "
    "3) Dopo la correzione di Holm, in meno della metà degli indici la strategia batte le scimmie con la stessa dieta con "
    "una significatività del cinque per cento: l'effetto stagionale, preso da solo, non si distingue dalla fortuna. "
    "4) Dopo il 2002 (anno dell'articolo che ha reso famoso l'effetto) la differenza media tra i due semestri è più piccola "
    "di prima in almeno metà degli indici."
)
