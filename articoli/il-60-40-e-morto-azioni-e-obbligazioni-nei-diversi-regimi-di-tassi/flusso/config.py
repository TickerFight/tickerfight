"""Parametri dell'articolo n. 181 - "Il 60/40 è morto? Azioni e obbligazioni nei diversi regimi di tassi".

Tutti i parametri dell'analisi stanno qui, scritti PRIMA di guardare i risultati. Gli script numerati li leggono da questo file.

Il disegno: un portafoglio 60% azioni americane / 40% obbligazioni del Tesoro a 10 anni, ribilanciato a ogni gennaio, dal gennaio 1981
all'ultimo mese completo. Azioni: il fondo Vanguard 500 Index (VFINX), con dividendi reinvestiti. Obbligazioni: serie SINTETICA di un
Treasury a 10 anni a cedola pari, ricostruita mese per mese dal rendimento a 10 anni (^TNX) con la formula esatta del prezzo; la
si controlla contro il fondo Vanguard Total Bond Market (VBMFX) dal 1987. Liquidità: rendimento dei Bot a 13 settimane (^IRX).
Rendimenti nominali, in dollari, lordi di costi e tasse. Il "regime di tassi" di un mese è deciso dal rendimento a 10 anni
della fine del mese PRECEDENTE (nessun look-ahead).
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati (ticker Yahoo Finance, nome, ruolo) ------------------------------------------------------------------
SERIE = [
    ("VFINX", "Vanguard 500 Index (azioni USA, dividendi reinvestiti)", "azioni"),
    ("VBMFX", "Vanguard Total Bond Market Index (controllo delle obbligazioni)", "controllo"),
    ("^TNX", "Rendimento del Treasury a 10 anni (in %)", "tasso10"),
    ("^IRX", "Rendimento dei Bot a 13 settimane (in %)", "cassa"),
]
INIZIO_DOWNLOAD = "1960-01-01"
FUSO_BORSA = "America/New_York"
URL_FONTE = "https://finance.yahoo.com/"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "le serie mensili di un fondo azionario S&P 500, di un fondo obbligazionario e dei rendimenti dei titoli di Stato USA"
NOMI_ESENTI = ("S&P", "TickerFight", "181", "60/40", "VFINX", "VBMFX", "Treasury", "10 anni")


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Il portafoglio ------------------------------------------------------------------------------------------------
INIZIO_CAMPIONE = "1981-01"        # primo mese di rendimento (il fondo azionario parte nel 1980)
PESO_AZIONI = 0.60                 # il resto va in obbligazioni a 10 anni
SCADENZA_OBBL = 10.0               # anni, cedola pari al rendimento del mese precedente
# Il ribilanciamento è sempre al primo mese di ogni anno solare.

# --- Regimi di tassi (rendimento a 10 anni di fine mese precedente, in %) --------------------------------------------
SOGLIA_BASSI = 3.0                 # sotto: tassi bassi
SOGLIA_ALTI = 6.0                  # da qui in su: tassi alti; in mezzo: medi

ORIZZONTE_ANNI = 10                # finestre mobili per la domanda "da che tassi parti?"

# --- Il caso e l'incertezza ------------------------------------------------------------------------------------------
SEME = 20261024
N_SCIMMIE = 2000                   # portafogli con peso azionario a caso (uniforme 0-100%), ripescato ogni gennaio
N_BOOTSTRAP = 2000
BLOCCO_MESI = 12                   # bootstrap a blocchi circolari
LIVELLO_CONFIDENZA = 0.95

# --- Soglie delle ipotesi (riportate qui per scriverle nell'articolo senza cifre a mano) ----------------------------
SOGLIE = {"ip1_anno": 2022, "ip2_diff": 0.20, "ip4_pp": 0.03, "ip6_lo": 0.25, "ip6_hi": 0.75, "ip7_corr": 0.80}

# --- Ipotesi, scritte PRIMA di guardare i risultati ---------------------------------------------------------------
IPOTESI = (
    "1) Il 2022 è l'anno solare peggiore del 60/40 dal 1981 a oggi: peggio anche del 2008, quando le obbligazioni avevano protetto. "
    "2) La correlazione mensile tra azioni e obbligazioni è più alta con tassi alti (10 anni da 6% in su) che con tassi bassi (sotto il 3%): "
    "la differenza è di almeno 0,20. "
    "3) Sull'intero periodo il 60/40 ha un Sharpe ratio più alto delle sole azioni E una perdita massima più piccola. "
    "4) Partire da tassi alti conta: la mediana del rendimento annuo del 60/40 nei 10 anni successivi è più alta di almeno 3 punti percentuali "
    "se si parte con tassi alti rispetto a tassi bassi. "
    "5) Il vantaggio di Sharpe del 60/40 sulle sole azioni non è distinguibile dal caso: l'intervallo di confidenza al 95% (bootstrap a blocchi di 12 mesi) "
    "della differenza comprende lo zero. "
    "6) Il 60/40 non è speciale rispetto a un peso azionario scelto a caso: il suo Sharpe sta tra il 25° e il 75° percentile di 2000 portafogli con peso azionario casuale. "
    "7) Controllo del metodo: la serie sintetica delle obbligazioni a 10 anni ha una correlazione mensile di almeno 0,80 con il fondo obbligazionario reale dal 1987."
)
