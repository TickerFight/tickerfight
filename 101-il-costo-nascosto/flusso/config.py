"""Parametri dell'articolo n. 101 - "Il costo nascosto: commissioni, slippage, ribilanciamento".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: si prendono otto regole di investimento fisse (le stesse dell'articolo 61, nessuna ottimizzata) e si fa variare
il costo per operazione da 0 a 0,5% del valore scambiato. Si guarda quanto costa a ciascuna regola, se il costo è
proporzionale al numero di cambi di posizione, se la classifica per Sharpe cambia, quanto costa ribilanciare un portafoglio
50/50 a frequenze diverse e che cosa succede a chi cambia posizione a caso con frequenze crescenti (scimmie).
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

# --- Le otto regole (long o cash), come nell'articolo 61 --------------------------------------------------------------
# Il segnale della chiusura di ieri decide la posizione di oggi (nessun look-ahead, come nell'articolo 4).
# "Cambio" = un acquisto o una vendita dell'intera posizione; entrare e uscire sono due cambi.
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
ID_BH, ID_FILTRO, ID_VELOCE = "bh", "sma200", "sma50"

# --- La griglia dei costi (quota del valore scambiato, per ogni acquisto o vendita) -----------------------------------
# Il costo è unico: somma di commissione, spread e slippage. Nessuna tassa.
COSTI = (0.0, 0.0005, 0.001, 0.002, 0.003, 0.005)
COSTO_MAX = COSTI[-1]
COSTO_PROVA = 0.001               # il costo "tipico" che si cita nel testo (0,1%)

SEDUTE_ANNO = 252
INIZIO_TEST_SEDUTE = 260          # le prime sedute servono per il momentum a 252 giorni: tutte le regole partono dallo stesso giorno

# --- Ribilanciamento: portafoglio 50% S&P 500, 50% cassa a rendimento zero -----------------------------------------------
QUOTA_AZIONI = 0.5
RIBILANCIAMENTI = {"giornaliero": 1, "mensile": 21, "annuale": 252}   # ogni quante sedute si riporta la quota al 50%

# --- Scimmie: posizione casuale (investito / cassa) con probabilità giornaliera p di cambiare stato ---------------------
SEME = 20261023
N_SCIMMIE = 300
PROB_CAMBIO = (0.01, 0.05, 0.10, 0.20, 0.50)

# --- Soglie delle ipotesi ------------------------------------------------------------------------------------------------
CAMBI_MIN_ANNO = 1.0              # ipotesi 1: si guardano le regole con almeno un cambio all'anno
BANDA_PROPORZIONALITA = (0.7, 1.3)  # ipotesi 1: perdita di rendimento / (cambi annui x costo) deve stare in questa banda
SOGLIA_BH = 0.0001                # ipotesi 2: perdita di rendimento annuo del buy & hold sotto 0,01 punti percentuali
SOGLIA_PROB_SCIMMIE = 0.10         # ipotesi 6: scimmie con probabilità di cambio almeno pari a questa

SOGLIA_RIBIL = 0.0005             # ipotesi 5: perdita di rendimento annuo con ribilanciamento annuale sotto 0,05 punti percentuali

NOMI_ESENTI = tuple(v[0] for v in STRATEGIE.values()) + ("50/50",)

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Il costo si paga a ogni cambio di posizione: per ogni regola con almeno un cambio all'anno, la perdita di rendimento annuo "
    "composto tra costo zero e costo 0,5% sta tra 0,7 e 1,3 volte (cambi all'anno x 0,5%). "
    "2) Il buy & hold, che compra una volta sola, perde meno di 0,01 punti percentuali di rendimento annuo anche con costo 0,5%. "
    "3) Il numero di regole con Sharpe più alto del buy & hold è più basso con costo 0,5% che con costo zero. "
    "4) Il filtro a 200 giorni conserva uno Sharpe più alto del buy & hold anche con costo 0,5%. "
    "5) Ribilanciare un portafoglio 50/50 ogni giorno costa, a parità di costo 0,5%, più di ribilanciare ogni mese, e ribilanciare ogni mese "
    "costa più che ogni anno; con ribilanciamento annuale la perdita di rendimento annuo è sotto 0,05 punti percentuali. "
    "6) Una scimmia che cambia posizione a caso con probabilità giornaliera di almeno il 10% ha un rendimento annuo mediano positivo "
    "a costo zero e negativo a costo 0,5%."
)
