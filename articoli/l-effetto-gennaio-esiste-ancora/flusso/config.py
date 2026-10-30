"""Parametri dell'articolo n. 162 - "L'effetto gennaio".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

L'«effetto gennaio» dice due cose: gennaio rende in media più degli altri mesi, e rende di più per le azioni di piccole dimensioni. Lo si prova sull'S&P 500 (indice di
prezzo, dal 1927, rendimenti mensili da fine mese a fine mese, senza dividendi) e sul Russell 2000 (piccole capitalizzazioni, dal 1987). Il confronto è tra gennaio e
gli altri undici mesi; la significatività si misura con un test di permutazione (le etichette dei mesi mescolate a caso). Si guarda anche se l'effetto è cambiato dopo la
pubblicazione dei primi studi (1976) e se la direzione di gennaio anticipa quella dei mesi restanti dell'anno («barometro di gennaio»).
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

TICKER = "^GSPC"
TICKER_PICCOLE = "^RUT"
INIZIO_DOWNLOAD = "1927-01-01"
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "gspc_giornaliero.csv"
FILE_PICCOLE = DATI / "rut_giornaliero.csv"
FILE_METADATI = DATI / "gspc_metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere dell'S&P 500 e del Russell 2000"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = "Si usano solo le chiusure; i dividendi non sono considerati"
NOMI_ESENTI = ("S&P 500", "Russell 2000", "Russell")

ANNO_SPARTIACQUE = 1976              # primi studi sull'effetto gennaio: prima e dopo
N_PERMUTAZIONI = 10000
SEME = 20261030
SOGLIA_P = 0.05
H6_QUOTA = 0.60                      # 6) barometro: gennaio e il resto dell'anno hanno lo stesso segno in oltre il 60% degli anni

IPOTESI = (
    "1) Sull'S&P 500 il rendimento medio di gennaio è più alto di quello medio degli altri undici mesi. "
    "2) La differenza non è significativa al 5% con il test di permutazione: tra le oscillazioni dei mesi il vantaggio di gennaio si confonde. "
    "3) La differenza di gennaio è più piccola dopo il 1976 che prima. "
    "4) Sul Russell 2000 (dal 1987) la differenza tra il rendimento di gennaio e quello degli altri mesi è più grande di quella dell'S&P 500 nello stesso periodo: l'effetto è delle piccole. "
    "5) Gennaio non è il mese con il rendimento medio più alto sull'S&P 500: sta fuori dai primi tre. "
    "6) Il barometro di gennaio funziona: il segno di gennaio coincide con quello del rendimento da febbraio a dicembre in oltre il 60% degli anni."
)
