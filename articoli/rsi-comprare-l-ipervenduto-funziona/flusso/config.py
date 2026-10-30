"""Parametri dell'articolo n. 146 - "RSI: comprare l'ipervenduto funziona?".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

L'RSI (indice di forza relativa, Wilder) a 14 sedute è il segnale di inversione più popolare: sotto 30 il mercato sarebbe «ipervenduto» e conviene comprare, sopra 70
«ipercomprato». Si prova sull'S&P 500 (indice di prezzo, dal 1927, senza dividendi) in due modi. (a) Studio degli eventi: rendimento nelle dieci sedute successive al
giorno in cui l'RSI scende sotto 30 (o sale sopra 70) per la prima volta, confrontato con il rendimento a dieci sedute di un giorno qualunque. (b) Regola: si compra
quando l'RSI chiude sotto 30 e si esce quando chiude sopra 50, con la posizione che parte dalla seduta successiva al segnale; si confronta con il buy & hold e con la stessa
posizione fatta ruotare a caso nel tempo (spostamenti circolari: stessa quota investita, stessa durata dei periodi, momenti scelti a caso). Niente costi.
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
NOMI_ESENTI = ("S&P 500", "RSI", "Wilder")

GIORNI_ANNO = 252
RSI_N = 14                           # periodo dell'RSI
SOGLIA_BASSA = 30.0                  # sotto: ipervenduto
SOGLIA_ALTA = 70.0                   # sopra: ipercomprato
SOGLIA_USCITA = 50.0                 # la regola esce quando l'RSI chiude sopra questo valore
ORIZZONTE = 10                       # sedute dell'orizzonte dello studio degli eventi
SPARTIACQUE = "1990-01-01"           # divide il campione in due metà per la stabilità
N_SPOSTAMENTI = 2000                 # spostamenti circolari della posizione
SEME = 20261030

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H3_ECCESSO = 0.005                   # 3) rendimento a 10 sedute dopo RSI<30 superiore a quello di un giorno qualunque di almeno 0,5 punti
H5_PVAL = 0.05                       # 5) p-value dello spostamento circolare sotto 0,05
H6_TOLLERANZA = 0.0025               # 6) dopo RSI>70 il rendimento a 10 sedute non è inferiore alla media di più di 0,25 punti

IPOTESI = (
    "1) Lo Sharpe della regola (compra con RSI sotto 30, esce sopra 50) è inferiore a quello del buy & hold. "
    "2) Il rendimento annuo composto della regola è inferiore a quello del buy & hold: sta investita solo una parte del tempo. "
    "3) Nelle dieci sedute dopo la prima chiusura con RSI sotto 30 il rendimento medio supera di almeno 0,5 punti percentuali quello medio di dieci sedute di un giorno qualunque. "
    "4) Quel vantaggio è più piccolo dal 1990 in poi che prima del 1990. "
    "5) Lo Sharpe della regola è migliore di quello della stessa posizione spostata a caso nel tempo, con p-value sotto 0,05: il momento scelto dall'RSI conta. "
    "6) Dopo la prima chiusura con RSI sopra 70 il rendimento medio a dieci sedute non è inferiore a quello di un giorno qualunque di più di 0,25 punti: l'ipercomprato non è un segnale di vendita."
)
