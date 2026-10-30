"""Parametri dell'articolo n. 523 - "Se avessi azzeccato ogni anno il settore migliore".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: con il senno di poi, ogni anno si compra il settore (tra i nove ETF settoriali SPDR originali) che a fine anno
risulterà il migliore. Si confronta con l'S&P 500 (SPY), con il caso (scimmie che scelgono un settore a caso ogni anno)
e con una regola che si poteva davvero applicare (comprare il vincitore dell'anno prima).
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: ETF (ticker Yahoo Finance, nome, descrizione). Prezzi corretti per dividendi e frazionamenti ----------
SETTORI = [
    ("XLB", "Materiali", "materiali"),
    ("XLE", "Energia", "energia"),
    ("XLF", "Finanza", "finanza"),
    ("XLI", "Industria", "industria"),
    ("XLK", "Tecnologia", "tecnologia"),
    ("XLP", "Beni di prima necessità", "beni di prima necessità"),
    ("XLU", "Servizi di pubblica utilità", "servizi di pubblica utilità"),
    ("XLV", "Sanità", "sanità"),
    ("XLY", "Consumi discrezionali", "consumi discrezionali"),
]
BENCHMARK = ("SPY", "S&P 500 (ETF SPY)")
TICKER_DATI = [t for t, _, _ in SETTORI] + [BENCHMARK[0]]
INIZIO_DOWNLOAD = "1998-12-01"
FUSO_BORSA = "America/New_York"
URL_FONTE = "https://finance.yahoo.com/"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "i prezzi giornalieri, corretti per i dividendi, dei nove ETF settoriali SPDR originali e dell'ETF SPY sull'S&P 500"
NOMI_ESENTI = ("S&P", "523", "Moskowitz e Grinblatt (1999)", "Hong, Torous e Valkanov (2002)", "Sharpe (1975)",
               "Buzzacchi e Ghezzi (2021)", "SPDR", "Select Sector",
               "(1999)", "(2002)", "(2021)", "(1975)", "54(4), 1249–1290", "doi:10.1111/0022-1082.00146", "14(6), 250")


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Periodo e definizioni -----------------------------------------------------------------------------------
ANNO_INIZIO = 1999            # primo anno solare completo di tutti i nove ETF (nati a dicembre 1998)
ANNO_FINE = 2025              # ultimo anno solare completo alla data del download
CAPITALE_INIZIALE = 10000     # in dollari, per le curve di capitale
FREQUENZE = {"anno": "YE", "trimestre": "QE", "mese": "ME"}   # rotazione con senno di poi ogni anno / trimestre / mese

# --- Il caso -------------------------------------------------------------------------------------------------
SEME = 20261030
N_SCIMMIE = 10000             # scimmie: ognuna sceglie un settore a caso all'inizio di ogni anno
LIVELLO_CONFIDENZA = 0.95

# --- Costi e tasse (scenario netto) -------------------------------------------------------------------------
COSTO_ORDINE = 0.001          # 0,1% per ogni acquisto e per ogni vendita
TASSA = 0.26                  # tassa sulle plusvalenze, con minusvalenze riportate; rotazione: si vende tutto a fine anno

SOGLIE = {"ip1_pp": 10.0, "ip2_quota": 0.50, "ip3_pp": 1.0, "ip3_perc": 0.95, "ip4_volte": 100.0,
          "ip5_frazione": 0.50, "ip7_lo": 3.0, "ip7_hi": 7.0, "alfa": 0.05}

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Scegliendo ogni anno, con il senno di poi, il settore migliore, il rendimento annuo composto supera quello dell'S&P 500 (SPY) "
    "di almeno 10 punti percentuali. "
    "2) Una scimmia che sceglie un settore a caso ogni anno batte l'S&P 500 (SPY) in meno della metà dei casi: i settori scelti a caso non sono "
    "una scorciatoia per battere l'indice. "
    "3) La regola realizzabile «compra ogni anno il settore che ha vinto l'anno prima» non supera l'S&P 500 (SPY) di più di un punto percentuale "
    "all'anno e non batte il 95% delle scimmie (p-value corretto per Holm sopra 0,05); il vantaggio della prima ipotesi è tutto senno di poi. "
    "4) Se la stessa scelta con il senno di poi si facesse ogni mese invece che ogni anno, il capitale finale sarebbe almeno 100 volte quello della "
    "rotazione annuale. "
    "5) Con 0,1% di costo per ordine e 26% di tassa sulle plusvalenze, la rotazione annuale perfetta tiene meno della metà del capitale finale lordo, "
    "ma resta sopra l'S&P 500 (SPY) a parità di costi e tasse. "
    "6) In almeno un anno anche il settore migliore ha chiuso in perdita. "
    "7) Il vincitore dell'anno prima, l'anno dopo, si piazza in media a metà classifica: la sua posizione mediana tra i nove settori è compresa tra 3 e 7 "
    "(nessuna persistenza evidente)."
)
