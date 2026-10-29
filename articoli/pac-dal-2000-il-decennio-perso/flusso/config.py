"""Parametri dell'articolo n. 426 - "PAC dal 2000: il decennio perso".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Piano di accumulo (PAC): ogni mese si versa la stessa somma e si comprano quote (frazionate) dell'indice S&P 500 (indice di prezzo, senza
dividendi) alla chiusura della prima seduta del mese. Il piano dura dieci anni (centoventi versamenti) e si liquida alla chiusura della
prima seduta del mese successivo all'ultimo versamento, con commissione e imposta. Caso principale: il piano che parte a gennaio 2000.
Confronti: il lump sum (la stessa somma totale investita tutta insieme il primo giorno), tutte le altre date di partenza dal 1928, e serie
con gli stessi rendimenti mensili messi in ordine casuale.
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
NOMI_ESENTI = ("S&P 500", "PAC")

# --- Il piano -------------------------------------------------------------------------------------------------
VERSAMENTO = 100.0              # somma versata ogni mese
MESI = 120                      # versamenti: dieci anni
COMMISSIONE = 2.0               # per ogni acquisto e per la vendita finale
ALIQUOTA = 0.26                 # sulla plusvalenza, alla vendita finale (nessuna compensazione: una sola vendita)
ANNO_CASO = 2000                # il piano del caso principale parte a gennaio di quest'anno
ANNO_CRISI = 1929               # secondo caso storico di confronto: parte a gennaio di quest'anno

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_MARGINE = 0.10               # ipotesi 2: il piano 2000 chiude entro questo margine dal versato (in valore assoluto)
H2_QUOTA = 0.10                 # ipotesi 3: il piano 2000 sta nel peggior 10% delle date di partenza
H3_PUNTI = 0.10                 # ipotesi 1: il PAC supera il lump sum del 2000 di almeno 10 punti percentuali
H4_QUOTA = 0.15                 # ipotesi 4: su serie rimescolate meno del 15% dei piani fa peggio del piano 2000

# --- Confronto con il caso ----------------------------------------------------------------------------------------
N_PERM = 1000
SEME = 20261029
SOGLIA = 0.05

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------
IPOTESI = (
    "1) Il piano di accumulo che parte a gennaio 2000 fa meglio del lump sum dello stesso mese di almeno dieci punti percentuali di "
    "rendimento totale netto: il decennio perso colpisce molto di più chi investe tutto insieme. "
    "2) Anche il piano 2000 resta vicino al pareggio: il suo valore finale netto sta entro il dieci per cento (in più o in meno) dal "
    "totale versato. "
    "3) Il piano 2000 sta tra il dieci per cento peggiore di tutte le date di partenza dal 1928 (a parità di durata di dieci anni). "
    "4) Il caso non basta a spiegarlo: su serie con gli stessi rendimenti mensili messi in ordine casuale, meno del quindici per cento "
    "dei piani decennali chiude con un rendimento pari o peggiore di quello del piano 2000. "
    "5) Non è il solo decennio perso: il piano che parte a gennaio 1929 chiude sotto il totale versato (rendimento netto negativo)."
)
