"""Parametri dell'articolo n. 515 - "La scimmia con il dardo contro la media mobile".

Tutti i parametri dell'analisi stanno qui, scritti prima di guardare i risultati.

Regola: si è investiti quando la chiusura di ieri è sopra la sua media mobile semplice (n sedute), altrimenti si sta in
liquidità (che non rende). Il segnale di ieri decide la posizione di oggi: nessun look-ahead.
Scimmie: stessa quota di tempo investito della regola.
  - «scimmie a blocchi»: stesso numero di operazioni e stesse durate dei periodi dentro e fuori, ma messe in ordine casuale;
  - «scimmie a moneta»: ogni seduta investita con probabilità pari alla quota della regola (molte più operazioni; solo senza costi).
Tutti i confronti partono dallo stesso giorno (dopo la media più lunga), per regola, buy & hold e scimmie.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

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
NOMI_ESENTI = ("S&P", "DAX", "FTSE 100", "Nikkei 225", "FTSE", "515", "Nikkei", "Holm", "1992", "1999", "1998", "47(5)", "54(5)",
               "1731-1764", "1647-1691", "SMA", "1897", "1986", "N225")
INDICE_PRINCIPALE = "^GSPC"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- La famiglia di regole ----------------------------------------------------------------------------------------
LUNGHEZZE = (50, 100, 150, 200, 250)   # medie mobili semplici provate (sedute); tutte dichiarate, nessuna scelta dopo
LUNGHEZZA_PRINCIPALE = 200             # la regola classica, scelta prima di guardare i dati
COSTO_CAMBIO = 0.001                   # 0,1% del valore a ogni acquisto o vendita (scenario con costi)
SEDUTE_ANNO = 252

# --- Il caso -------------------------------------------------------------------------------------------------------
SEME = 20261028
N_SCIMMIE = 1000
LIVELLO_CONFIDENZA = 0.95
DATA_SPARTIACQUE = "1975-01-01"        # per dividere la storia dell'S&P 500 in due metà

SOGLIE = {"ip1_indici": 3, "ip2_pp": 0.10, "ip3_indici": 3, "ip3_alfa": 0.05, "ip4_meta": 10,
          "ip5_perc": 0.90, "ip6_pp": 0.005, "ip7_perc": 0.90}

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Senza costi, il rendimento annuo composto della media a 200 sedute è più basso di quello del buy & hold in almeno "
    "3 indici su 4 (indici di prezzo, senza dividendi). "
    "2) La perdita massima della media a 200 sedute è meno profonda di quella del buy & hold di almeno 10 punti percentuali "
    "in tutti e 4 gli indici. "
    "3) Il rapporto di Sharpe della media a 200 sedute batte il 95% delle scimmie a blocchi (stessa quota e stesso numero di "
    "operazioni), con p corretto per Holm sotto 0,05, in almeno 3 indici su 4. "
    "4) Sul rendimento annuo composto la regola batte il 95% delle scimmie a blocchi, con p corretto per Holm sotto 0,05, in "
    "meno di 10 delle 20 combinazioni (4 indici per 5 lunghezze): la tempistica da sola non regala rendimento. "
    "5) Nell'S&P 500 il rapporto di Sharpe della regola sta sopra il 90° percentile delle scimmie a blocchi per tutte e 5 le "
    "lunghezze: il risultato non dipende dalla lunghezza scelta. "
    "6) Con un costo dello 0,1% per operazione il rendimento annuo della media a 200 sedute sull'S&P 500 scende di meno di "
    "0,5 punti percentuali rispetto al caso senza costi. "
    "7) Dividendo la storia dell'S&P 500 al 1975, il rapporto di Sharpe della media a 200 sedute sta sopra il 90° percentile "
    "delle scimmie a blocchi in entrambe le metà."
)
