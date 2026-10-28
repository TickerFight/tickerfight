"""Parametri dell'articolo n. 302 - "ACF e PACF dei rendimenti".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Idea: l'autocorrelazione (ACF) misura quanto un rendimento è legato a quelli dei giorni precedenti; l'autocorrelazione parziale (PACF)
misura il legame con il rendimento di k giorni prima tolta l'influenza dei giorni in mezzo. Le si calcola sui rendimenti logaritmici
giornalieri dell'S&P 500, sul loro valore assoluto e sul loro quadrato (la grandezza dei movimenti, senza il segno), sull'intero periodo
e in finestre di dieci anni non sovrapposte. Il confronto con il caso si fa rimescolando i rendimenti (la «scimmia»): rimescolati su
tutta la storia, i rendimenti perdono ogni memoria ma conservano la stessa distribuzione.
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
NOMI_ESENTI = ("ACF", "PACF", "AR(1)", "Ljung-Box")

# --- Misure ----------------------------------------------------------------------------------------------------
NLAG = 20                         # ritardi guardati: da 1 a 20 sedute (circa un mese di borsa)
NLAG_LUNGO = 100                  # per il grafico della persistenza della grandezza dei movimenti
SOGLIA = 0.05                     # livello di significatività dei test
SOGLIA_FORTE = 0.01
H1_ACF_MAX = 0.10                 # ipotesi 1: nessuna autocorrelazione dei rendimenti supera 0,10 in valore assoluto
H3_RAPPORTO = 5                   # ipotesi 3: rapporto minimo tra l'autocorrelazione dei rendimenti assoluti e quella dei rendimenti
H4_DIFFERENZA = 0.10              # ipotesi 4: differenza minima tra la finestra con l'autocorrelazione più alta e quella più bassa
H5_R2_MAX = 0.01                  # ipotesi 5: quota di varianza spiegata dal ritardo 1 sotto l'1%
H5_QUOTA_FINESTRE = 0.50          # ipotesi 5: in almeno metà delle finestre
H6_PACF_MAX = 0.05                # ipotesi 6: nessuna autocorrelazione parziale dei ritardi da 2 in poi supera 0,05 in valore assoluto
SEDUTE_FINESTRA = 2520            # dieci anni di borsa
SEDUTE_ANNO = 252

# --- Confronto con il caso -------------------------------------------------------------------------------------
N_PERM = 1000                     # rimescolamenti dei rendimenti su tutta la storia
SEME = 20261028

# --- Ipotesi, scritte PRIMA di guardare i risultati ------------------------------------------------------------
IPOTESI = (
    "1) Sull'intero periodo nessuna delle prime venti autocorrelazioni dei rendimenti giornalieri supera 0,10 in valore assoluto. "
    "2) Piccola non vuol dire nulla: il test di Ljung-Box sui primi venti ritardi rifiuta l'assenza di autocorrelazione dei rendimenti "
    "(p-value sotto 0,01) e l'autocorrelazione al primo ritardo reale cade fuori dal 99% di quelle ottenute rimescolando i rendimenti. "
    "3) La memoria sta nella grandezza dei movimenti, non nel segno: l'autocorrelazione al primo ritardo dei rendimenti assoluti è almeno "
    "cinque volte quella dei rendimenti (in valore assoluto) ed è positiva in tutti i primi venti ritardi. "
    "4) La memoria dei rendimenti non è stabile: tra le finestre di dieci anni, l'autocorrelazione al primo ritardo più alta supera quella "
    "più bassa di almeno 0,10. "
    "5) La memoria dei rendimenti vale poco: un modello AR(1) spiega meno dell'1% della varianza dei rendimenti sull'intero periodo e in "
    "almeno la metà delle finestre. "
    "6) Dopo il primo ritardo la PACF non aggiunge memoria: nessuno dei ritardi da 2 a 20 ha un'autocorrelazione parziale oltre 0,05 in "
    "valore assoluto sull'intero periodo."
)
