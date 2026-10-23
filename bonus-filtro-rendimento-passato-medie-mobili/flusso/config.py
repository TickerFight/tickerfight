"""Parametri dell'articolo bonus - "Applichiamo il filtro sul rendimento passato".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni
numero dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.
L'articolo è fuori programmazione e fuori catalogo: per questo la cartella si chiama "bonus" e non ha numero.

Idea: nell'articolo precedente, sui titoli del 2021-2026, la regola 50/200 andava meglio quando il rendimento
dei dodici mesi precedenti era basso. Qui si applica quel filtro come strategia - regola sui titoli con
rendimento passato basso, buy & hold sugli altri - e la si prova FUORI CAMPIONE: in un periodo precedente
(cinque anni fino a ottobre 2021) e su titoli mai usati negli articoli precedenti.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
DATI_TITOLI = DATI / "titoli"                 # titoli nuovi, scaricati dal passo 1
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
TICKER_CAMBIO = "EURUSD=X"
INIZIO_DOWNLOAD = "2015-01-01"        # serve storia per i 12 mesi di rendimento passato e per la media a 200 giorni
FINE_TEST = "2021-10-20"              # il periodo del test finisce dove cominciava quello dell'articolo precedente
FUSO_BORSA = "America/New_York"
FILE_COMPOSIZIONE = DATI / "sp500_composizione.csv"          # stesso elenco e stesso ordine di sorteggio degli articoli precedenti
FILE_CAMBIO = DATI / "eurusd_giornaliero.csv"                # scaricato dal passo 1
FILE_SELEZ_SVIL = DATI / "selezione_sviluppo.csv"            # titoli già usati negli articoli precedenti
FILE_SELEZ_VAL = DATI / "selezione_validazione.csv"
FILE_RIFERIMENTO = DATI / "riferimento_2021_2026.csv"        # risultati dell'articolo precedente (2021-2026), solo come confronto
FILE_SELEZIONE = DATI / "selezione.csv"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure e aperture giornaliere di 150 titoli dell'S&P 500 mai usati prima e cambio euro/dollaro"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = ("Open e Close non corretti per i dividendi (già corretti per gli split): "
                "i dividendi non sono considerati, né per la regola né per il buy & hold")

# --- Campione -----------------------------------------------------------
# Stesso sorteggio degli articoli precedenti (stesso elenco, seme e ordine), saltando i titoli già usati: si
# prendono i primi N_TITOLI con dati completi (dodici mesi più duecento giorni prima dell'inizio del test).
N_TITOLI = 150
SEME = 2026
SEDUTE_MINIME_PRIMA = 420

# --- Scenario dell'investitore (identico agli articoli precedenti) ----------
CAPITALE = 500.0
COMMISSIONE = 1.0
ALIQUOTA = 0.26
ANNI_TEST = 5
SMA_VELOCE = 50
SMA_LENTA = 200
MODO_PRINCIPALE = "apertura"
FINESTRA_RENDIMENTO = 252

# --- La strategia con il filtro, fissata prima di guardare i risultati --------------------
# Il primo giorno del test si ordinano i titoli del campione per rendimento dei dodici mesi precedenti.
# Principale: sul terzo con il rendimento più basso si applica la regola 50/200, sugli altri si compra e si tiene.
# Controllo: lo stesso con la metà più bassa.
QUOTA_FILTRO = 1 / 3
QUOTA_CONTROLLO = 1 / 2

# --- Statistica ----------------------------------------------------------
N_PERMUTAZIONI = 10000
N_BOOTSTRAP = 2000
SEME_STAT = 11

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Fuori campione la relazione si ripete: tra rendimento passato e differenza regola meno buy & hold la "
    "correlazione di rango è negativa. "
    "2) La strategia con il filtro chiude sopra la regola applicata a tutti i titoli e sopra una scelta casuale "
    "dello stesso numero di titoli su cui applicare la regola. "
    "3) La strategia con il filtro NON batte il buy & hold applicato a tutti i titoli: anche nel terzo più favorevole "
    "la regola vinceva solo in una minoranza di casi."
)
