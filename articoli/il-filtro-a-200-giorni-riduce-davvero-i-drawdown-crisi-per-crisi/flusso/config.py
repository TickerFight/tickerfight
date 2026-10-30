"""Parametri dell'articolo n. 133 - "Il filtro a 200 giorni riduce davvero i drawdown?".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati di QUESTO articolo.
Attenzione: nell'articolo 122 abbiamo già visto, in aggregato, che il drawdown massimo della regola è il 60% circa di quello del buy & hold. Qui si guarda crisi per crisi.

Una crisi (episodio) è un tratto dal massimo al minimo del buy & hold sull'S&P 500 (indice di prezzo, dal 1927, senza dividendi) in cui la perdita arriva ad almeno il 20% prima di tornare a un
nuovo massimo. Per ogni episodio si misura quanto perde il buy & hold e quanto perde la regola a media mobile a 200 sedute (liquidi sotto la media, segnale ritardato di una seduta, rendimento
zero in liquidità) nello stesso tratto, dopo quante sedute dal massimo la regola esce, quanto aveva già perso l'indice a quel punto, e che cosa succede nei dodici mesi dopo il minimo.
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

MEDIA = 200
GIORNI_ANNO = 252
SOGLIA_EPISODIO = 0.20               # perdita minima del buy & hold per contare l'episodio
SESSIONI_RAPIDO = 60                 # un episodio è «rapido» se dal massimo al minimo passano meno di 60 sedute
H2_QUOTA = 1.0 / 3.0                 # 2) in almeno un terzo degli episodi la regola evita meno della metà della perdita
H3_USCITA = 0.10                     # 3) alla mediana la regola esce quando l'indice ha già perso almeno il 10%
H6_EPISODI = 10                      # 6) almeno 10 episodi

IPOTESI = (
    "1) In ogni episodio (perdita del buy & hold di almeno il 20%) la regola perde meno del buy & hold. "
    "2) In almeno un terzo degli episodi la regola evita meno della metà della perdita del buy & hold, cioè la protezione è debole. "
    "3) La regola esce, in mediana, quando l'indice ha già perso almeno il 10% dal massimo. "
    "4) Nei dodici mesi dopo il minimo, la regola rende meno del buy & hold nella maggioranza degli episodi: il filtro perde il rimbalzo. "
    "5) La protezione è più debole negli episodi rapidi (meno di 60 sedute dal massimo al minimo) che in quelli lenti: la perdita media della regola, in rapporto a quella del buy & hold, è più alta. "
    "6) Gli episodi sono almeno 10 nel campione."
)
