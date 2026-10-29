"""Parametri dell'articolo n. 243 - "VIX sopra 30: comprare la paura?".

Tutti i parametri dell'analisi stanno qui, scritti prima di guardare i risultati.

Domanda: dopo che il VIX chiude sopra 30, l'S&P 500 rende di più del solito nei mesi successivi? Si può «comprare la paura»?

Evento: un episodio comincia nella prima seduta in cui il VIX chiude sopra la soglia dopo almeno QUIETE sedute consecutive con il VIX
uguale o sotto la soglia (così gli episodi sono separati e non si sovrappongono). Si compra alla chiusura della seduta SUCCESSIVA a
quella in cui il VIX chiude sopra la soglia (il segnale non può essere scambiato nella stessa chiusura: nessun look-ahead) e si guarda
il rendimento dell'S&P 500 (indice di prezzo, senza dividendi) a 21, 63, 126 e 252 sedute. Confronti: tutte le sedute qualunque (rendimento
«generico») e le scimmie, cioè lo stesso numero di date di acquisto scelte a caso.
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
NOMI_ESENTI = ("S&P 500", "VIX")


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Parametri (fissati prima di guardare i dati) --------------------------------------------
GIORNI_ANNO = 252
SOGLIA_BASE = 30.0
QUIETE = 63                  # sedute consecutive sotto la soglia prima che un nuovo episodio possa cominciare (circa tre mesi)
ORIZZONTI = (21, 63, 126, 252)
ORIZZONTE_MIN = 63           # per l'ipotesi sul minimo successivo: finestra di sedute dopo l'acquisto
GRIGLIA_SOGLIE = (25.0, 30.0, 35.0, 40.0)    # robustezza: si riportano tutte
EPISODI_MIN_GRIGLIA = 5      # una soglia con meno episodi non si valuta
H3_QUOTA = 0.50              # ipotesi 3: in più della metà degli episodi l'indice scende ancora sotto il prezzo d'acquisto
H4_QUOTA = 0.80              # ipotesi 4: quota di episodi con rendimento a un anno positivo sopra l'80%
H6_EPISODI = 20              # ipotesi 6: meno di venti episodi indipendenti

# --- Test statistici ----------------------------------------------------------------------
SEME = 20261029
N_SCIMMIE = 10000
LIVELLO_CONFIDENZA = 0.95
SOGLIA = 0.05
SOGLIA_FORTE = 0.01

IPOTESI = (
    "1) Dopo un episodio con il VIX sopra 30 il rendimento medio dell'S&P 500 a un anno (252 sedute) è più alto del rendimento medio a un "
    "anno su una seduta qualunque. "
    "2) A un mese (21 sedute) la differenza non si distingue dal caso: il rendimento medio degli episodi cade dentro l'intervallo al 95% "
    "ottenuto dalle scimmie (stesso numero di acquisti, date a caso). "
    "3) Comprare non è comodo: in più della metà degli episodi l'indice scende ancora, cioè nelle 63 sedute successive l'acquisto tocca "
    "almeno una chiusura sotto il prezzo pagato. "
    "4) A un anno più dell'80% degli episodi chiude in positivo. "
    "5) Il risultato non dipende dalla soglia: con 25, 30, 35 e 40 (se ci sono almeno cinque episodi) il rendimento medio a un anno è "
    "sempre più alto di quello generico. "
    "6) Gli episodi indipendenti sono meno di venti, e a un anno il rendimento medio degli episodi non si distingue dalle scimmie al "
    "livello severo dell'1%: p-value sopra 0,01."
)
