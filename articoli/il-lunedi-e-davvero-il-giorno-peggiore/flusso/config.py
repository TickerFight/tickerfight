"""Parametri dell'articolo n. 506 - "Il lunedì è davvero il giorno peggiore?".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Rendimento giornaliero (chiusura su chiusura, indice di prezzo, senza dividendi) dell'S&P 500 per giorno della settimana. Il giorno della settimana è quello
della seduta cui il rendimento si riferisce: il rendimento del lunedì va dalla chiusura del venerdì (o dell'ultimo giorno di Borsa aperta) a quella del lunedì.
Se il lunedì è festivo, il rendimento che copre il fine settimana cade di martedì e conta come martedì. Fino al settembre del 1952 la Borsa americana teneva
sedute anche il sabato: si parte quindi dal 1953, quando le sedute sono solo da lunedì a venerdì. Il test di significatività è di permutazione: si mescolano le
etichette dei giorni tra i rendimenti e si guarda quanto spesso la differenza tra il giorno migliore e il peggiore è grande come quella vera.
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
INIZIO_ANALISI = "1953-01-01"                  # dalla fine delle sedute del sabato
PERIODO_1 = (1953, 1989)
PERIODO_2 = (1990, 2026)
N_PERMUTAZIONI = 20000
TOP_PEGGIORI = 10                              # giorni peggiori tolti nel test di robustezza
COSTO = 0.0005                                 # costo di ogni operazione (0,05%) nella variante con costi
SEME = 20261031
NOMI_GIORNI = ("lunedì", "martedì", "mercoledì", "giovedì", "venerdì")

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H3_P = 0.05                      # ipotesi 3: p-value del test di permutazione sotto il 5%
H6_COSTO = 0.0002                # ipotesi 6: il costo di pareggio è inferiore allo 0,02% per operazione

IPOTESI = (
    "1) Dal 1953 a oggi il lunedì ha il rendimento medio giornaliero più basso dei cinque giorni della settimana. "
    "2) Dal 1990 a oggi il lunedì non è più il giorno peggiore della settimana. "
    "3) La differenza tra il giorno migliore e il peggiore è statisticamente significativa: p-value del test di permutazione sotto il 5%. "
    "4) Togliendo i 10 giorni peggiori dell'intero periodo, il lunedì non è più il giorno con la media più bassa. "
    "5) Stare in liquidità ogni lunedì, senza costi, rende più del buy & hold. "
    "6) Il costo per operazione che azzera quel vantaggio è inferiore allo 0,02%."
)
