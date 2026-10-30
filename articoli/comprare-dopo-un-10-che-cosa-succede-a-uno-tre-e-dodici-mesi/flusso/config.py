"""Parametri dell'articolo n. 151 - "Comprare dopo un -10%".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

«Quando il mercato crolla del dieci per cento, compra». Sull'S&P 500 (indice di prezzo, dal 1927, senza dividendi) un «calo rapido» è il giorno in cui la chiusura è almeno il
10% sotto il massimo delle 20 chiusure precedenti. Per rendere gli eventi quasi indipendenti, dopo un evento se ne ignorano altri per un anno di borsa (252 sedute). Si misura
il rendimento a 1, 3 e 12 mesi (21, 63 e 252 sedute) dalla chiusura dell'evento e lo si confronta con quello di un giorno qualunque. Si guarda anche quanto l'indice scende ancora
dopo l'evento, e se i risultati dipendono dagli anni della Grande Depressione.
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

FINESTRA = 20                        # sedute per il massimo di riferimento
SOGLIA_CALO = 0.10                   # calo minimo dal massimo
PAUSA = 252                          # sedute di pausa dopo un evento
ORIZZONTI = (21, 63, 252)            # 1, 3 e 12 mesi
ANNO_ESCLUSO_FINO = 1939             # 5) si tolgono gli eventi fino a questo anno compreso (Grande Depressione)
N_CASUALI = 10000
SEME = 20261030
H1_ECCESSO = 0.02                    # 1) a 12 mesi l'eccesso è di almeno 2 punti
H3_QUOTA = 1.0 / 3.0                 # 3) a 3 mesi almeno un terzo degli eventi ha rendimento negativo
H4_CALO = 0.05                       # 4) un ulteriore calo di almeno il 5% nei 63 giorni dopo l'evento
H4_QUOTA = 0.50                      # ... in oltre la metà degli eventi
SOGLIA_P = 0.05

IPOTESI = (
    "1) Dodici mesi dopo un calo rapido del 10% il rendimento medio supera di almeno 2 punti percentuali quello medio di dodici mesi di un giorno qualunque. "
    "2) A un mese dall'evento il rendimento medio è inferiore a quello medio a un mese di un giorno qualunque: il calo, nel breve, continua. "
    "3) A tre mesi dall'evento almeno un terzo degli eventi ha un rendimento negativo. "
    "4) In oltre la metà degli eventi l'indice scende di almeno un ulteriore 5% rispetto alla chiusura dell'evento nei tre mesi successivi. "
    "5) Togliendo gli eventi fino al 1939, il rendimento medio a dodici mesi continua a superare quello di un giorno qualunque. "
    "6) Il rendimento medio a dodici mesi dopo l'evento è significativamente più alto di quello di altrettanti giorni scelti a caso: il p-value (estrazioni casuali) è sotto 0,05."
)
