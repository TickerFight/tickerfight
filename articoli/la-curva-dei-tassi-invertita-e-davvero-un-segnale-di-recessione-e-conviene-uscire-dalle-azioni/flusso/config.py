"""Parametri dell'articolo n. 341 - "La curva dei tassi invertita".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Idea: la curva dei tassi americana è «invertita» quando il rendimento a 10 anni (^TNX) scende sotto quello a 3 mesi (^IRX). Si misura
(1) se le recessioni dichiarate dal NBER sono state precedute da un'inversione, (2) quante inversioni non hanno poi portato a una
recessione, (3) con quanto anticipo, (4) che cosa succede a chi esce dall'S&P 500 (^GSPC) quando la curva è invertita, (5) se il
risultato batte il caso (stessa quantità di mesi in liquidità, ma in momenti scelti a caso).
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

TICKER_AZIONI = "^GSPC"
TICKER_10A = "^TNX"
TICKER_3M = "^IRX"
INIZIO_DOWNLOAD = "1960-01-01"
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "serie_giornaliere.csv"
FILE_METADATI = DATI / "serie_metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere dell'S&P 500 e i rendimenti dei titoli di Stato americani a 10 anni e a 3 mesi"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = "Si usano solo le chiusure; i dividendi non sono considerati"
NOMI_ESENTI = ("NBER",)
SEDUTE_ANNO = 252

# --- Recessioni americane dichiarate dal NBER (mese del picco e mese del minimo) ---------------------------------
# Fonte: National Bureau of Economic Research, Business Cycle Dating Committee, https://www.nber.org/cycles/cyclesmain.html
RECESSIONI = (
    ("1969-12", "1970-11"),
    ("1973-11", "1975-03"),
    ("1980-01", "1980-07"),
    ("1981-07", "1982-11"),
    ("1990-07", "1991-03"),
    ("2001-03", "2001-11"),
    ("2007-12", "2009-06"),
    ("2020-02", "2020-04"),
)

# --- Definizioni (fissate prima dei risultati) --------------------------------------------------------------------
SPREAD_SOGLIA = 0.0               # curva invertita quando (10 anni - 3 mesi) è sotto zero, in punti percentuali
MIN_MESI_EPISODIO = 3             # un episodio è una serie di almeno 3 fine-mese consecutivi con curva invertita
GAP_UNIONE = 6                    # due serie separate da meno di 6 mesi con curva normale sono un unico episodio
ORIZZONTE = 24                    # mesi: una recessione «segue» l'inversione se inizia entro 24 mesi dall'inizio dell'episodio
H1_MIN_RECESSIONI = 7             # ipotesi 1: almeno 7 recessioni su 8 precedute da un'inversione
H2_QUOTA_MIN = 0.60               # ipotesi 2: quota minima di episodi seguiti da recessione
H3_MEDIANA_MIN, H3_MEDIANA_MAX = 6, 18   # ipotesi 3: anticipo mediano (mesi)
H3_AMPIEZZA_MIN = 12              # ipotesi 3: differenza tra anticipo massimo e minimo (mesi)
SOGLIA_P = 0.05                   # ipotesi 5
N_SPOSTAMENTI = 2000              # strategie «a caso»: lo stesso segnale spostato circolarmente nel tempo
SPOSTAMENTO_MIN = 24              # mesi: spostamenti più piccoli di 2 anni sono esclusi (sarebbero troppo simili al segnale vero)
SEME = 20261025

# --- Ipotesi, scritte PRIMA di guardare i risultati ----------------------------------------------------------------
IPOTESI = (
    "1) Almeno 7 delle 8 recessioni dichiarate dal NBER dal 1969 in poi sono state precedute da una curva invertita (10 anni sotto 3 mesi) "
    "in almeno un fine-mese dei 24 mesi prima dell'inizio. "
    "2) L'inversione non è infallibile ma di solito ha ragione: almeno il 60% degli episodi di inversione (giudicabili) è seguito da una recessione entro 24 mesi. "
    "3) Il segnale dà un orizzonte, non una data: l'anticipo mediano tra inizio dell'inversione e inizio della recessione sta tra 6 e 18 mesi, "
    "ma tra l'anticipo massimo e quello minimo ci sono almeno 12 mesi di differenza. "
    "4) Uscire dall'S&P 500 quando la curva è invertita riduce il drawdown massimo ma rende meno del buy & hold (le azioni continuano a salire per mesi dopo l'inversione). "
    "5) Il risultato della strategia non è distinguibile dal caso: tra 2.000 strategie con lo stesso segnale spostato nel tempo, "
    "la quota che rende almeno quanto quella vera supera il 5%."
)
