"""Parametri dell'articolo n. 81 - "Quanti anni di dati servono per fidarsi?".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Due parti. (A) Dati veri: il rapporto di Sharpe dell'S&P 500 (indice di prezzo, tasso privo di rischio zero, rendimenti giornalieri) misurato su tutte le
finestre di N anni che partono da ogni mese dal 1927, per N = 1, 2, 3, 5, 10, 20 e 30: quanto cambia, e quante volte ha il segno sbagliato?
(B) Simulazione: una strategia che per costruzione ha uno Sharpe vero di SHARPE_VERO, con rendimenti giornalieri normali e indipendenti: quanto spesso
un backtest di N anni la fa sembrare priva di vantaggio, e quanti anni servono per accorgersi, con potenza dell'80%, che il vantaggio c'è.
Nella simulazione la media e la deviazione standard del campione si estraggono direttamente dalle loro distribuzioni esatte (normale e chi quadro),
senza generare i singoli rendimenti: il risultato è identico e molto più veloce.
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

GIORNI_ANNO = 252
ORIZZONTI = (1, 2, 3, 5, 10, 20, 30)          # anni delle finestre
SHARPE_VERO = 0.5                              # parte B: Sharpe annuo vero della strategia simulata
ANNI_SIM = tuple(range(1, 61))                 # anni provati nella simulazione
SIM_N = 20000                                  # backtest simulati per ogni durata
Z_BILATERALE = 1.959964                        # soglia del test al 95% a due code
POTENZA = 0.80
SEME = 20261029

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_QUOTA = 0.20                  # ipotesi 1: su un anno lo Sharpe è negativo in oltre il 20% delle finestre
H2_QUOTA = 0.90                  # ipotesi 2: su dieci anni lo Sharpe è positivo in almeno il 90% delle finestre
H3_RIDUZIONE = 0.40              # ipotesi 3: l'ampiezza 5-95 percentile dello Sharpe scende di almeno il 40% da cinque a venti anni
H4_SHARPE = 0.25                 # ipotesi 4: su venti anni la finestra peggiore ha comunque uno Sharpe sotto questo valore
H5_QUOTA = 0.10                  # ipotesi 5: con Sharpe vero 0,5, un backtest di cinque anni mostra Sharpe negativo con probabilità sopra il 10%
H6_ANNI = 25                     # ipotesi 6: per riconoscere uno Sharpe vero di 0,5 con potenza dell'80% servono più di 25 anni

IPOTESI = (
    "1) Sull'S&P 500, su finestre di un anno, lo Sharpe è negativo in oltre il 20% delle finestre. "
    "2) Su finestre di dieci anni lo Sharpe è positivo in almeno il 90% delle finestre. "
    "3) L'ampiezza dell'intervallo tra il 5° e il 95° percentile dello Sharpe scende di almeno il 40% passando da finestre di cinque a finestre di venti anni. "
    "4) Anche su finestre di venti anni la finestra peggiore ha uno Sharpe sotto 0,25: un solo ventennio basta a dare un verdetto pessimo. "
    "5) Una strategia con Sharpe vero 0,5 mostra, in un backtest di cinque anni, uno Sharpe negativo con probabilità superiore al 10%. "
    "6) Per accorgersi con potenza dell'80% (test al 95%, due code) che quella strategia ha uno Sharpe diverso da zero servono più di 25 anni di dati."
)
