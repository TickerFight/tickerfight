"""Parametri dell'articolo n. 201 - "PAC contro lump sum: conta più la lunghezza delle rate o il decennio di partenza?".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Round di TickerFight: due sfidanti con lo stesso budget. Il LUMP SUM compra tutto il primo giorno (è un buy & hold dal primo
giorno). Il PAC divide il budget in N rate uguali, una al primo giorno di Borsa di ciascuno degli N mesi di partenza; la
parte non ancora investita resta in cassa, senza interessi. Tutti e due sono valutati allo stesso giorno, 60 mesi dopo la
partenza, per OGNI mese di partenza della storia. Si fa variare N (3, 6, 12, 24, 36 rate) e si guarda in quali decenni di
partenza il PAC ha vinto, che cosa cambia se si parte vicino ai massimi e come si comportano gli esiti peggiori.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: indici di prezzo (ticker Yahoo Finance, nome, valuta) -----------------------------------------------
# Scelti a priori, gli stessi dell'articolo 519. Sono indici di prezzo (niente dividendi): il confronto è sempre dentro lo
# stesso indice e in valuta locale. L'S&P 500, con la storia più lunga, è l'indice principale.
INDICI = [
    ("^GSPC", "S&P 500 (Stati Uniti)", "USD"),
    ("^GDAXI", "DAX (Germania)", "EUR"),
    ("^FTSE", "FTSE 100 (Regno Unito)", "GBP"),
    ("^N225", "Nikkei 225 (Giappone)", "JPY"),
]
INIZIO_DOWNLOAD = "1927-01-01"
FUSO_BORSA = "America/New_York"
URL_FONTE = "https://finance.yahoo.com/"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere di quattro indici azionari (S&P 500, DAX, FTSE 100, Nikkei 225)"
NOMI_ESENTI = ("S&P", "DAX", "FTSE 100", "Nikkei 225", "FTSE", "201", "519", "TickerFight")
INDICE_PRINCIPALE = "^GSPC"


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Il confronto ---------------------------------------------------------------------------------------------
BUDGET = 12000.0                   # euro totali da investire
RATE = (3, 6, 12, 24, 36)          # lunghezze del PAC in mesi (una rata al mese)
ORIZZONTE = 60                     # mesi dalla partenza al giorno di valutazione (primo giorno di Borsa del mese t+60)
N_PRINCIPALE = 12                  # il PAC "di riferimento" per decenni, massimi, esiti peggiori e scimmie
# Prezzi: chiusura del primo giorno di Borsa di ogni mese (si acquista a quel prezzo). Partenze: ogni mese per cui t+60 sta nei dati.

# --- Partenze vicino ai massimi -----------------------------------------------------------------------------------
# Una partenza è "ai massimi" se il prezzo del mese di partenza è entro questa quota dal massimo dei prezzi mensili
# fino a quel mese incluso (informazione nota alla partenza, nessun look-ahead).
SOGLIA_MASSIMI = 0.03

# --- Decenni di partenza -------------------------------------------------------------------------------------------
# Le partenze dell'S&P 500 si raggruppano per decennio di calendario. Decenni fissati a priori: dal 1930 al 2010 (nove gruppi, tutti con
# 120 partenze). Restano fuori i 25 mesi del 1927-1929 e le partenze dal 2020 in poi, che non riempiono un decennio.
DECENNI = tuple(range(1930, 2020, 10))

# --- Il caso: scimmie ------------------------------------------------------------------------------------------------
SEME = 20261023
N_SCIMMIE = 200                    # per ogni partenza: scimmie che piazzano le N_PRINCIPALE rate in mesi a caso (con ripetizione) entro i primi N_PRINCIPALE mesi
N_BOOTSTRAP = 2000
LIVELLO_CONFIDENZA = 0.95

# --- Soglie delle ipotesi (numeri riportati qui per scriverli nell'articolo senza cifre a mano) -----------------------
SOGLIE = {"ip1_quota": 0.55, "ip3_min_dec": 1, "ip3_max_dec": 3, "ip4_pp": 10.0, "ip6_lo": 0.45, "ip6_hi": 0.55}

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Nell'S&P 500, con valutazione a 60 mesi dalla partenza, il lump sum chiude davanti al PAC in più del 55% dei mesi di partenza, "
    "per ciascuna delle cinque lunghezze del PAC (3, 6, 12, 24 e 36 rate). "
    "2) Più il PAC è lungo, meno spesso vince: la quota di vittorie del lump sum cresce a ogni passo da 3 a 36 rate, e lo fa in tutti e quattro gli indici. "
    "3) Il PAC a 12 rate vince la maggioranza delle partenze in almeno un decennio di partenza dell'S&P 500 e in non più di tre: "
    "a decidere sono pochi periodi, non la regola. "
    "4) Partire vicino ai massimi (entro il 3% dal massimo storico noto alla partenza) non cambia il verdetto: nell'S&P 500, con il PAC a 12 rate, "
    "la quota di vittorie del lump sum nelle partenze ai massimi sta entro 10 punti percentuali da quella delle altre partenze. "
    "5) Il PAC a 12 rate protegge dal caso peggiore: nell'S&P 500 il quinto percentile del valore finale in euro è più alto per il PAC che per il lump sum. "
    "6) Una scimmia che piazza le 12 rate in mesi a caso non è né meglio né peggio del PAC regolare: nell'S&P 500 la quota di partenze in cui il PAC "
    "regolare batte più della metà delle scimmie sta tra il 45% e il 55%."
)
