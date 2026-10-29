"""Parametri dell'articolo n. 570 - "Trailing stop contro uscita a tempo: quale delle due regole di uscita costa meno?" (rubrica «trading con poco capitale»).

Tutti i parametri dell'analisi stanno qui, scritti PRIMA di guardare qualunque risultato. Gli script numerati li leggono da
questo file: ogni numero dell'articolo si può ricondurre a una scelta dichiarata, e nessun valore è nascosto nel codice.

L'ingresso è uguale per tutte le regole (nessuna ottimizzazione, parametro classico): si compra quando la chiusura sta
sopra la media mobile semplice a 200 sedute. Il segnale calcolato alla chiusura della seduta t decide l'ordine della
seduta t+1, eseguito al prezzo di chiusura di t+1 (nessun look-ahead). Cambia solo l'uscita:
  - "tr"  uscita di trend (riferimento): si vende quando la chiusura torna sotto la media;
  - "ts10" trailing stop del 10%: si vende quando la chiusura sta il 10% o più sotto il massimo delle chiusure dall'acquisto;
  - "tt60" uscita a tempo: si vende quando sono passate 60 sedute dall'acquisto (circa tre mesi).
Con il trailing stop e con l'uscita a tempo il segnale di trend serve solo per entrare. Dopo l'uscita si rientra solo
dopo che il segnale è tornato falso e poi vero; se il segnale è già falso al momento dell'uscita, si rientra alla prima
risalita sopra la media. Le soglie di controllo (5% e 15%; 20 e 120 sedute) servono a vedere se il verdetto dipende dalla
soglia scelta, non a scegliere la migliore: la regola principale resta 10% contro 60 sedute.
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
TRAIL = 0.10
TEMPO = 60
# Soglie di controllo (robustezza): non servono a scegliere la migliore.
TRAIL_CONTROLLO = (0.05, 0.15)
TEMPO_CONTROLLO = (20, 120)

# --- Test statistici -------------------------------------------------------------------------------------------------
SEME = 20261024
N_SCIMMIE = 5000
N_BOOTSTRAP = 5000
LUNGHEZZA_BLOCCO = 20        # sedute per blocco nel bootstrap a blocchi della differenza di rendimento giornaliero
LIVELLO_CONFIDENZA = 0.95
# Numero dichiarato di prove: 3 strumenti x 8 regole (buy & hold, uscita di trend, trailing stop 10% + 2 controlli,
# uscita a 60 sedute + 2 controlli) x 4 scenari (lordo e tre di costo). Le conclusioni si traggono sullo scenario principale e
# sulle due regole principali (10% e 60 sedute); i test di ipotesi (scimmie e bootstrap) sono 3 per ognuna delle tre famiglie
# (scimmie sul trailing stop, scimmie sull'uscita a tempo, bootstrap della differenza) e sono corretti con Holm sugli strumenti.

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------------------------------
IPOTESI = (
    "1) Il trailing stop del 10% ha una perdita massima dal picco più piccola dell'uscita a 60 sedute in almeno due "
    "strumenti su tre (il trailing stop esce quando il prezzo scende; l'uscita a tempo esce comunque, anche in pieno rialzo, "
    "e rientra solo dopo un nuovo incrocio). "
    "2) Il trailing stop del 10% ha un rendimento annuo netto (scenario principale) più alto dell'uscita a 60 sedute in "
    "almeno due strumenti su tre, perché lascia correre i rialzi lunghi e fa pagare meno ordini. "
    "3) Dopo la correzione di Holm, la differenza media del rendimento giornaliero netto tra le due regole non è "
    "statisticamente diversa da zero in nessuno strumento (bootstrap a blocchi). "
    "4) Dopo la correzione di Holm, nessuna delle due regole batte le scimmie (stessa quota di tempo investito e stesso "
    "numero di ordini) in almeno due strumenti su tre. "
    "5) Al netto di costi e tasse nello scenario principale, entrambe le regole restano sotto il buy & hold in almeno due "
    "strumenti su tre."
)
