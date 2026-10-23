"""Parametri dell'articolo n. 61 - "Sharpe, Sortino, Calmar: quale ti inganna meno?".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: si prendono otto regole di investimento fisse, decise a priori (nessuna ottimizzata), e si misurano con tre metriche
(Sharpe, Sortino, Calmar). Si guarda se le tre metriche danno la stessa classifica, quanto la classifica resta uguale
da un decennio al successivo, quanto è fragile al rumore dei dati (bootstrap) e che cosa dicono di regole decise dal caso.
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

# --- Le otto regole (long o cash) -----------------------------------------------------------------
# Il segnale della chiusura di ieri decide la posizione di oggi (nessun look-ahead, come nell'articolo 4).
# Nessuna regola è ottimizzata: sono le versioni "da manuale". Ordine = ordine delle tabelle dell'articolo.
STRATEGIE = {
    "bh": ("Buy & hold", ("bh",)),
    "sma50": ("Prezzo sopra la media a 50 giorni", ("sopra_media", 50)),
    "sma100": ("Prezzo sopra la media a 100 giorni", ("sopra_media", 100)),
    "sma200": ("Prezzo sopra la media a 200 giorni", ("sopra_media", 200)),
    "cross": ("Incrocio 50/200", ("incrocio", 50, 200)),
    "mom": ("Momentum a 12 mesi", ("momentum", 252)),
    "calma": ("Solo a mercato calmo", ("calma", 20, 0.20)),       # investito se la volatilità a 20 giorni è sotto il 20% annuo
    "ritorno": ("Ritorno alla media nel trend", ("ritorno_media", 5, 200)),  # investito se sotto la media a 5 giorni ma sopra quella a 200
}
# Strumento di prova, fuori dalle classifiche: metà del capitale nel buy & hold e metà in cassa, sempre.
META = ("meta", "Metà buy & hold, metà cassa")
ID_BH, ID_FILTRO = "bh", "sma200"  # i due protagonisti dei confronti con il caso

# --- Metriche (tutte sui rendimenti giornalieri netti dei costi) ------------------------------------------
SEDUTE_ANNO = 252                 # per annualizzare Sharpe e Sortino
TASSO_SENZA_RISCHIO = 0.0         # la cassa non rende nella simulazione, quindi lo Sharpe usa zero come tasso senza rischio
OBIETTIVO_SORTINO = 0.0           # il Sortino penalizza solo i rendimenti giornalieri sotto zero
COSTO_CAMBIO = 0.001              # 0,1% del valore a ogni acquisto o vendita; nessuna tassa

# --- Finestre -----------------------------------------------------------------------------------------------
INIZIO_TEST_SEDUTE = 260          # le prime sedute servono per il momentum a 252 giorni: tutte le regole partono dallo stesso giorno
SEDUTE_BLOCCO = 2520              # blocchi non sovrapposti di dieci anni di borsa

# --- Bootstrap e scimmie --------------------------------------------------------------------------------------
SEME = 20261022
N_BOOTSTRAP = 1000                # serie ricampionate a blocchi circolari
LUNGHEZZA_BLOCCO_BOOT = 21        # un mese di borsa
LIVELLO_CONFIDENZA = 0.95
N_SCIMMIE = 1000                  # regole casuali con lo stesso tempo investito e lo stesso numero di cambi del filtro a 200 giorni
SOGLIA_SCIMMIE = 0.90             # quota di scimmie che il filtro deve battere per dire che "batte il caso"

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
TOLLERANZA_UGUALI = 0.01          # due valori di Sharpe o Sortino sono "uguali" se differiscono meno di questo
DIFFERENZA_RELATIVA_CALMAR = 0.10 # il Calmar "distingue" due regole se differisce di almeno il 10% in valore relativo

NOMI_ESENTI = tuple(v[0] for v in STRATEGIE.values()) + (META[1], "Incrocio 50/200", "50/200")

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Sull'intero periodo le tre metriche non indicano la stessa regola come migliore: i vincitori sono almeno due diversi. "
    "2) Il Calmar è la metrica che si discosta di più dalle altre: la media delle correlazioni di rango (tau di Kendall) del Calmar con Sharpe e Sortino, "
    "calcolata sui blocchi di dieci anni, è la più bassa delle tre. "
    "3) Il Calmar è la metrica meno persistente: la correlazione di rango media (Spearman) tra la classifica di un decennio e quella del successivo "
    "è la più bassa delle tre. "
    "4) Il Calmar è il più fragile al rumore dei dati: nel bootstrap la regola vincitrice sull'intero periodo resta prima in una quota di serie "
    "più bassa che per lo Sharpe. "
    "5) Lo Sharpe e il Sortino danno al buy & hold dimezzato lo stesso voto del buy & hold intero (differenza sotto 0,01), mentre il Calmar li "
    "distingue (differenza relativa di almeno il 10%). "
    "6) Il filtro a 200 giorni batte almeno il 90% delle scimmie (regole casuali con lo stesso tempo investito e lo stesso numero di cambi) in tutte e tre le metriche."
)
