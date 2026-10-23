"""Parametri dell'articolo n. 519 - "Chi ha più fortuna: chi compra una volta o chi compra ogni mese?".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Due investitori hanno lo stesso budget. Il primo lo investe tutto il primo giorno ("una volta", lump sum). Il secondo lo
divide in dodici rate uguali, una al primo giorno di Borsa di ciascuno dei dodici mesi ("ogni mese", PAC); la parte non
ancora investita resta ferma in cassa, senza interessi. Si confronta il valore in euro dei due portafogli dopo 12 e dopo
24 mesi dalla partenza, per OGNI mese di partenza possibile della storia di ciascun indice.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati: indici di prezzo (ticker Yahoo Finance, nome, valuta) -----------------------------------------------
# Scelti a priori. Sono indici di prezzo (niente dividendi): il confronto è sempre dentro lo stesso indice e in valuta
# locale, quindi la mancanza dei dividendi non cambia il confronto tra i due modi di comprare, ma abbassa il rialzo medio.
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
NOMI_ESENTI = ("S&P", "DAX", "FTSE 100", "Nikkei 225", "FTSE", "519")
INDICE_PRINCIPALE = "^GSPC"        # quello dei grafici di dettaglio, scelto a priori: ha la storia più lunga


def file_dati(ticker: str) -> Path:
    return DATI / (ticker.replace("^", "").replace(".", "_") + ".csv")


# --- Il confronto ---------------------------------------------------------------------------------------------
BUDGET = 1200.0                    # euro totali da investire: 100 euro al mese per 12 mesi
N_RATE = 12                        # rate del PAC, una al primo giorno di Borsa di ogni mese
ORIZZONTI = (12, 24)               # mesi dalla partenza al giorno di valutazione (il primo giorno di Borsa del mese)
# Prezzi: chiusura del primo giorno di Borsa di ogni mese (si acquista a quel prezzo). Mese di partenza = ogni mese
# in cui l'orizzonte più lungo sta ancora nei dati.
COMMISSIONI = (0.0, 2.0)           # euro per ordine: 0 e 2. Il lump sum fa 1 ordine, il PAC 12.
ORIZZONTE_PRINCIPALE = 12

# --- Il caso ------------------------------------------------------------------------------------------------------
SEME = 20261023
N_RIMESCOLATE = 1000               # storie sintetiche per indice: gli stessi rendimenti mensili, in ordine rimescolato
N_SCIMMIE = 200                    # per ogni partenza: scimmie che piazzano le 12 rate in mesi a caso (con ripetizione)
N_BOOTSTRAP = 2000
LIVELLO_CONFIDENZA = 0.95
SOGLIA_PARITA_PP = 5.0             # "entro cinque punti percentuali" nelle ipotesi

# Le soglie delle ipotesi, riportate qui come numeri solo per scriverle nell'articolo senza cifre a mano (valori identici a quelli del testo che segue)
SOGLIE = {"ip1_quota": 0.55, "ip2_scende": 0.80, "ip2_sale": 0.25, "ip5_salto_pp": 3.0, "ip6_lo": 0.45, "ip6_hi": 0.55, "alfa": 0.05}

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Su 12 mesi, nell'S&P 500 chi investe tutto subito chiude davanti al PAC in più del 55% dei mesi di partenza "
    "(ci aspettiamo circa due su tre, perché in media il mercato sale). "
    "2) Il PAC vince quasi solo quando il mercato scende: tra le partenze in cui l'indice perde nei 12 mesi successivi, "
    "il PAC vince in almeno l'80% dei casi, mentre tra quelle in cui sale vince in meno del 25%. "
    "3) La quota di vittorie del lump sum nella storia vera è entro cinque punti percentuali da quella media delle storie "
    "con i rendimenti mensili rimescolati (stessi rendimenti, ordine a caso): a decidere è il rialzo medio, non una "
    "regolarità della storia. Quindi il test di rimescolamento NON rifiuta il caso (p corretto per Holm sopra 0,05). "
    "4) Su 24 mesi la quota di vittorie del lump sum non scende rispetto ai 12 mesi, in nessuno dei quattro indici "
    "(il PAC resta fermo nei mesi 13-24, mentre il lump sum continua a esporsi al rialzo). "
    "5) Con 2 euro a ordine (12 ordini contro 1, su 1.200 euro) la quota di vittorie del lump sum sale di almeno "
    "tre punti percentuali nell'S&P 500: sul piccolo capitale i costi del PAC pesano. "
    "6) Una scimmia che piazza le 12 rate in mesi a caso non è né meglio né peggio del PAC regolare: la quota di partenze "
    "in cui il PAC regolare batte la scimmia mediana sta tra il 45% e il 55% nell'S&P 500."
)
