"""Parametri dell'articolo n. 182 - "Il Portafoglio Permanente: funziona davvero, o ha solo avuto la fortuna dell'oro?".

Tutti i parametri dell'analisi stanno qui, scritti PRIMA di guardare i risultati. Gli script numerati li leggono da questo file.

Il disegno: il Portafoglio Permanente di Harry Browne mette un quarto in azioni, un quarto in obbligazioni di Stato a lunga scadenza,
un quarto in oro e un quarto in liquidità, ribilanciato ogni gennaio. Lo seguiamo dal settembre 2000 (primo mese con un prezzo dell'oro
su Yahoo Finance) all'ultimo mese completo. Azioni: fondo Vanguard 500 Index (VFINX). Obbligazioni lunghe: fondo Vanguard Long-Term
Treasury (VUSTX). Oro: future continuo sull'oro (GC=F); controllo con l'ETF GLD. Liquidità: Bot a 13 settimane (^IRX), reso mese per mese.
Confronti: sole azioni, 60/40 (VFINX + VBMFX), il portafoglio senza oro, il portafoglio senza liquidità, e 2000 «scimmie» con pesi casuali.
Rendimenti nominali, in dollari, lordi di costi e tasse.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati (ticker Yahoo Finance, nome, ruolo) ------------------------------------------------------------------
SERIE = [
    ("VFINX", "Vanguard 500 Index (azioni USA, dividendi reinvestiti)", "azioni"),
    ("VUSTX", "Vanguard Long-Term Treasury (obbligazioni di Stato a lunga scadenza)", "obbligazioni"),
    ("GC=F", "Future continuo sull'oro (dollari per oncia)", "oro"),
    ("GLD", "SPDR Gold Shares (controllo dell'oro)", "controllo"),
    ("VBMFX", "Vanguard Total Bond Market Index (per il 60/40)", "obbl_aggregate"),
    ("^IRX", "Rendimento dei Bot a 13 settimane (in %)", "cassa"),
]
INIZIO_DOWNLOAD = "1995-01-01"
FUSO_BORSA = "America/New_York"
URL_FONTE = "https://finance.yahoo.com/"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "le serie mensili di un fondo azionario S&P 500, di un fondo di titoli di Stato a lunga scadenza, dell'oro e dei Bot americani"
NOMI_ESENTI = ("S&P", "TickerFight", "182", "60/40", "VFINX", "VUSTX", "VBMFX", "GC=F", "GLD", "25/25/25/25", "Treasury", "1/N")


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_").replace("=", "_") + ".csv")


# --- I portafogli (pesi: azioni, obbligazioni lunghe, oro, liquidità) -----------------------------------------------------
INIZIO_CAMPIONE = "2000-09"
PESI = {
    "pp": (0.25, 0.25, 0.25, 0.25),         # Portafoglio Permanente
    "senza_oro": (1 / 3, 1 / 3, 0.0, 1 / 3),
    "senza_cassa": (1 / 3, 1 / 3, 1 / 3, 0.0),
}
PESO_AZIONI_6040 = 0.60                      # 60/40: VFINX + VBMFX
# Ribilanciamento sempre al primo mese di ogni anno solare.
DIVISIONE_PERIODO = "2012-01"                # primo mese del secondo sotto-periodo (scelto a priori)
INIZIO_CONTROLLO_ORO = "2004-12"             # il GLD nasce a novembre 2004

# --- Il caso e l'incertezza ------------------------------------------------------------------------------------------
SEME = 20261031
N_SCIMMIE = 2000                   # portafogli con pesi casuali (Dirichlet uniforme sui 4 asset), estratti di nuovo ogni gennaio
N_BOOTSTRAP = 2000
BLOCCO_MESI = 12
LIVELLO_CONFIDENZA = 0.95

SOGLIE = {"ip3_anno": 2022, "ip7_perc": 0.50, "ip9_corr": 0.95}

# --- Ipotesi, scritte PRIMA di guardare i risultati ---------------------------------------------------------------
IPOTESI = (
    "1) Il Portafoglio Permanente ha una perdita massima dal picco più piccola sia delle sole azioni sia del 60/40. "
    "2) Il suo Sharpe ratio è più alto di quello delle sole azioni. "
    "3) Il suo rendimento annuo composto è più basso di quello delle sole azioni: la protezione si paga in rendimento. "
    "4) Il suo anno solare peggiore è il 2022, non il 2008: l'anno in cui le obbligazioni lunghe crollano. "
    "5) L'oro conta: il Portafoglio Permanente ha uno Sharpe più alto della versione senza oro (un terzo azioni, un terzo obbligazioni lunghe, un terzo liquidità). "
    "6) La liquidità serve a limitare le perdite: la versione senza liquidità (un terzo azioni, obbligazioni lunghe, oro) ha una perdita massima più grande. "
    "7) Il vantaggio di Sharpe sulle sole azioni non è distinguibile dal caso: l'intervallo di confidenza al 95% (bootstrap a blocchi di 12 mesi) comprende lo zero. "
    "8) Contro il caso: lo Sharpe del Portafoglio Permanente supera quello di più della metà di 2000 portafogli con pesi casuali. "
    "9) Il vantaggio di Sharpe sul 60/40 è più grande nel periodo del grande rialzo dell'oro (fino a dicembre 2011) che dopo (da gennaio 2012). "
    "10) Controllo del metodo: la serie dell'oro (future) ha una correlazione mensile di almeno 0,95 con l'ETF GLD dal dicembre 2004."
)
