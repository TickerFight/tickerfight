"""Parametri dell'articolo n. 578 - "Quante operazioni all'anno si possono permettere 1.000 euro?" (rubrica «trading con poco capitale»).

Tutti i parametri dell'analisi stanno qui, scritti PRIMA di guardare qualunque risultato.

Che cosa si misura. Non si valuta una regola che prevede i prezzi, ma il solo peso della frequenza. La «regola a cicli» è
un'agenda di posizione stabilita in anticipo, senza alcun segnale di mercato: si è investiti tutte le sedute tranne una ogni
L sedute. Alla chiusura della seduta fuori si vende, alla chiusura della seduta successiva si ricompra. Ogni ciclo costa quindi
due ordini (una vendita e un acquisto) e si resta fuori dal mercato una seduta su L. Cambiando L cambia solo la frequenza degli
ordini: le previsioni sono assenti per costruzione, e ciò che separa la regola dal buy & hold è il costo di operare (più la
tassa pagata ogni volta che si realizza una plusvalenza). Il confronto con le scimmie dice se la scelta del giorno in cui si
sta fuori conta (stesso numero di periodi investiti e stessa durata totale, piazzati a caso).
Ordini e segnale: nessun look-ahead (l'agenda dipende solo dal numero della seduta); ordini eseguiti alla chiusura.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# Strumenti scelti a priori (gli stessi delle puntate precedenti della rubrica, per poter confrontare i numeri).
STRUMENTI = [
    ("SWDA.MI", "ETF azionario mondiale (MSCI World, in euro)", "EUR"),
    ("CSSPX.MI", "ETF sull'S&P 500 (in euro)", "EUR"),
    ("^GSPC", "indice S&P 500 (in dollari, convertito in euro)", "USD"),
]
TICKER_CAMBIO = "EURUSD=X"
INIZIO_DOWNLOAD = "1995-01-01"
STORIA_MINIMA_ANNI = 8
NOMI_ESENTI = ("S&P 500", "MSCI World", "EUR/USD", "buy & hold")
FUSO_BORSA = "Europe/Rome"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere di due ETF quotati a Milano, dell'indice S&P 500 e del cambio euro-dollaro"
URL_FONTE = "https://finance.yahoo.com/"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_").replace("=", "_") + ".csv")


def slug(ticker: str) -> str:
    return ticker.replace("^", "").replace(".", "_").replace("=", "_").lower()


# --- Condizioni della rubrica ---------------------------------------------------------------------------------------
CAPITALE = 1000.0
SCENARI_COSTO = [("0 euro", 0.0, 0.0), ("2 euro", 2.0, 0.0), ("0,1%", 0.0, 0.001)]
SCENARIO_PRINCIPALE = 1       # «2 euro»
ALIQUOTA = 0.26
MODO = "chiusura"

# --- La regola a cicli ------------------------------------------------------------------------------------------------
# Lunghezza del ciclo in sedute: L-1 sedute investite e 1 fuori. Circa 252 sedute l'anno.
CICLI = (252, 126, 63, 21, 10, 5)
SEDUTE_ANNO = 252
SOGLIA_SOSTENIBILE = 0.005    # perdita massima di rendimento annuo netto rispetto al buy & hold (scenario 2 euro): 0,5 punti
ORDINI_TABELLA = (2, 12, 52, 104, 250)   # tabella teorica: ordini all'anno e costo in quota del capitale (nessun dato di mercato)

# --- Test statistici -------------------------------------------------------------------------------------------------
SEME = 20261027
N_SCIMMIE = 2000
LIVELLO_CONFIDENZA = 0.95
# Prove dichiarate: 3 strumenti x (buy & hold + 6 frequenze) x 4 scenari (lordo + 3 di costo) = 84 simulazioni.
# Test di ipotesi: le scimmie, 3 strumenti x 6 frequenze = 18 test (scenario 2 euro), corretti con Holm.

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------------------------------
IPOTESI = (
    "1) Con 2 euro a ordine, a un ciclo ogni 10 sedute (circa 50 ordini l'anno) il rendimento annuo netto è negativo in tutti "
    "gli strumenti. "
    "2) Con un solo ciclo l'anno (2 ordini) la perdita di rendimento annuo netto rispetto al buy & hold con 2 euro a ordine è "
    "sotto la soglia di 0,5 punti percentuali in tutti gli strumenti (soglia di sostenibilità scritta prima). "
    "3) Il numero massimo di ordini all'anno sostenibile (perdita sotto 0,5 punti, 2 euro a ordine) tra le frequenze provate "
    "è inferiore a 10 in tutti gli strumenti. "
    "4) Anche con commissione zero, la sola tassa del 26% pagata a ogni plusvalenza realizzata fa rendere meno la frequenza più "
    "alta (un ciclo ogni 5 sedute) del buy & hold, in tutti gli strumenti. "
    "5) Con 1.000 euro la commissione dello 0,1% pesa meno di quella da 2 euro (a 1.000 euro 2 euro valgono lo 0,2%): la perdita "
    "di rendimento annuo con 0,1% è inferiore a quella con 2 euro alle frequenze di almeno un ciclo al mese, in tutti gli strumenti. "
    "6) Dopo la correzione di Holm sui 18 test, nessuna frequenza batte le scimmie: scegliere il giorno in cui stare fuori "
    "non aggiunge né toglie nulla."
)
