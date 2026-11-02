"""Parametri dell'articolo n. 524 - "Se avessi sbagliato ogni anno il settore peggiore".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: con il senno di poi, ogni anno si compra il settore (tra i nove ETF settoriali SPDR originali) che a fine anno
risulterà il peggiore: il «contro-fortunato» perfetto. Si confronta con l'S&P 500 (SPY), con il caso (scimmie che scelgono
un settore a caso ogni anno) e con una regola che si poteva davvero applicare (comprare il perdente dell'anno prima).
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
NOMI_ESENTI = ("S&P", "524", "Moskowitz e Grinblatt (1999)", "SPDR", "Select Sector",
               "(1999)", "54(4), 1249–1290", "doi:10.1111/0022-1082.00146")


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

SOGLIE = {"ip1_pp": 15.0, "ip2_quota": 0.50, "ip3_perc": 0.05, "ip4_pp": 2.0, "ip5_frazione": 0.01,
          "ip6_tasse": 0.05, "ip8_lo": 3.0, "ip8_hi": 7.0, "alfa": 0.05}

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Scegliendo ogni anno, con il senno di poi, il settore peggiore, il rendimento annuo composto è negativo e inferiore a quello dell'S&P 500 (SPY) "
    "di almeno 15 punti percentuali. "
    "2) Una scimmia che sceglie un settore a caso ogni anno batte l'S&P 500 (SPY) in meno della metà dei casi. "
    "3) Nessuna scimmia (o meno del 5%) fa peggio della scelta del peggiore con il senno di poi: p-value corretto per Holm sotto 0,05. "
    "4) La regola realizzabile «compra ogni anno il settore che ha perso di più l'anno prima» (contrarian) si scosta dall'S&P 500 (SPY) per meno di 2 punti "
    "percentuali all'anno e non è distinguibile dal caso (p-value bilaterale corretto per Holm sopra 0,05). "
    "5) Se la stessa scelta del peggiore si facesse ogni mese invece che ogni anno, il capitale finale sarebbe meno dell'1% di quello della rotazione annuale. "
    "6) Con 0,1% di costo per ordine e 26% di tassa, la tassa pagata in tutto sulla rotazione del peggiore vale meno del 5% del capitale iniziale "
    "(le perdite non si tassano) e il capitale netto finale è inferiore a quello lordo. "
    "7) In almeno un anno anche il settore peggiore ha chiuso in guadagno. "
    "8) Il perdente dell'anno prima, l'anno dopo, si piazza a metà classifica: la sua posizione mediana tra i nove settori (1 = migliore, 9 = peggiore) "
    "è compresa tra 3 e 7."
)
