"""Parametri dell'articolo n. 581 - "Lo stesso sistema con commissioni 0, 1 e 3 euro per ordine" (rubrica «trading con poco capitale»).

Scritti PRIMA di guardare qualunque risultato.

Il sistema è uno solo e non cambia mai: si è investiti se la chiusura sta sopra la media mobile semplice a 200 sedute (parametro
classico, nessuna ottimizzazione), il segnale è guardato a ogni seduta, l'ordine parte alla chiusura della seduta successiva
(nessun look-ahead). Cambia soltanto la commissione per ordine: 0, 1 e 3 euro (più un esame su una griglia da 0 a 10 euro per
trovare, se esiste, la commissione che azzera il vantaggio sul buy & hold). Tassa del 26% con minusvalenze riportate in tutti gli
scenari netti. I dati sono quelli degli articoli 578 e 579 (stessi strumenti, stesso scarico).
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

STRUMENTI = [
    ("SWDA.MI", "ETF azionario mondiale (MSCI World, in euro)", "EUR"),
    ("CSSPX.MI", "ETF sull'S&P 500 (in euro)", "EUR"),
    ("^GSPC", "indice S&P 500 (in dollari, convertito in euro)", "USD"),
]
TICKER_CAMBIO = "EURUSD=X"
INIZIO_DOWNLOAD = "1995-01-01"
STORIA_MINIMA_ANNI = 8
NOMI_ESENTI = ("S&P 500", "MSCI World", "EUR/USD", "buy & hold", "SMA200")
FUSO_BORSA = "Europe/Rome"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere di due ETF quotati a Milano, dell'indice S&P 500 e del cambio euro-dollaro"
URL_FONTE = "https://finance.yahoo.com/"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_").replace("=", "_") + ".csv")


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").replace("=", "_").lower()


CAPITALE = 1000.0
SCENARI_COSTO = [("0 euro", 0.0, 0.0), ("1 euro", 1.0, 0.0), ("3 euro", 3.0, 0.0)]
SCENARIO_PRINCIPALE = 1
GRIGLIA_FISSA = [0.5 * k for k in range(0, 21)]   # da 0 a 10 euro, passo 0,5
ALIQUOTA = 0.26
MEDIA_MOBILE = 200

SEME = 20261103
N_SCIMMIE = 2000
# Prove: 3 strumenti x (buy & hold + trend) x 4 scenari = 24 simulazioni, più la griglia (21 commissioni x 2 regole x 3 strumenti).
# Test: scimmie, 3 strumenti x 3 commissioni = 9, correzione di Holm.

IPOTESI = (
    "1) La regola fa in media almeno 4 ordini all'anno in tutti gli strumenti (il numero di ordini non dipende dalla commissione). "
    "2) Passare da 0 a 3 euro per ordine toglie almeno mezzo punto di rendimento annuo netto in almeno due strumenti su tre. "
    "3) Con commissione zero, quindi con la sola tassa del 26%, la regola chiude sotto il buy & hold netto in almeno due strumenti su tre. "
    "4) Con 3 euro per ordine la regola chiude sotto il buy & hold netto in tutti gli strumenti. "
    "5) Sulla griglia da 0 a 10 euro, quando il vantaggio sul buy & hold netto esiste a commissione zero, sparisce prima dei 3 euro. "
    "6) Dopo la correzione di Holm sui 9 test, la regola non batte le scimmie (stessa durata investita, stesso numero di periodi) "
    "in modo significativo in nessuno scenario di costo."
)
