"""Parametri dell'articolo n. 3 - "Prezzi adjusted e non adjusted: l'errore che gonfia i risultati".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni numero
dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.

Idea: Yahoo Finance dà due colonne di prezzo, «Close» (chiusura corretta per gli split ma NON per i dividendi) e
«Adj Close» (corretta anche per i dividendi, cioè rendimento totale). Misuriamo quanto sbaglia chi usa la prima per
valutare un buy & hold e una regola a medie mobili, e che cosa succede se si usano prezzi non corretti per gli split
(ricostruiti dai dati). Il test è su sei strumenti scelti a priori, con dividendi molto diversi.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
# (chiave, ticker, descrizione). Scelti prima di vedere i dati: indice largo, tecnologia, utility, immobiliare,
# un titolo con dividendi stabili e un titolo con molti split.
STRUMENTI = [
    ("spy", "SPY", "SPY (S&P 500)"),
    ("qqq", "QQQ", "QQQ (Nasdaq 100)"),
    ("xlu", "XLU", "XLU (utility USA)"),
    ("vnq", "VNQ", "VNQ (immobiliare USA)"),
    ("ko", "KO", "Coca-Cola"),
    ("aapl", "AAPL", "Apple"),
]
INIZIO_DOWNLOAD = "1990-01-01"
FUSO_BORSA = "America/New_York"
DESCRIZIONE_DATI = "i prezzi giornalieri di sei strumenti USA (SPY, QQQ, XLU, VNQ, Coca-Cola e Apple), con dividendi e split"
URL_FONTE = "https://finance.yahoo.com/"

# --- Convenzioni di calcolo ---------------------------------------------
INIZIO_TEST_SEDUTE = 300         # le prime sedute servono per le medie; tutto parte dallo stesso giorno
SMA_VELOCE = 50
SMA_LENTA = 200
RITARDO_ONESTO = 1               # il segnale della chiusura di ieri decide la posizione di oggi
CAPITALE = 500.0                 # solo per dare un'idea: valori lordi, senza commissioni né tasse
SOGLIA_SEGNALE_PP = 0.005        # ipotesi 4: scarto massimo di rendimento annuo tra segnale su Close e su Adj Close
SOGLIA_RAPPORTO_SPY = 0.75       # ipotesi 3: capitale finale a soli prezzi / capitale finale a rendimento totale (SPY)
SOGLIA_SPEARMAN = 0.8            # ipotesi 2: correlazione di rango tra dividend yield e divario

# --- Ipotesi, scritte PRIMA di guardare i risultati --------------------------------------------
IPOTESI = (
    "1) Per tutti e sei gli strumenti il rendimento annuo del buy & hold calcolato sulla colonna Close (solo prezzo) è più basso di quello "
    "calcolato su Adj Close (rendimento totale). "
    "2) Il divario è tanto più grande quanto più alto è il dividend yield: la correlazione di rango (Spearman) tra yield medio e divario è sopra 0,8. "
    "3) Per SPY, su tutta la storia disponibile, il capitale finale calcolato sui soli prezzi è meno dei tre quarti di quello a rendimento totale. "
    "4) Una regola a medie 50/200 che usa Close per il segnale invece di Adj Close cambia il rendimento annuo di meno di mezzo punto percentuale "
    "per ogni strumento: l'errore grosso non sta nel segnale ma nel rendimento che si misura. "
    "5) Valutare la regola sui soli prezzi sbaglia meno del buy & hold (perché la regola è investita solo una parte del tempo): "
    "l'errore sul rendimento annuo della regola è più piccolo del divario del buy & hold per ogni strumento. "
    "6) Per Apple, usare i prezzi grezzi non corretti per gli split (ricostruiti dai dati) fa scattare falsi segnali: la regola 50/200 fa più cambi di posizione "
    "e rende meno della versione con prezzi corretti."
)
