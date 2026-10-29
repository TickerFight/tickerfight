"""Parametri dell'articolo n. 108 - "Tasse sulle plusvalenze: strategia attiva contro buy & hold".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Si confrontano, sull'S&P 500 (indice di prezzo, senza dividendi) e con l'imposta italiana sulle plusvalenze, un buy & hold, che paga l'imposta una sola volta
alla fine, e il filtro a 200 sedute (in mercato sopra la media, in liquidità senza interessi sotto), che realizza una plusvalenza o una minusvalenza a ogni
uscita e paga l'imposta subito, riducendo il capitale che continua a lavorare. Le minusvalenze realizzate si possono portare in compensazione di plusvalenze
successive fino al quarto anno solare dopo quello della perdita (regola italiana per i redditi diversi). L'aliquota ALIQUOTA vale per l'intera storia,
anche se in Italia è in vigore solo da pochi anni: è un'ipotesi di lavoro. Alla fine della storia si liquida tutto e si paga l'imposta sulla plusvalenza
latente, così da confrontare capitali comparabili.
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

SMA_GIORNI = 200
ALIQUOTA = 0.26                                # aliquota sulle plusvalenze
ALIQUOTE = (0.0, 0.125, 0.20, 0.26)            # aliquote della tabella di sensibilità (0,125 = titoli di Stato)
ANNI_CREDITO = 4                               # le minusvalenze valgono fino al quarto anno solare successivo
COSTO = 0.001                                  # costo di ogni cambio di posizione (0,10%), nella variante con costi
QUOTA_ANNI_TOP = 0.20                          # ipotesi 5: il 20% degli anni con più imposta

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_RIDUZIONE = 0.50              # ipotesi 1: le imposte tolgono almeno metà del vantaggio lordo del filtro
H4_QUOTA = 0.50                  # ipotesi 4: il filtro paga imposta in almeno metà degli anni
H5_QUOTA = 0.50                  # ipotesi 5: il 20% degli anni con più imposta paga almeno metà del totale
H6_ALIQUOTA = 0.15               # ipotesi 6: l'aliquota di pareggio è sotto il 15%

IPOTESI = (
    "1) Con aliquota del 26%, le imposte tolgono almeno metà del vantaggio lordo del filtro a 200 sedute rispetto al buy & hold. "
    "2) Dopo le imposte il filtro rende meno del buy & hold. "
    "3) La quota del guadagno finale che se ne va in imposte è più alta nel filtro che nel buy & hold. "
    "4) Il filtro paga imposta in almeno la metà degli anni. "
    "5) Il 20% degli anni con più imposta paga almeno metà delle imposte totali del filtro. "
    "6) L'aliquota di pareggio, cioè quella per cui il filtro rende come il buy & hold dopo le imposte, è inferiore al 15%."
)
