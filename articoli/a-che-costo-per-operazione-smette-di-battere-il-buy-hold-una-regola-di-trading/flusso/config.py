"""Parametri dell'articolo n. 102 - "A che costo per trade muore la strategia?".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file.

Idea: l'articolo 101 ha fatto crescere il costo per operazione e ha guardato la perdita. Qui si rovescia la domanda: per ogni regola
si cerca il costo per cambio di posizione a cui la regola smette di battere il buy & hold (costo di pareggio), una volta sul rendimento
annuo e una volta sullo Sharpe. Studi che motivano le ipotesi (abstract letti):
  - Bajgrowicz e Scaillet (2012), Journal of Financial Economics: sul Dow Jones 1897-2011 i costi di transazione bassi eliminano
    la performance in campione delle regole tecniche.
  - Novy-Marx e Velikov (2016), Review of Financial Studies: le strategie con rotazione mensile sotto il 50% restano profittevoli
    al netto dei costi, poche di quelle con rotazione più alta.
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

# --- Dieci regole fisse (long o cash), decise prima, nessuna ottimizzata -----------------------------------------------------
# Il segnale della chiusura di ieri decide la posizione di oggi. Un cambio = un acquisto o una vendita dell'intera posizione.
STRATEGIE = {
    "bh": ("Buy & hold", ("bh",)),
    "sma10": ("Prezzo sopra la media a 10 giorni", ("sopra_media", 10)),
    "sma20": ("Prezzo sopra la media a 20 giorni", ("sopra_media", 20)),
    "sma50": ("Prezzo sopra la media a 50 giorni", ("sopra_media", 50)),
    "sma100": ("Prezzo sopra la media a 100 giorni", ("sopra_media", 100)),
    "sma200": ("Prezzo sopra la media a 200 giorni", ("sopra_media", 200)),
    "cross1050": ("Incrocio 10/50", ("incrocio", 10, 50)),
    "cross": ("Incrocio 50/200", ("incrocio", 50, 200)),
    "mom63": ("Momentum a 3 mesi", ("momentum", 63)),
    "mom": ("Momentum a 12 mesi", ("momentum", 252)),
    "ritorno": ("Ritorno alla media nel trend", ("ritorno_media", 5, 200)),
}
ID_BH, ID_FILTRO, ID_MEDIA = "bh", "sma200", "sma50"
NOMI_ESENTI = tuple(v[0] for v in STRATEGIE.values())

SEDUTE_ANNO = 252
INIZIO_TEST_SEDUTE = 260           # tutte le regole partono dallo stesso giorno (serve il momentum a 252 sedute)

# --- Costo di pareggio ---------------------------------------------------------------------------------------------------------
COSTO_MAX_RICERCA = 0.05           # si cerca fino al 5% per cambio; oltre, la regola è registrata come "oltre il 5%"
COSTO_TIPICO = 0.001               # 0,1%: costo tipico citato nel testo (commissione + spread + slippage di un ETF molto liquido)
COSTO_CURVA = tuple(round(0.0005 * k, 4) for k in range(0, 21))   # griglia 0 - 1% per le curve del grafico
ORDINE_ESEMPIO = 5000              # euro per ordine, solo per tradurre il costo percentuale in euro

# --- Scimmie: stessa frequenza di cambi della regola ID_MEDIA ----------------------------------------------------------------------
SEME = 20261024
N_SCIMMIE = 500

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------------------------
SOGLIA_SPEARMAN = -0.8             # ipotesi 1
SOGLIA_FILTRO = 0.005              # ipotesi 2: costo di pareggio (Sharpe) del filtro a 200 giorni oltre lo 0,5%
CAMBI_VELOCI_ANNO = 10.0           # ipotesi 3: regole con almeno 10 cambi all'anno
FATTORE_INSTABILITA = 2.0          # ipotesi 4
SOGLIA_SCIMMIE = 0.10              # ipotesi 5

IPOTESI = (
    "1) Più una regola cambia posizione, più presto muore: la correlazione di rango di Spearman tra cambi all'anno e costo di pareggio "
    "(Sharpe) sulle dieci regole è pari o inferiore a -0,8. "
    "2) Il filtro a 200 giorni, che cambia poco, ha un costo di pareggio sullo Sharpe superiore allo 0,5% per cambio. "
    "3) Ogni regola con almeno 10 cambi all'anno ha un costo di pareggio sullo Sharpe inferiore allo 0,1% per cambio, il costo tipico di un ETF liquido. "
    "4) Il costo di pareggio non è stabile nel tempo: dividendo il periodo in due metà, per almeno metà delle regole il più alto dei due valori "
    "è più del doppio del più basso. "
    "5) Il caso non batte il buy & hold nemmeno gratis: meno del 10% delle scimmie con la stessa frequenza di cambi del prezzo sopra la media a 50 giorni "
    "ha, a costo zero, uno Sharpe più alto del buy & hold."
)
