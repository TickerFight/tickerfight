"""Parametri dell'articolo n. 482 - "Gli ETF a ribasso limitato (buffer ETF)".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Idea: i buffer ETF di Innovator (serie «U.S. Equity Buffer» sull'S&P 500, un fondo per ogni mese di partenza) promettono di assorbire
i primi ribassi dell'indice in cambio di un tetto ai rialzi, ma solo se si tiene il fondo per l'intero periodo di 12 mesi. Per ogni fondo
e per ogni anno si misura il rendimento sull'intero periodo (dal primo giorno di borsa del mese di partenza al primo giorno di borsa dello
stesso mese dell'anno dopo) e lo si confronta con quello dell'S&P 500 total return (SPY, dividendi reinvestiti) nelle stesse date e con
un portafoglio semplice 80% SPY e 20% liquidità (tasso a 3 mesi, ^IRX).
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

TICKER_INDICE = "SPY"
TICKER_3M = "^IRX"
# Un fondo per ogni mese di partenza del periodo di 12 mesi (numero del mese di partenza)
FONDI = {"PJAN": 1, "PFEB": 2, "PMAR": 3, "PAPR": 4, "PMAY": 5, "PJUN": 6,
         "PJUL": 7, "PAUG": 8, "PSEP": 9, "POCT": 10, "PNOV": 11, "PDEC": 12}
INIZIO_DOWNLOAD = "2018-01-01"
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "serie_giornaliere.csv"
FILE_METADATI = DATI / "serie_metadati.json"
DESCRIZIONE_DATI = "i prezzi giornalieri dei dodici buffer ETF di Innovator, di SPY (S&P 500 total return) e il tasso a 3 mesi"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = "Prezzi di mercato aggiustati; nessuna tassa, nessuna commissione di negoziazione"
NOMI_ESENTI = ("ETF", "SPY", "IRX", "PJAN", "PFEB", "PMAR", "PAPR", "PMAY", "PJUN", "PJUL", "PAUG", "PSEP", "POCT", "PNOV", "PDEC")
MESI_ANNO = 12

# --- Definizioni (fissate prima dei risultati) --------------------------------------------------------------------
MESI_PERIODO = 12                 # lunghezza del periodo di un buffer ETF
QUOTA_AZIONI_MIX = 0.80           # portafoglio semplice di confronto: 80% SPY, 20% liquidità
SOGLIA_FORTE = 0.15               # un periodo è «di forte rialzo» se l'S&P 500 TR rende più del 15%
SEME = 20261026

# --- Soglie delle ipotesi ------------------------------------------------------------------------------------------
H1_QUOTA_MIN = 0.90               # ipotesi 1: nei periodi di ribasso il fondo perde meno dell'indice in almeno il 90% dei casi
H2_RIDUZIONE_MIN = 0.05           # ipotesi 2: la perdita media si riduce di almeno 5 punti percentuali
H3_QUOTA_MIN = 0.90               # ipotesi 3: nei periodi di forte rialzo il fondo rende meno dell'indice in almeno il 90% dei casi
H5_QUOTA_MIN = 0.50               # ipotesi 5: il fondo batte il portafoglio 80/20 in meno della metà dei periodi

# --- Ipotesi, scritte PRIMA di guardare i risultati ----------------------------------------------------------------
IPOTESI = (
    "1) Nei periodi di 12 mesi in cui l'S&P 500 total return perde, il buffer ETF perde meno dell'indice in almeno il 90% dei casi. "
    "2) In quei periodi la perdita si riduce in media di almeno 5 punti percentuali rispetto all'indice. "
    "3) Nei periodi in cui l'S&P 500 total return guadagna più del 15%, il buffer ETF rende meno dell'indice in almeno il 90% dei casi (il tetto ai rialzi si fa sentire). "
    "4) Sull'insieme dei periodi, il rendimento medio dei buffer ETF è più basso di quello dell'indice: la protezione si paga. "
    "5) Un portafoglio semplice, 80% S&P 500 e 20% liquidità, ottiene un rendimento almeno pari a quello del buffer ETF nella metà o più dei periodi: "
    "per ridurre il rischio non serve un derivato."
)
