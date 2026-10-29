"""Parametri dell'articolo n. 303 - "ARIMA sui rendimenti".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Idea: un modello ARIMA(p, d, q) descrive una serie con la sua memoria (p ritardi dei valori passati, q ritardi degli errori passati) dopo
aver tolto d volte la tendenza. Sui rendimenti d è zero (un rendimento è già una differenza di logaritmi dei prezzi). Si adatta, sui
rendimenti logaritmici MENSILI dell'S&P 500 (chiusure di fine mese, senza dividendi), il modello scelto con il criterio BIC tra tutti gli
ordini fino a (2, 2); lo si verifica dentro il campione (BIC, spiegazione della varianza, residui) e FUORI dal campione: ogni dodici mesi si
ristima il modello solo con i dati già noti e si prevede il mese successivo, confrontando l'errore con quello della semplice media storica.
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
NOMI_ESENTI = ("ARIMA", "ARMA", "AR(1)", "MA(1)", "ARIMA(0,1,0)", "BIC", "AIC", "Ljung-Box", "Clark-West")

# --- Modello ---------------------------------------------------------------------------------------------------
P_MAX, Q_MAX = 2, 2                # ordini provati: tutte le coppie da (0, 0) a (2, 2)
MESI_INIZIALI = 240                # primi vent'anni solo per stimare; le previsioni cominciano dopo
OGNI_MESI = 12                     # il modello si ristima una volta all'anno, con i soli dati già noti
LAG_TEST = 12                      # ritardi del test di Ljung-Box sui residui e per l'errore standard di Newey-West
LAG_ADF = 12
H1_P_PIU_Q_MAX = 1                 # ipotesi 1: il BIC sceglie al massimo un parametro di memoria (p + q <= 1)
H2_R2_MAX = 0.02                   # ipotesi 2: il miglior modello spiega in campione meno del 2% della varianza
H3_R2_OOS_MAX = 0.01               # ipotesi 3: R quadro fuori campione sotto l'1%
SOGLIA = 0.05
SOGLIA_FORTE = 0.01
N_BOOT = 2000
BLOCCO_MEDIO = 12
LIVELLO_IC = 0.95
SEME = 20261030

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------
IPOTESI = (
    "1) Sull'intero periodo il BIC sceglie un modello con al massimo un parametro di memoria (p più q non superiore a uno): la serie dei rendimenti mensili ha pochissima struttura. "
    "2) Il modello scelto spiega, dentro il campione, meno del 2% della varianza dei rendimenti mensili. "
    "3) Fuori dal campione il modello non migliora la media storica di più dell'1%: l'R quadro fuori campione, calcolato sull'errore quadratico, è sotto l'1%. "
    "4) Il modello lascia intatta la volatilità: il test di Ljung-Box sui quadrati dei residui, a dodici ritardi, rifiuta al 1% (p-value sotto 0,01). "
    "5) Il segno previsto non batte il segno ovvio: la quota di mesi in cui il modello indovina il segno non supera la quota di mesi positivi, cioè quella di chi prevede sempre «sale». "
    "6) Il test di Clark-West non rifiuta al 5% l'uguaglianza tra il modello e la media storica."
)
