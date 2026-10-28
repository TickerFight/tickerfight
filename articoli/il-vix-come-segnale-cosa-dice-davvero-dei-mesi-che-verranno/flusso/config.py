"""Parametri dell'articolo n. 242 - "Il VIX come segnale".

Tutti i parametri dell'analisi stanno qui, scritti prima di guardare i risultati.

Domanda: che cosa dice il VIX dei rendimenti e della volatilità del mese successivo, e una regola semplice basata sul
VIX batte il buy & hold sull'S&P 500 e la fortuna?

Segnale: alla chiusura dell'ultima seduta del mese si calcola il percentile del VIX rispetto a TUTTA la sua storia
fino a quel giorno (finestra crescente: nessuna informazione futura). Il segnale della chiusura t viene scambiato alla
chiusura t+1 e lavora sul rendimento della seduta t+2 (segnale di ieri, posizione di oggi), fino al segnale successivo.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------------------------
INDICI = [
    ("^GSPC", "S&P 500", "USD"),
    ("^VIX", "VIX", "punti"),
]
TICKER_INDICE = "^GSPC"
TICKER_VIX = "^VIX"
INIZIO_DOWNLOAD = "1989-01-01"
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere dell'S&P 500 e del VIX"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = "Si usano solo le chiusure; l'S&P 500 è l'indice di prezzo, senza dividendi"
NOMI_ESENTI = ("S&P 500",)


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Parametri (fissati prima di guardare i dati) --------------------------------------------
GIORNI_ANNO = 252
STORIA_MINIMA = 504         # giorni di VIX necessari prima di calcolare il primo percentile (circa due anni)
SOGLIA_A = 0.80             # regola A «prudente»: in azioni se il percentile del VIX è sotto la soglia, altrimenti cassa
SOGLIA_B = 0.50             # regola B «contraria»: in azioni solo se il percentile del VIX è uguale o sopra la soglia
COSTO_BP = 5.0              # punti base per ogni scambio (scenario)
CAPITALE = 500.0
N_QUINTILI = 5

# Varianti di robustezza: si riportano TUTTE
VARIANTI = [
    # (etichetta, regola, soglia)
    ("A con soglia 70%", "A", 0.70),
    ("A con soglia 80% (base)", "A", 0.80),
    ("A con soglia 90%", "A", 0.90),
    ("B con soglia 40%", "B", 0.40),
    ("B con soglia 50% (base)", "B", 0.50),
    ("B con soglia 60%", "B", 0.60),
]

# --- Test statistici ----------------------------------------------------------------------
SEME = 20261028
N_SCIMMIE = 5000
N_BOOTSTRAP = 2000
N_PERMUTAZIONI = 10000
BLOCCO_BOOTSTRAP = 21
LIVELLO_CONFIDENZA = 0.95

CRISI = [
    ("Crisi finanziaria", "2008-09-01", "2009-03-09"),
    ("Crollo del Covid", "2020-02-19", "2020-03-23"),
]

IPOTESI = (
    "1) Più il VIX è alto a fine mese, più è alta la volatilità realizzata del mese successivo: la correlazione di rango "
    "(Spearman) è positiva con p-value sotto 0,01 (test di permutazione). "
    "2) Sul rendimento del mese successivo la relazione con il VIX non è significativa: p-value della correlazione di rango "
    "uguale o sopra 0,05. "
    "3) Il rendimento medio del mese dopo i mesi del quinto quintile del VIX (il più alto) è più alto di quello del primo, "
    "ma l'intervallo di confidenza al 95% della differenza contiene lo zero. "
    "4) Regola A (fuori dalle azioni quando il VIX è alto): perdita massima più piccola del buy & hold, ma Sharpe non più alto "
    "in modo significativo (l'intervallo della differenza contiene lo zero) e le scimmie (stessa quota di mesi in azioni, "
    "mesi a caso) fanno meglio in almeno il cinque per cento dei casi (p-value uguale o sopra 0,05). "
    "5) Regola B (dentro solo quando il VIX è alto): lo Sharpe non è più alto di quello del buy & hold in modo significativo "
    "e le scimmie fanno meglio in almeno il cinque per cento dei casi."
)
