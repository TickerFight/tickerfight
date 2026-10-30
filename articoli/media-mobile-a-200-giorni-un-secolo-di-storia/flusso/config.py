"""Parametri dell'articolo n. 122 - "Media mobile a 200 giorni: un secolo di storia".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati di QUESTO articolo.
Attenzione: nell'articolo 82 abbiamo già confrontato lo Sharpe di questa stessa regola con quello del buy & hold (la regola vinceva): la terza ipotesi è quindi dichiarata come già nota.

La regola: si resta investiti nell'S&P 500 (indice di prezzo, dal 1927, senza dividendi) se la chiusura è sopra la media semplice delle ultime 200 chiusure, altrimenti si sta in liquidità
con rendimento zero. Il segnale della chiusura del giorno t vale per il rendimento del giorno t+1. Si confronta con il buy & hold sugli stessi giorni per rendimento annuo composto, Sharpe,
massima perdita dal massimo (drawdown) e numero di operazioni; poi per decennio; poi con un costo per ogni cambio di posizione.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

TICKER = "^GSPC"
INIZIO_DOWNLOAD = "1927-01-01"
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "gspc_giornaliero.csv"
FILE_METADATI = DATI / "gspc_metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere dell'indice S&P 500"
URL_FONTE = "https://finance.yahoo.com/quote/%5EGSPC/history/"
NOTA_COLONNA = "Si usano solo le chiusure; i dividendi non sono considerati"
NOMI_ESENTI = ("S&P 500",)

MEDIA = 200
GIORNI_ANNO = 252
COSTO = 0.001                        # 0,1% per ogni cambio di posizione
H2_RAPPORTO_DD = 0.5                 # 2) il drawdown massimo della regola è al massimo metà di quello del buy & hold
H4_ORDINI_ANNO = 5.0                 # 4) più di 5 operazioni all'anno in media
DECENNI = (1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020)

IPOTESI = (
    "1) Il rendimento annuo composto della regola è inferiore a quello del buy & hold (indice di prezzo, liquidità a rendimento zero). "
    "2) Il drawdown massimo della regola è al massimo la metà di quello del buy & hold. "
    "3) (Già nota dall'articolo 82) Lo Sharpe della regola è più alto di quello del buy & hold. "
    "4) La regola fa in media più di 5 operazioni (cambi di posizione) all'anno. "
    "5) La regola batte il buy & hold per rendimento annuo composto in meno della metà dei decenni. "
    "6) Con un costo dello 0,1% a ogni cambio di posizione lo Sharpe della regola resta più alto di quello del buy & hold."
)
