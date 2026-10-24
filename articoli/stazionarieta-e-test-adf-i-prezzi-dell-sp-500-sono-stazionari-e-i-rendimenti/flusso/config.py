"""Parametri dell'articolo n. 301 - "Stazionarietà e test ADF".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Idea: il test di Dickey-Fuller aumentato (ADF) ha come ipotesi nulla la radice unitaria (serie non stazionaria). Lo si applica al
logaritmo del prezzo dell'S&P 500 e ai suoi rendimenti logaritmici giornalieri, sull'intero periodo e in finestre di dieci anni non
sovrapposte; poi si misura con simulazioni quanto il test sia affidabile (dimensione e potenza) su serie lunghe quanto una finestra.
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
NOMI_ESENTI = ("ADF", "KPSS")

# --- Test ----------------------------------------------------------------------------------------------------
SOGLIA = 0.05                     # livello di significatività dei test
SOGLIA_FORTE = 0.01
MAXLAG_AIC = 20                   # ritardi massimi per l'ADF sui dati reali; il numero è scelto col criterio AIC
REGR_LIVELLI = "ct"               # logaritmo del prezzo: costante e trend deterministico (la serie sale nel tempo)
REGR_LIVELLI_ALT = "c"            # robustezza: solo costante
REGR_RENDIMENTI = "c"             # rendimenti: solo costante (oscillano attorno a una media)
H3_QUOTA_LIV = 0.80               # ipotesi 3: quota minima di finestre in cui il prezzo non rifiuta
H3_QUOTA_REND = 0.95              # ipotesi 3: quota minima di finestre in cui i rendimenti rifiutano
H5_POTENZA_MAX = 0.50             # ipotesi 5: potenza massima
H5_DIM_MIN, H5_DIM_MAX = 0.03, 0.07   # ipotesi 5: intervallo della dimensione
SEDUTE_FINESTRA = 2520            # dieci anni di borsa
SEDUTE_ANNO = 252

# --- Simulazioni (dimensione e potenza del test su serie lunghe come una finestra) -----------------------------
N_SIM = 1000
MAXLAG_SIM = 5                    # ritardi fissi nelle simulazioni (niente selezione: velocità)
SEME = 20261024
EMIVITA_ANNI = 5                  # la serie stazionaria simulata ritorna a metà strada verso la media in cinque anni
# AR(1) sul log-prezzo: phi = 0,5^(1/(emivita in sedute)); volatilità giornaliera uguale a quella dei dati reali

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------
IPOTESI = (
    "1) Sull'intero periodo l'ADF applicato al logaritmo del prezzo NON rifiuta la radice unitaria (p-value sopra 0,05). "
    "2) Sull'intero periodo l'ADF applicato ai rendimenti giornalieri la rifiuta con decisione (p-value sotto 0,01). "
    "3) Lo stesso vale nelle finestre di dieci anni: sul logaritmo del prezzo il test non rifiuta in almeno l'80% delle finestre, "
    "sui rendimenti rifiuta (p-value sotto 0,05) in almeno il 95%. "
    "4) Stazionario non vuol dire costante: la volatilità annualizzata del decennio più turbolento è almeno il doppio di quella del decennio più calmo. "
    "5) Il test ha una potenza modesta: su una serie davvero stazionaria ma lenta (mezza vita di cinque anni) lunga come una finestra, "
    "l'ADF rifiuta la radice unitaria in meno del 50% delle simulazioni; su un random walk rifiuta in una quota vicina al 5% (tra 3% e 7%)."
)
