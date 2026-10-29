"""Parametri dell'articolo n. 326 - "Perdere i 10 giorni migliori".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Si prendono i rendimenti giornalieri dell'S&P 500 (indice di prezzo, senza dividendi) e si chiede: che cosa succede al rendimento annuo composto se si
resta fuori dal mercato nei giorni migliori (rendimento zero in quei giorni, come se si fosse in liquidità senza interessi), nei giorni peggiori o in
entrambi? E quanto vale lo stesso esercizio su finestre di 10 e 20 anni, invece che sull'intera storia?
Poi: i giorni migliori sono sparsi a caso o vengono dopo i peggiori? E un filtro a 200 sedute, che sta fuori quando l'indice chiude sotto la sua
media, salta i giorni migliori? Il regime di ogni giorno usa solo la chiusura del giorno prima (nessuna informazione dal futuro).
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
N_GIORNI = (5, 10, 20, 30, 40)                 # quanti giorni migliori/peggiori saltare (nella tabella)
N_BASE = 10                                    # il caso di cui parla il titolo
FINESTRE_ANNI = (10, 20)                       # finestre mobili, una per mese di partenza
SMA_GIORNI = 200                               # media mobile del filtro (segnale ritardato di una seduta)
VICINANZA = 30                                 # "vicino": entro 30 sedute da uno dei 10 peggiori giorni
CASUALI_N = 10000                              # estrazioni del controllo "10 giorni a caso"
SEME = 20261030

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_PUNTI = 0.010                 # ipotesi 1: saltare i 10 giorni migliori costa almeno 1,0 punti all'anno sull'intera storia
H2_PUNTI = 0.020                 # ipotesi 2: su finestre di 20 anni, la perdita mediana è di almeno 2,0 punti all'anno
H3_QUOTA = 0.50                  # ipotesi 3: almeno la metà dei 10 giorni migliori viene con l'indice sotto la media a 200 sedute
H5_VICINI = 7                    # ipotesi 5: almeno 7 dei 10 giorni migliori cadono entro 30 sedute da uno dei 10 peggiori

IPOTESI = (
    "1) Sull'intera storia dell'S&P 500, saltare i 10 giorni migliori costa almeno 1,0 punti di rendimento annuo composto. "
    "2) Su finestre mobili di 20 anni, saltare i 10 giorni migliori della finestra costa in mediana almeno 2,0 punti all'anno. "
    "3) Almeno metà dei 10 giorni migliori cade quando l'indice, alla chiusura precedente, era sotto la sua media a 200 sedute. "
    "4) Saltare i 10 giorni peggiori fa guadagnare più punti di quanti ne faccia perdere saltare i 10 migliori. "
    "5) Almeno 7 dei 10 giorni migliori cadono entro 30 sedute da uno dei 10 peggiori. "
    "6) Il filtro a 200 sedute chiude la storia con un rendimento annuo composto inferiore al buy & hold."
)
