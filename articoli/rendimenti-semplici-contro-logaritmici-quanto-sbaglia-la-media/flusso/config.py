"""Parametri dell'articolo n. 2 - "Rendimenti semplici contro logaritmici".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: il rendimento semplice di una seduta è P(t)/P(t-1) - 1, quello logaritmico è ln(P(t)/P(t-1)). I logaritmi si sommano
nel tempo, i rendimenti semplici si compongono. La media dei rendimenti semplici è sempre più alta della media dei
logaritmici, di circa metà della varianza: è la ragione per cui "il rendimento medio" di un indice è più alto di quanto
l'indice abbia davvero reso a chi lo ha tenuto. Si misura quanto vale la differenza sul S&P 500, se la regola della
mezza varianza funziona, e come cambia con la volatilità del periodo e con la frequenza dei dati.
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

# --- Convenzioni di calcolo ---------------------------------------------
# Finestra: dal primo 31 dicembre (ultima chiusura del primo anno solare) all'ultima chiusura dell'ultimo anno solare
# COMPLETO. Così giornaliero, mensile e annuale coprono esattamente lo stesso periodo e gli anni sono un numero intero.
MESI_ANNO = 12                   # per annualizzare i rendimenti mensili: media mensile x 12
DECENNIO_MIN_ANNI = 5            # un decennio entra nel confronto solo se ha almeno questi anni nella finestra
CAPITALE = 500.0                 # solo per dare un'idea: valori lordi, senza commissioni né tasse
ESEMPIO_SU = 0.10                # esempio da manuale: +10% e poi -10%
ESEMPIO_GIU = -0.10
SOGLIA_GIORNO = 0.0001           # un centesimo di punto percentuale: sotto, semplice e logaritmico si confondono
SOGLIA_QUOTA_GIORNI = 0.90       # ipotesi 4: almeno il 90% delle sedute sotto la soglia
SOGLIA_PEGGIOR_GIORNO = 0.01     # ipotesi 4: nella peggior seduta la differenza supera un punto percentuale
GAP_MIN, GAP_MAX = 0.005, 0.03   # ipotesi 1: il divario tra media aritmetica e rendimento composto sta tra 0,5 e 3 punti l'anno
ERRORE_MEZZA_VARIANZA = 0.003    # ipotesi 2: la mezza varianza spiega il divario con errore sotto 0,3 punti l'anno
SOGLIA_CORRELAZIONE = 0.95       # ipotesi 3: correlazione tra divario e mezza varianza, tra decenni
SOGLIA_FREQUENZE = 0.01          # ipotesi 5: il divario cambia meno di un punto l'anno tra giornaliero, mensile e annuale

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) La media annua dei rendimenti semplici giornalieri supera il rendimento annuo composto di un valore compreso tra 0,5 e 3 punti percentuali. "
    "2) La mezza varianza (varianza annua dei rendimenti divisa per due) riproduce il divario tra media semplice e media logaritmica, "
    "con un errore sotto 0,3 punti l'anno sull'intero periodo e in ciascun decennio. "
    "3) Tra i decenni il divario segue la volatilità: la correlazione tra divario e mezza varianza è sopra 0,95, "
    "e il divario del decennio più volatile è maggiore di quello del decennio più calmo. "
    "4) Giorno per giorno la differenza tra rendimento semplice e logaritmico è trascurabile: sotto un centesimo di punto percentuale "
    "in almeno il 90% delle sedute, ma sopra un punto percentuale nella peggior seduta. "
    "5) Il divario non dipende dalla frequenza dei dati: calcolato con rendimenti giornalieri, mensili e annuali varia di meno di un punto l'anno."
)
