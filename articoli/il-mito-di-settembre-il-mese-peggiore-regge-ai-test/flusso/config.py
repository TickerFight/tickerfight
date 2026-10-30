"""Parametri dell'articolo n. 170 - "Il mito di settembre".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati di QUESTO articolo.
Attenzione: nell'articolo 162 (effetto gennaio) abbiamo già visto la classifica dei mesi dell'S&P 500 sull'intero periodo, e settembre era l'ultimo. Per questo la prima
ipotesi è dichiarata come già nota, e le altre riguardano aspetti che non avevamo guardato: significatività, correzione per la scelta del peggiore dei dodici mesi, stabilità
tra le due metà del campione.

«Settembre è il mese peggiore dell'anno». Si prova sull'S&P 500 (indice di prezzo, dal 1927, rendimenti mensili da fine mese a fine mese, senza dividendi). Il punto delicato:
tra dodici mesi uno è per forza il peggiore, quindi il confronto onesto non è «settembre contro gli altri» ma «il peggiore dei dodici contro il peggiore che si avrebbe se i
mesi non avessero nessuna differenza» (permutazione dei rendimenti tra i mesi). La permutazione mescola i rendimenti mensili tra tutti i mesi del campione.
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

MESE = 9                             # settembre
N_PERMUTAZIONI = 10000
SEME = 20261030
SOGLIA_P = 0.05
N_PEGGIORI = 3                       # 6) si tolgono i tre settembri peggiori

IPOTESI = (
    "1) (Già nota dall'articolo 162) Sull'intero periodo settembre ha il rendimento medio più basso dei dodici mesi. "
    "2) La differenza tra settembre e gli altri undici mesi ha un p-value di permutazione sotto 0,05. "
    "3) Il confronto onesto, che tiene conto del fatto che il peggiore dei dodici è comunque qualcuno (permutazione del minimo), ha un p-value di almeno 0,05. "
    "4) Settembre è il mese peggiore in entrambe le metà del campione (divise a metà del numero di anni). "
    "5) In oltre la metà dei settembri l'S&P 500 scende. "
    "6) Tolti i tre settembri peggiori, la media di settembre diventa positiva."
)
