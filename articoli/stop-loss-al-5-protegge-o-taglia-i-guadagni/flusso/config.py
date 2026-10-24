"""Parametri dell'articolo n. 569 - "Stop loss al 5%: protegge o taglia i guadagni?" (rubrica «trading con poco capitale»).

Tutti i parametri dell'analisi stanno qui, scritti PRIMA di guardare qualunque risultato. Gli script numerati li leggono da
questo file: ogni numero dell'articolo si può ricondurre a una scelta dichiarata, e nessun valore è nascosto nel codice.

La regola di trend (nessuna ottimizzazione, parametro classico): si è investiti se la chiusura di oggi sta sopra la media
mobile semplice a 200 sedute. Il segnale calcolato alla chiusura della seduta t decide l'ordine della seduta t+1,
eseguito al prezzo di chiusura di t+1 (nessun look-ahead).
La stessa regola con lo stop loss: alla chiusura di t, se la chiusura è scesa del 5% o più sotto il prezzo di acquisto
(espresso nella valuta dello strumento), si vende alla chiusura di t+1. Dopo uno stop si rientra solo quando il segnale
di trend è prima tornato falso (chiusura sotto la media) e poi di nuovo vero: così lo stop non provoca rientri
immediati nello stesso ribasso. Se nella stessa seduta anche il trend chiede di uscire, l'uscita è del trend: non
conta come stop e non blocca il rientro. (Questa precisazione è stata aggiunta dopo la prima esecuzione, perché un
conteggio mostrava uno stop coincidente con l'uscita di trend; non ha cambiato alcun rendimento.)
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Strumenti (scelti a priori, prima di guardare i dati) ---------------------------------------------------------
# (ticker Yahoo Finance, nome, valuta dello strumento). Due ETF quotati a Milano in euro e l'indice S&P 500 in dollari,
# convertito in euro con il cambio EUR/USD (serve per avere una storia più lunga). Se uno strumento ha meno di
# STORIA_MINIMA_ANNI di storia utile viene scartato e l'articolo lo dichiara.
STRUMENTI = [
    ("SWDA.MI", "ETF azionario mondiale (MSCI World, in euro)", "EUR"),
    ("CSSPX.MI", "ETF sull'S&P 500 (in euro)", "EUR"),
    ("^GSPC", "indice S&P 500 (in dollari, convertito in euro)", "USD"),
]
TICKER_CAMBIO = "EURUSD=X"          # dollari per un euro
INIZIO_DOWNLOAD = "1995-01-01"
STORIA_MINIMA_ANNI = 8
NOMI_ESENTI = ("S&P 500", "MSCI World", "EUR/USD", "SMA200", "SMA 200")   # nomi con cifre: non sono dati dell'analisi
FUSO_BORSA = "Europe/Rome"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere di due ETF quotati a Milano, dell'indice S&P 500 e del cambio euro-dollaro"
URL_FONTE = "https://finance.yahoo.com/"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_").replace("=", "_") + ".csv")


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").replace("=", "_").lower()


# --- Condizioni della rubrica -----------------------------------------------------------------------------------
CAPITALE = 1000.0
# Tre scenari di commissione per ordine, scritti prima: (nome, parte fissa in euro, parte proporzionale all'importo)
SCENARI_COSTO = [
    ("0 euro", 0.0, 0.0),
    ("2 euro", 2.0, 0.0),
    ("0,1%", 0.0, 0.001),
]
SCENARIO_PRINCIPALE = 1      # indice in SCENARI_COSTO: il caso «2 euro» è quello delle tabelle principali
ALIQUOTA = 0.26              # tassa sulle plusvalenze, minusvalenze riportate fino al quarto anno seguente
MODO = "chiusura"

# --- La regola ------------------------------------------------------------------------------------------------------
MEDIA_MOBILE = 200
STOP = 0.05
# Soglie di controllo (robustezza): non servono a scegliere la migliore, ma a vedere se il verdetto dipende dal 5%.
SOGLIE_CONTROLLO = (0.03, 0.08, 0.10)

# --- Test statistici -------------------------------------------------------------------------------------------------
SEME = 20261024
N_SCIMMIE = 5000
N_BOOTSTRAP = 5000
LUNGHEZZA_BLOCCO = 20        # sedute per blocco nel bootstrap a blocchi della differenza di rendimento giornaliero
LIVELLO_CONFIDENZA = 0.95
# Numero dichiarato di prove: 3 strumenti x (1 regola con stop al 5% + 3 soglie di controllo + 1 regola di trend senza stop) x
# 3 scenari di costo. Le conclusioni vengono tratte sullo scenario principale e sullo stop del 5%; i test di ipotesi
# (scimmie e bootstrap) sono 3 per ognuna delle due famiglie e sono corretti con il metodo di Holm.

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------------------------------
IPOTESI = (
    "1) Lo stop loss al 5% riduce la perdita massima dal picco della regola di trend in almeno due strumenti su tre. "
    "2) Lo stop loss al 5% riduce il rendimento annuo netto (scenario principale) rispetto alla sola regola di trend in "
    "almeno due strumenti su tre, perché fa uscire prima dei rimbalzi e fa pagare più ordini. "
    "3) Lo stop loss aumenta il numero di ordini all'anno in tutti gli strumenti. "
    "4) Dopo la correzione di Holm, la differenza media del rendimento giornaliero tra la regola con stop e la regola senza "
    "stop non è statisticamente diversa da zero in nessuno strumento (bootstrap a blocchi). "
    "5) Dopo la correzione di Holm, la regola con lo stop non batte le scimmie (stessa quota di tempo investito e stesso "
    "numero di ordini) in almeno due strumenti su tre. "
    "6) Al netto di costi e tasse nello scenario principale, la regola con lo stop resta sotto il buy & hold in almeno due "
    "strumenti su tre."
)
