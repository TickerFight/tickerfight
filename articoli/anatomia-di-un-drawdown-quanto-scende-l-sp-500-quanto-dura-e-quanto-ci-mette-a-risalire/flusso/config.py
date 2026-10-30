"""Parametri dell'articolo n. 261 - "Anatomia di un drawdown".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: sull'S&P 500 dal 1927 si misura ogni drawdown (discesa dal massimo storico fino al nuovo massimo): quanto scende,
quanto dura la discesa, quanto serve per recuperare. Poi si confronta la serie vera con serie "del caso" ottenute
rimescolando a sorte gli stessi rendimenti giornalieri.

Letteratura (abstract letti prima di scrivere le ipotesi):
  - Grossman e Zhou (1993), "Optimal Investment Strategies for Controlling Drawdowns", Mathematical Finance 3(3), 241-276:
    studiano la politica d'investimento ottima per chi vuole tenere la ricchezza sopra una frazione fissa del proprio massimo storico.
  - Magdon-Ismail e Atiya (2004), "Maximum drawdown", Risk, ottobre 2004: legano il drawdown massimo al rendimento medio e al
    rapporto di Sharpe e propongono leggi di scala con la durata della serie.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
TICKER = "^GSPC"                  # S&P 500, indice di prezzo (senza dividendi), dal 1927
INIZIO_DOWNLOAD = "1927-01-01"
FUSO_BORSA = "America/New_York"
FILE_DATI = DATI / "gspc_giornaliero.csv"
FILE_METADATI = DATI / "gspc_metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere dell'indice S&P 500"
URL_FONTE = "https://finance.yahoo.com/quote/%5EGSPC/history/"
NOTA_COLONNA = "Si usano solo le chiusure; i dividendi non sono considerati"

# --- Definizione di drawdown -------------------------------------------------------------------------------------
# Drawdown a una data = chiusura / massimo storico precedente - 1. Un "episodio" va dal massimo storico fino al giorno in cui
# la chiusura torna almeno a quel massimo (recupero). Si contano solo gli episodi che scendono almeno della soglia minima.
SOGLIA_MINIMA = 0.05
SOGLIE = (0.05, 0.10, 0.20, 0.30)  # profondità per i conteggi
SOGLIA_RECUPERO_ANALISI = 0.10     # episodi "veri" per i confronti discesa/recupero
SEDUTE_ANNO = 252
GIORNI_MESE = 30.4375

# --- Confronto con il caso ----------------------------------------------------------------------------------------
# Si rimescolano a sorte i rendimenti giornalieri reali (stessa distribuzione, ordine casuale): si distrugge il
# raggruppamento delle giornate agitate. Per ogni serie rimescolata si misurano gli stessi indicatori.
N_RIMESCOLAMENTI = 500
SEME = 20261030
LIVELLO_CONFIDENZA = 0.95

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) L'indice passa più di due sedute su tre sotto il massimo storico precedente: stare sul massimo è l'eccezione. "
    "2) I drawdown di almeno il 10% sono frequenti: in media almeno uno ogni due anni dal 1927. "
    "3) Il recupero (dal minimo al nuovo massimo) dura più della discesa (dal massimo al minimo) in più della metà "
    "dei drawdown di almeno il 10%. "
    "4) Più un drawdown è profondo, più dura: la correlazione di rango tra profondità e durata totale, sugli episodi "
    "di almeno il 5%, è superiore a 0,5. "
    "5) Il drawdown massimo reale è più profondo del 95° percentile delle serie rimescolate a caso: i crolli veri sono "
    "più gravi di quelli che produrrebbe il solo caso con gli stessi rendimenti."
)
