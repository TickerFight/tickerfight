"""Parametri dell'articolo n. 13 - "La data di partenza cambia il verdetto".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Regola: filtro di tendenza a 200 sedute sull'S&P 500 (indice di prezzo, senza dividendi). Si è investiti se la chiusura sta sopra la media
mobile semplice delle ultime 200 chiusure, altrimenti si sta in liquidità (rendimento zero). Il segnale si osserva a una chiusura e si
esegue alla chiusura SUCCESSIVA (nessun look-ahead); ogni cambio di posizione costa COSTO_BP punti base. Confronto: buy & hold sullo stesso indice.
La domanda non è se la regola funzioni, ma quanto il verdetto dipenda dalla data di partenza: si misura su ogni mese di partenza dal 1928,
con finestre di 5, 10 e 20 anni. Il segnale usa la storia precedente alla partenza, come farebbe chi avvia la regola in quel momento.
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

# --- La regola ------------------------------------------------------------------------------------------------
MEDIA = 200                      # sedute della media mobile
COSTO_BP = 10                    # punti base per ogni cambio di posizione
GIORNI_ANNO = 252
ORIZZONTI = (5, 10, 20)          # anni delle finestre
ORIZZONTE_PRINCIPALE = 10
ANNO_FAVOREVOLE = 2000           # decennio che parte a gennaio di quest'anno (caso 1)
ANNO_SFAVOREVOLE = 1990          # decennio che parte a gennaio di quest'anno (caso 2)

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_MIN, H1_MAX = 0.20, 0.80      # ipotesi 1: sul rendimento annuo la regola vince in una quota di partenze tra il 20% e l'80% (verdetto instabile)
H2_QUOTA = 0.90                  # ipotesi 2: sulla perdita massima la regola fa meglio in almeno il 90% delle partenze
H3_VANTAGGIO = 0.05              # ipotesi 3: nel decennio del 2000 la regola batte il buy & hold di almeno 5 punti all'anno...
H3_SVANTAGGIO = 0.03             # ... e in quello del 1990 perde di almeno 3 punti all'anno
H5_AMPIEZZA = 0.10               # ipotesi 5: tra la partenza migliore e la peggiore la differenza di rendimento annuo supera 10 punti
SEME = 20261029

IPOTESI = (
    "1) Su finestre di dieci anni, su ogni mese di partenza dal 1928, la regola batte il buy & hold sul rendimento annuo composto in una "
    "quota di partenze compresa tra il 20% e l'80%: il verdetto dipende dalla data. "
    "2) Sulla perdita massima la regola fa meglio del buy & hold in almeno il 90% delle partenze. "
    "3) Il decennio che parte a gennaio 2000 vede la regola battere il buy & hold di almeno 5 punti all'anno, e quello che parte a gennaio 1990 la vede perdere di almeno 3 punti all'anno. "
    "4) Sull'insieme delle partenze, il rendimento annuo medio della regola è più basso di quello del buy & hold. "
    "5) Tra la data di partenza che più favorisce la regola e quella che più la sfavorisce, la differenza di rendimento annuo rispetto al buy & hold supera 10 punti percentuali. "
    "6) Allungando la finestra da dieci a venti anni la quota di partenze in cui la regola batte il buy & hold sul rendimento diminuisce."
)
