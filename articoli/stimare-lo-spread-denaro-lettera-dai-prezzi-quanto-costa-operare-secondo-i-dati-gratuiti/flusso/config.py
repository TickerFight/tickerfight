"""Parametri dell'articolo n. 103 - "Stimare lo spread denaro-lettera dai prezzi".

Tutti i parametri stanno qui; gli script numerati li leggono da questo file. Le ipotesi sono scritte prima di guardare i risultati.

Lo spread denaro-lettera (la differenza tra il prezzo a cui si compra e quello a cui si vende) è il costo di operare più citato e meno osservato: nei dati
giornalieri gratuiti non ci sono le quotazioni, ci sono solo apertura, massimo, minimo e chiusura. Si provano due stimatori che ricavano lo spread dai soli prezzi:
quello di Corwin e Schultz (dal rapporto tra massimo e minimo su due giorni consecutivi: il massimo contiene lo spread, la varianza cresce con il tempo ma lo spread no)
e quello di Roll (dalla covarianza tra variazioni consecutive della chiusura). Si applicano a sette ETF dal 2003 (prezzi NON corretti, perché i rapporti
intragiornalieri non cambiano ma la chiusura grezza serve per il minimo imposto dal tick). Non abbiamo le quotazioni vere: l'unico riferimento esterno ai dati è il
minimo teorico dello spread, un centesimo di dollaro diviso il prezzo (il tick minimo). Si usa la versione base dello stimatore, senza la correzione per i salti
notturni, e si pongono a zero le stime negative (come fanno gli autori).
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

TICKERS = ("SPY", "QQQ", "IWM", "EFA", "EEM", "GLD", "TLT")
INIZIO_DOWNLOAD = "2003-01-01"
FUSO_BORSA = "America/New_York"
FILE_METADATI = DATI / "metadati.json"
SENTINELLA = DATI / "spy.csv"
DESCRIZIONE_DATI = "le aperture, i massimi, i minimi e le chiusure giornaliere (non corrette) di sette ETF"
NOMI_ESENTI = ("SPY", "QQQ", "IWM", "EFA", "EEM", "GLD", "TLT", "ETF", "Corwin", "Schultz", "Roll", "S&P 500", "OHLC")

def file_dati(t: str) -> Path:
    return DATI / f"{t.lower()}.csv"

TICK = 0.01                          # dollari: il minimo scostamento di prezzo
GIORNI_ANNO = 252
MESE_CRISI = "2020-03"               # il mese del crollo del Covid
SOGLIA_PRIMA_ANNO = "2013-01-01"     # per la stabilità: seconda metà del campione

# --- Soglie delle ipotesi ---------------------------------------------------------------------------------------
H1_MULTIPLO = 10.0                   # 1) stima media di SPY almeno 10 volte il minimo imposto dal tick
H2_QUOTA_NEG = 0.20                  # 2) quota di coppie di giorni con stima grezza negativa, SPY: oltre il 20%
H3_CORR = 0.50                       # 3) correlazione mensile tra stima e volatilità di SPY: sopra 0,5
H5_MULTIPLO = 3.0                    # 5) marzo 2020: la stima di SPY almeno 3 volte la mediana dei mesi
H6_QUOTA_ROLL = 0.50                 # 6) Roll non definito in oltre la metà dei mesi, SPY

IPOTESI = (
    "1) La stima media di Corwin e Schultz per SPY è almeno 10 volte il minimo teorico imposto dal tick: lo stimatore sovrastima lo spread di un ETF liquidissimo. "
    "2) Per SPY oltre il 20% delle stime su due giorni è negativo prima di porle a zero: il segnale è più piccolo del rumore. "
    "3) La stima media mensile di SPY è correlata con la volatilità mensile (deviazione standard dei rendimenti giornalieri) con un coefficiente superiore a 0,5: lo stimatore misura in parte la volatilità. "
    "4) Nell'intero periodo la stima media è più alta per EEM che per SPY e più alta per IWM che per SPY: l'ordine tra ETF più e meno liquidi è quello atteso. "
    "5) Nel mese di marzo 2020 la stima media di SPY è almeno 3 volte la mediana dei mesi. "
    "6) Lo stimatore di Roll non è definito (la covarianza è positiva) in oltre la metà dei mesi per SPY."
)
