"""Parametri dell'articolo n. 281 - "Portafogli di titoli casuali contro l'indice".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Round di TickerFight: mille portafogli estratti a caso da un universo di grandi titoli americani (l'S&P 100) contro l'indice.
Ogni portafoglio ha k titoli (5, 10, 20, 30) a pesi uguali, ribilanciati al primo giorno di Borsa di ogni anno, senza
costi. Si confronta il rendimento annuo composto con quello dell'indice (lo SPY, a rendimento totale) e con quello
dell'intero universo a pesi uguali (che ha lo stesso difetto del campione: vedi i limiti dell'articolo). La domanda: quanto
conta, da sola, la scelta dei titoli?
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
# Prezzi di chiusura corretti per dividendi e frazionamenti (rendimento totale), da Yahoo Finance.
INIZIO = "2006-01-01"              # primo giorno incluso; si usa dal primo giorno di Borsa in poi
FUSO_BORSA = "America/New_York"
URL_FONTE = "https://finance.yahoo.com/"
FILE_PREZZI = DATI / "prezzi.csv"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "le chiusure giornaliere corrette per dividendi di titoli americani e dello SPY"
NOMI_ESENTI = ("S&P 100", "S&P", "SPY", "281", "TickerFight")

# Indice di confronto: SPY (ETF sull'S&P 500), con dividendi reinvestiti.
INDICE = "SPY"

# Universo scelto a priori: i componenti dell'S&P 100 come li conosciamo oggi (lista fissata PRIMA di guardare i dati,
# una sola classe azionaria per società). Verranno tenuti solo i titoli con prezzi dal primo giorno del periodo: gli
# altri (quotati dopo il 2006) escono dall'universo e il numero esatto è riportato nell'articolo.
UNIVERSO = (
    "AAPL ABBV ABT ACN ADBE AIG AMD AMGN AMT AMZN AVGO AXP BA BAC BK BKNG BLK BMY BRK-B C CAT CHTR CL CMCSA COF COP COST "
    "CRM CSCO CVS CVX DE DHR DIS DUK EMR FDX GD GE GILD GM GOOGL GS HD HON IBM INTC INTU ISRG JNJ JPM KO LIN LLY LMT LOW "
    "MA MCD MDLZ MDT MET META MMM MO MRK MS MSFT NEE NFLX NKE NOW NVDA ORCL PEP PFE PG PLTR PM PYPL QCOM RTX SBUX SCHW SO "
    "SPG T TGT TMO TMUS TSLA TXN UBER UNH UNP UPS USB V VZ WFC WMT XOM"
).split()
SOGLIA_BUCHI = 0.01      # un titolo con più dell'1% di giorni senza prezzo (dopo il primo) esce dall'universo

# --- Portafogli casuali ---------------------------------------------------------------------------------------
K_TITOLI = (5, 10, 20, 30)     # titoli per portafoglio
K_PRINCIPALE = 20              # la dimensione di riferimento per ipotesi 1, 2 e 6
N_PORTAFOGLI = 1000            # portafogli estratti per ogni k (senza reinserimento dentro il portafoglio)
SEED = 20261023
SEED_CONTROLLO = (11, 22, 33, 44)   # altri quattro semi, per vedere se la quota di vittorie dipende dall'estrazione
LIVELLO_BASSO, LIVELLO_ALTO = 0.05, 0.95   # percentili che delimitano la "fascia" dei portafogli
GIORNI_ANNO_BORSA = 252
GIORNI_ANNO_CALENDARIO = 365.25
TASSO_SENZA_RISCHIO = 0.0      # semplificazione dichiarata
# Due metà del periodo, per vedere se chi ha avuto fortuna nella prima la ripete nella seconda
META_DATA = "2016-01-01"       # la seconda metà comincia dal primo giorno di Borsa di questa data

# --- Soglie delle ipotesi (riportate qui per scriverle nell'articolo senza cifre a mano) -----------------------------
SOGLIE = {"ip1_quota": 0.50, "ip2_lo": 0.40, "ip2_hi": 0.60, "ip4_quota": 0.25, "ip5_pp": 5.0, "ip6_corr": 0.30}

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Con 20 titoli, più della metà dei portafogli casuali batte lo SPY per rendimento annuo composto (lo prevediamo anche perché "
    "l'universo è fatto di società ancora grandi oggi, un vantaggio che dichiariamo tra i limiti). "
    "2) Con 20 titoli, la quota di portafogli che batte l'intero universo a pesi uguali sta tra il 40% e il 60%: "
    "contro un confronto che ha il suo stesso difetto di campione, la scelta dei titoli da sola non dà né vantaggio né svantaggio. "
    "3) La fascia dei rendimenti (95° meno 5° percentile) si stringe a ogni passo, da 5 a 10, 20 e 30 titoli. "
    "4) Con 5 titoli almeno un portafoglio su quattro perde contro lo SPY: pochi titoli, esito affidato alla sorte. "
    "5) Il drawdown massimo mediano dei portafogli da 30 titoli sta entro 5 punti percentuali da quello dello SPY: "
    "la diversificazione tra titoli non evita i crolli dell'intero mercato. "
    "6) Chi ha avuto fortuna nella prima metà del periodo non la ripete nella seconda: con 20 titoli la correlazione, tra i portafogli, "
    "dell'eccesso di rendimento sullo SPY nelle due metà è in valore assoluto sotto 0,30."
)
