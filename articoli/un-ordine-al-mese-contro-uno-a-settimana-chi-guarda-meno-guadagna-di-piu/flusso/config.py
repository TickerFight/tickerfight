"""Parametri dell'articolo n. 579 - "Un ordine al mese contro uno a settimana" (rubrica «trading con poco capitale»).

Scritti PRIMA di guardare qualunque risultato.

La regola è la stessa per tutti: si è investiti se la chiusura sta sopra la media mobile semplice a 200 sedute (parametro classico,
nessuna ottimizzazione). Cambia solo QUANDO si guarda il segnale: ogni seduta ("giornaliera", il riferimento), l'ultima seduta di
ogni settimana ("settimanale") oppure l'ultima seduta di ogni mese ("mensile"). Il segnale calcolato alla chiusura della seduta
di decisione d decide l'ordine della seduta successiva, eseguito alla sua chiusura, e vale fino alla decisione seguente
(nessun look-ahead). I dati sono quelli dell'articolo 578 (stessi strumenti, stesso scarico).
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
SCENARI_COSTO = [("0 euro", 0.0, 0.0), ("2 euro", 2.0, 0.0), ("0,1%", 0.0, 0.001)]
SCENARIO_PRINCIPALE = 1
ALIQUOTA = 0.26
MEDIA_MOBILE = 200
# Frequenze di decisione: (id, nome)
FREQUENZE = [("g", "ogni seduta"), ("s", "una volta a settimana"), ("m", "una volta al mese")]

SEME = 20261027
N_SCIMMIE = 2000
# Prove: 3 strumenti x (buy & hold + 3 frequenze) x 4 scenari = 48 simulazioni. Test: scimmie, 3 strumenti x 3 frequenze = 9, Holm.

IPOTESI = (
    "1) Decidere una volta a settimana fa almeno il doppio degli ordini di decidere una volta al mese, in tutti gli strumenti. "
    "2) Prima di costi e tasse, la decisione settimanale e quella mensile rendono quasi lo stesso: la differenza di rendimento annuo "
    "lordo è sotto un punto percentuale in tutti gli strumenti. "
    "3) Con 2 euro a ordine, la regola mensile rende più della settimanale (netto) in almeno due strumenti su tre. "
    "4) Con la commissione dello 0,1% la differenza netta tra settimanale e mensile è più piccola, in valore assoluto, di quella con "
    "2 euro in almeno due strumenti su tre (la commissione fissa pesa di più su 1.000 euro). "
    "5) Con 2 euro a ordine nessuna delle tre frequenze batte il buy & hold netto in almeno due strumenti su tre. "
    "6) Dopo la correzione di Holm sui 9 test, nessuna delle tre frequenze batte le scimmie (stessa durata investita e stesso "
    "numero di periodi) in almeno due strumenti su tre."
)
