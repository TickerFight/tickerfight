"""Parametri dell'articolo n. 525 - "I giorni migliori e peggiori sono vicini: perché?".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Si chiamano «giorni estremi» l'1% di sedute con il rendimento più alto (i giorni migliori) e l'1% con il rendimento
più basso (i giorni peggiori) di ciascun indice. Si misura quanto sono vicini nel tempo, si confronta con il caso
(le stesse sedute con i rendimenti rimescolati), e si cerca la spiegazione nella volatilità di ieri.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: indici di prezzo (ticker Yahoo Finance, nome, valuta) -----------------------------------------------
INDICI = [
    ("^GSPC", "S&P 500 (Stati Uniti)", "USD"),
    ("^GDAXI", "DAX (Germania)", "EUR"),
    ("^FTSE", "FTSE 100 (Regno Unito)", "GBP"),
    ("^N225", "Nikkei 225 (Giappone)", "JPY"),
]
INIZIO_DOWNLOAD = "1927-01-01"
FUSO_BORSA = "America/New_York"
URL_FONTE = "https://finance.yahoo.com/"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere di quattro indici azionari (S&P 500, DAX, FTSE 100, Nikkei 225)"
NOMI_ESENTI = ("S&P", "DAX", "FTSE 100", "Nikkei 225", "FTSE", "525", "Nikkei", "2009", "1982", "1963", "987-1008", "50(4)", "80%", "294632", "1928")
INDICE_PRINCIPALE = "^GSPC"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Definizioni ----------------------------------------------------------------------------------------------
QUOTA_ESTREMI = 0.01          # l'1% delle sedute con rendimento più alto e l'1% con quello più basso
FINESTRA_VICINO = 10          # "vicino" = entro 10 sedute (prima o dopo)
LAMBDA_EWMA = 0.94            # volatilità di ieri: media mobile esponenziale dei quadrati (RiskMetrics), solo dati fino a ieri
RODAGGIO = 60                 # sedute iniziali scartate dalla serie standardizzata
FINESTRA_VOL = 60             # volatilità "di ieri" per la classificazione in quintili: deviazione standard delle ultime 60 sedute fino a ieri
N_ANNI_TOP = 5                # i cinque anni con più giorni estremi

# --- Il caso ------------------------------------------------------------------------------------------------------
SEME = 20261026
N_RIMESCOLATE = 2000          # storie finte: gli stessi rendimenti giornalieri in ordine casuale
N_SCIMMIE = 1000              # scimmie che stanno fuori dal mercato per lo stesso numero di sedute, scelte a caso
LIVELLO_CONFIDENZA = 0.95

# --- Il filtro (strategia di prova) --------------------------------------------------------------------------------
FINESTRA_FILTRO = 20          # volatilità = deviazione standard degli ultimi 20 rendimenti fino a ieri
PERCENTILE_FILTRO = 0.80      # liquidità se la volatilità supera l'80° percentile della propria storia fino a ieri (storia espandente)
STORIA_MINIMA = 500           # sedute di storia prima che il filtro possa scattare
COSTO_CAMBIO = 0.001          # 0,1% per ogni passaggio tra mercato e liquidità (scenario con costi)
LIQUIDITA_RENDE = 0.0         # la liquidità non rende

SOGLIE = {"ip1_alfa": 0.05, "ip2_rapporto": 2.0, "ip3_quota": 0.40, "ip4_dimezza": 0.5,
          "ip5_evitati": 0.50, "ip5_rapp_lo": 0.8, "ip5_rapp_hi": 1.5, "ip6_perc": 0.95, "ip6_cagr_pp": 1.0,
          "ip7_top": 0.35}

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) In ciascuno dei quattro indici, la distanza mediana tra un giorno peggiore e il giorno migliore più vicino è più "
    "corta di quella delle storie rimescolate: il caso viene rifiutato (p corretto per Holm sotto 0,05). "
    "2) Nell'S&P 500, la quota di giorni peggiori con almeno un giorno migliore entro 10 sedute è almeno il doppio di quella "
    "delle storie rimescolate. "
    "3) Nell'S&P 500, almeno il 40% dei giorni estremi (migliori e peggiori) cade nel quinto di sedute con la volatilità di "
    "ieri più alta (il caso ne darebbe il 20%): i giorni estremi sono vicini perché la volatilità resta alta. "
    "4) Se si dividono i rendimenti per la volatilità di ieri (rendimenti standardizzati), l'eccesso di vicinanza rispetto "
    "al caso (rapporto meno uno, nell'S&P 500) si dimezza almeno: la volatilità spiega più di metà del fenomeno. "
    "5) Un filtro «fuori dal mercato quando la volatilità è nel quinto più alto della sua storia» evita almeno la metà dei "
    "giorni peggiori, ma anche almeno la metà dei giorni migliori: il rapporto tra le due quote evitate sta tra 0,8 e 1,5 "
    "(i giorni migliori abitano nello stesso quartiere dei peggiori). "
    "6) Nell'S&P 500 il filtro batte almeno il 95% delle scimmie (stesso numero di sedute in liquidità, scelte a caso), "
    "ma il suo rendimento annuo composto non supera il buy & hold di più di un punto percentuale, nemmeno senza costi. "
    "7) Nell'S&P 500 almeno il 35% dei giorni estremi sta nei cinque anni con più giorni estremi (il caso ne darebbe una quota molto più bassa)."
)
