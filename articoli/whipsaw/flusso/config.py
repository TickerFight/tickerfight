"""Parametri dell'articolo n. 134 - "Whipsaw".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Filtro di trend sull'S&P 500 (indice di prezzo): in mercato quando la chiusura è sopra la media delle ultime SMA_GIORNI chiusure, in liquidità senza
interessi quando è sotto. Il segnale alla chiusura del giorno t decide la posizione del giorno t+1 (nessuna informazione dal futuro). Un «whipsaw» è
un'uscita seguita da un rientro a un prezzo uguale o più alto di quello di uscita: si è venduto e ricomprato più caro. Si misura quante volte succede,
quanto dura ogni uscita, quanto pesano i casi buoni e quelli cattivi, e quanto costa se ogni cambio di posizione ha un costo. Si prova anche una banda
attorno alla media (esce sotto la media meno la banda, rientra sopra la media più la banda).
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
SMA_GIORNI = 200
BANDA = 0.02                                   # banda attorno alla media (2%)
COSTO = 0.001                                  # costo di ogni cambio di posizione (0,10%)
DURATA_BREVE = 20                              # un'uscita è «breve» se dura al massimo 20 sedute
TOP_N = 10                                     # quante uscite migliori contano nell'ipotesi 3
PERIODO_A = (1966, 1981)                       # anni di mercato laterale (ipotesi 5)
PERIODO_B = (1982, 1999)                       # anni di mercato in forte salita (ipotesi 5)
DECENNI = (1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020)
ESEMPIO = ("2018-01-01", "2020-12-31")         # tratto mostrato nel grafico dei segnali

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_QUOTA = 0.50                  # ipotesi 1: almeno metà delle uscite dura al massimo 20 sedute
H2_QUOTA = 0.50                  # ipotesi 2: almeno metà delle uscite si chiude con un rientro a prezzo uguale o più alto
H3_QUOTA = 0.50                  # ipotesi 3: le 10 uscite migliori valgono almeno metà della somma di tutti i guadagni delle uscite in guadagno
H5_RAPPORTO = 1.5                # ipotesi 5: cambi all'anno nel periodo A almeno 1,5 volte quelli del periodo B
H6_RIDUZIONE = 0.40              # ipotesi 6: la banda riduce i cambi di almeno il 40%

IPOTESI = (
    "1) Almeno metà delle uscite dal mercato dura al massimo 20 sedute. "
    "2) Almeno metà delle uscite si chiude con un rientro a un prezzo uguale o più alto di quello di uscita (whipsaw). "
    "3) Le 10 uscite migliori valgono almeno metà della somma dei guadagni di tutte le uscite in guadagno. "
    "4) Anche dopo un costo dello 0,10% a ogni cambio di posizione, il filtro rende più del buy & hold. "
    "5) Nel periodo laterale 1966-1981 i cambi di posizione all'anno sono almeno 1,5 volte quelli del periodo 1982-1999. "
    "6) Una banda del 2% attorno alla media riduce i cambi di posizione di almeno il 40%."
)
