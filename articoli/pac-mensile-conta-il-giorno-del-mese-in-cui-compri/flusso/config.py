"""Parametri dell'articolo n. 421 - "PAC mensile: conta il giorno del mese?".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Piano di accumulo: ogni mese si versa la stessa somma e si comprano quote dell'indice (frazionate) alla chiusura
della prima seduta uguale o successiva al giorno scelto. Si prova ogni giorno del mese da 1 a 28 e si confronta il
valore finale. Confronti: le serie con i rendimenti giornalieri rimescolati (stessa media e stessa volatilità, nessun calendario) e le scimmie, che scelgono il giorno a caso ogni mese.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: indici azionari (ticker Yahoo Finance, nome, valuta) -----------------------------------------------
# Scelti a priori, prima di guardare i dati. Indici di prezzo, nella valuta locale, senza cambio: il confronto è
# sempre fatto dentro lo stesso indice.
INDICI = [
    ("^GSPC", "S&P 500 (Stati Uniti)", "USD"),
    ("^GDAXI", "DAX (Germania)", "EUR"),
    ("^FCHI", "CAC 40 (Francia)", "EUR"),
    ("^STOXX50E", "Euro Stoxx 50", "EUR"),
    ("FTSEMIB.MI", "FTSE MIB (Italia)", "EUR"),
    ("^N225", "Nikkei 225 (Giappone)", "JPY"),
]
INIZIO_DOWNLOAD = "1980-01-01"
NOMI_ESENTI = ("S&P 500", "CAC 40", "Euro Stoxx 50", "Nikkei 225")   # nomi di indici con cifre: non sono dati
FUSO_BORSA = "Europe/Berlin"
MESI_MINIMI = 120            # sotto questa soglia (dieci anni di versamenti) l'indice viene scartato
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure giornaliere di sei indici azionari"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = "Si usano solo le chiusure."


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Il piano di accumulo ----------------------------------------------------------------------------------
VERSAMENTO = 100.0           # somma versata ogni mese, nella valuta dell'indice
COMMISSIONE = 2.0            # per ogni acquisto (uguale per tutti i giorni)
ALIQUOTA = 0.26              # sulla plusvalenza, pagata alla vendita finale di tutto
GIORNI = list(range(1, 29))  # giorno del mese in cui si compra: 1..28 (esiste in ogni mese)
GIORNI_FINE_MESE = (24, 25, 26, 27, 28)
GIORNI_INIZIO_MESE = (1, 2, 3, 4, 5)
SOGLIA_SCARTO = 0.03         # ipotesi 1: scarto tra giorno migliore e peggiore sotto il 3%
TOLLERANZA_GIORNI = 3        # ipotesi 4: giorno migliore "stabile" se prima e dopo differiscono al massimo di tre giorni

# --- Test statistici -------------------------------------------------------------------------------------
SEME = 20261027
N_PERMUTAZIONI = 1000
N_SCIMMIE = 5000

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------------------
IPOTESI = (
    "1) Lo scarto tra il valore finale del giorno migliore e quello del giorno peggiore è sotto il 3% in almeno cinque "
    "indici su sei: scegliere il giorno conta poco in euro. "
    "2) Il giorno migliore di un indice, usato sugli altri indici, non fa meglio della mediana dei giorni in almeno la "
    "metà dei casi: il giorno 'giusto' non si trasferisce. "
    "3) Dopo la correzione di Holm, lo scarto osservato è più grande di quello che si ottiene su serie con gli stessi "
    "rendimenti giornalieri messi in ordine casuale (cioè il calendario conta davvero) in meno della metà degli indici. "
    "4) Il giorno migliore della prima metà della storia e quello della seconda metà differiscono di più di tre giorni "
    "in almeno la metà degli indici: non è stabile nel tempo."
)
