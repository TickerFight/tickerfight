"""Parametri dell'articolo n. 202 - "USA contro Europa contro emergenti".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Tre aree, tre ETF quotati in dollari, con i dividendi reinvestiti (prezzo "Adj Close" di Yahoo Finance):
SPY (Stati Uniti), VGK (Europa sviluppata), EEM (mercati emergenti). Si confrontano sul periodo in cui esistono tutti e tre.
Controllo di robustezza con altri tre ETF: VTI, VGK, VWO.
Confronti: rendimento e rischio su tutto il periodo, finestre mobili (3, 5 e 10 anni), correlazioni a un anno mobile e nelle crisi,
persistenza del vincitore (confronto con il caso) e scimmie (una scelta casuale dell'area ogni mese).

Nessun look-ahead: nel test di persistenza la "previsione" usa solo i rendimenti dei cinque anni che finiscono nel mese t;
il risultato si misura sui cinque anni successivi. Nessuna strategia di trading è ottimizzata: tutte le scelte sono fissate qui.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: ETF (ticker Yahoo Finance, nome, area) ---------------------------------------
# Scelti a priori, prima di guardare i dati. Tutti in dollari: chi investe da euro aggiungerebbe l'effetto del cambio.
ETF = [
    ("SPY", "SPDR S&P 500 (Stati Uniti)", "USA"),
    ("VGK", "Vanguard FTSE Europe (Europa)", "Europa"),
    ("EEM", "iShares MSCI Emerging Markets (emergenti)", "Emergenti"),
]
ETF_ALT = [
    ("VTI", "Vanguard Total Stock Market (Stati Uniti)", "USA"),
    ("VGK", "Vanguard FTSE Europe (Europa)", "Europa"),
    ("VWO", "Vanguard FTSE Emerging Markets (emergenti)", "Emergenti"),
]
TUTTI_I_TICKER = sorted({t for t, _, _ in ETF + ETF_ALT})
INIZIO_DOWNLOAD = "1995-01-01"
NOMI_ESENTI = ("S&P 500", "FTSE Europe", "MSCI Emerging Markets", "FTSE Emerging Markets", "Total Stock Market")
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere aggiustate di cinque ETF quotati negli Stati Uniti"
URL_FONTE = "https://finance.yahoo.com/"
COLONNA_PREZZO = "Adj Close"     # prezzo con dividendi reinvestiti
ANNI_MINIMI = 10                 # sotto questa storia comune l'analisi si ferma


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Parametri dell'analisi (fissati prima di guardare i dati) -------------------------------
GIORNI_ANNO = 252
CAPITALE = 500.0                 # per tradurre i rendimenti in dollari nell'articolo
FINESTRE_ANNI = [3, 5, 10]       # finestre mobili: si riportano tutte; quella di riferimento è la seconda
FINESTRA_RIF = 5
GIORNI_VOL = 252                 # volatilità e correlazione mobili a un anno
SOGLIA_CORR = 0.7
QUOTA_MAX_VINCITRICE = 0.70      # ipotesi 3: nessuna area prima in più del 70% delle finestre
QUOTA_MIN_VINCITRICE = 0.10      # ipotesi 3: ogni area prima in almeno il 10% delle finestre

# --- Test statistici -------------------------------------------------------------------
SEME = 20261025
N_SCIMMIE = 5000
N_PERMUTAZIONI = 5000
N_BOOTSTRAP = 2000
BLOCCO_BOOTSTRAP = 21            # giorni per blocco
LIVELLO_CONFIDENZA = 0.95

# --- Finestre di crisi, fissate a priori (date di calendario) ------------------------------------
CRISI = [
    ("Crisi finanziaria", "2008-09-01", "2009-03-09"),
    ("Crollo del Covid", "2020-02-19", "2020-03-23"),
]

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Nel periodo comune il rendimento annuo composto degli Stati Uniti è più alto di quello dell'Europa e dei mercati emergenti; "
    "l'intervallo di confidenza della differenza di Sharpe tra Stati Uniti ed Europa sta tutto sopra lo zero, mentre quello tra "
    "Stati Uniti ed emergenti contiene lo zero. "
    "2) I mercati emergenti hanno una volatilità a un anno più alta di quella degli Stati Uniti in oltre il 90% dei giorni e una perdita massima più profonda. "
    "3) Su finestre mobili di cinque anni la leadership ruota: nessuna delle tre aree è prima in più del 70% delle finestre e ciascuna è prima in almeno il 10%. "
    "4) La correlazione giornaliera a un anno tra Stati Uniti ed Europa ha una mediana superiore a 0,7; nelle due crisi fissate in anticipo "
    "la correlazione di Stati Uniti-Europa e di Stati Uniti-emergenti è più alta che sull'intero periodo in almeno tre casi su quattro. "
    "5) L'area vincitrice nei cinque anni precedenti vince anche nei cinque successivi in una quota di mesi non distinguibile dal caso "
    "(un terzo): il p-value del test di permutazione è sopra il 5%. "
    "6) Scegliere a caso l'area ogni mese (scimmie) dà un rendimento finale più alto del buy & hold sugli Stati Uniti in meno del 5% dei casi."
)
