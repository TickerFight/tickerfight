"""Parametri dell'articolo n. 26 - "Il p-value in finanza".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Il p-value dice quanto sarebbe sorprendente un risultato se non ci fosse alcun effetto. Ma quando si provano molte regole, qualcuna risulta «significativa» per caso.
Qui si prova una famiglia di cinquanta regole sull'S&P 500 (indice di prezzo, dal 1927): «si resta investiti se la chiusura di ieri è sopra la media mobile di N
sedute, altrimenti si sta fermi», con N da 5 a 250 a passi di 5. Per ogni regola si confronta il rendimento medio giornaliero dei giorni in cui è investita con quello
dei giorni in cui è ferma (test t di Welch). Si guardano: il p-value della regola più famosa (la media a 200 sedute) presa da sola; quante regole risultano
«significative» al 5% provandole tutte; le correzioni per test multipli (Holm, Benjamini-Hochberg, e un test a permutazione sul massimo, con spostamenti circolari
dei rendimenti rispetto ai segnali, che conserva volatilità e memoria); la replicazione sulla seconda metà dei dati della regola migliore della prima; e infine se
una regola «significativa» rende davvero più del buy & hold.
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
NOMI_ESENTI = ("S&P 500", "Welch", "Holm", "Benjamini-Hochberg", "Bonferroni", "SMA")

GIORNI_ANNO = 252
LUNGHEZZE = tuple(range(5, 251, 5))           # cinquanta medie mobili: da 5 a 250 sedute
LUNGHEZZA_FAMOSA = 200                         # la regola più nota, dichiarata in anticipo
SOGLIA = 0.05
N_SPOSTAMENTI = 1000                           # spostamenti circolari per il test a permutazione
SPOSTAMENTO_MIN = 250                          # spostamento minimo (sedute) dei rendimenti rispetto ai segnali
SEME = 20261030

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H2_REGOLE = 25                   # ipotesi 2: più di 25 regole su 50 con p-value sotto il 5%
H3_REGOLE = 10                   # ipotesi 3: almeno 10 regole restano significative dopo Holm

IPOTESI = (
    "1) La media mobile a 200 sedute, presa da sola, ha un p-value sotto il 5%: i giorni in cui è investita hanno un rendimento medio diverso da quelli in cui è ferma. "
    "2) Provando tutte e cinquanta le regole, più di 25 hanno un p-value sotto il 5%: le regole sono molto simili tra loro e il caso le fa «funzionare» insieme. "
    "3) Dopo la correzione di Holm almeno 10 regole su 50 restano significative al 5%. "
    "4) Il test a permutazione sul massimo (spostamenti circolari) dà alla regola migliore un p-value corretto sotto il 5%: l'effetto non è solo il frutto di aver provato cinquanta regole. "
    "5) La regola migliore nella prima metà dei dati, misurata sulla seconda metà, ha ancora un p-value sotto il 5% e lo stesso segno. "
    "6) Eppure la regola migliore rende, in rendimento annuo composto, meno del buy & hold sullo stesso periodo: significativa non vuol dire redditizia."
)
