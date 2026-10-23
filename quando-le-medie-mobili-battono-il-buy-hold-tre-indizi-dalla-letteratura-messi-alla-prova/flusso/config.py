"""Parametri dell'articolo bonus - "Quando le medie mobili battono il buy & hold?".

Tutti i parametri dell'analisi stanno qui. Gli script numerati li leggono da questo file, così ogni
numero dell'articolo si può ricondurre a una scelta dichiarata e nessun valore è nascosto nel codice.
L'articolo è fuori programmazione e fuori catalogo: per questo la cartella si chiama "bonus" e non ha numero.

Idea: nell'articolo sui 50 titoli la regola 50/200 ha battuto il buy & hold solo su 11 titoli. Qui ci
chiediamo se si può prevedere QUALI, usando caratteristiche del titolo misurate PRIMA dell'inizio del test.
"""
from pathlib import Path

# --- Percorsi -----------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
DATI = BASE / "dati"
DATI_SVIL = DATI / "titoli_sviluppo"          # i 50 titoli dell'articolo precedente (copia dei file già scaricati)
DATI_VAL = DATI / "titoli_validazione"        # titoli nuovi, scaricati dal passo 1
RISULTATI = BASE / "risultati"
FIGURE = BASE / "figure"

# --- Dati ---------------------------------------------------------------
TICKER_CAMBIO = "EURUSD=X"
INIZIO_DOWNLOAD = "2020-01-01"
FUSO_BORSA = "America/New_York"
FILE_COMPOSIZIONE = DATI / "sp500_composizione.csv"     # stesso elenco dell'articolo precedente (stesso ordine di sorteggio)
FILE_CAMBIO = DATI / "eurusd_giornaliero.csv"
FILE_SELEZIONE_SVIL = DATI / "selezione_sviluppo.csv"
FILE_META_SVIL = DATI / "metadati_sviluppo.json"
FILE_SELEZIONE_VAL = DATI / "selezione_validazione.csv"
FILE_METADATI = DATI / "metadati.json"
DESCRIZIONE_DATI = "chiusure e aperture giornaliere di 200 titoli dell'S&P 500 e cambio euro/dollaro"
URL_FONTE = "https://finance.yahoo.com/"
NOTA_COLONNA = ("Open e Close non corretti per i dividendi (già corretti per gli split): "
                "i dividendi non sono considerati, né per la regola né per il buy & hold")

# --- Campioni -----------------------------------------------------------
# Sviluppo: i 50 titoli dell'articolo precedente (sorteggio con seme 2026). Li abbiamo già visti: servono a esplorare.
# Validazione: titoli NUOVI, presi con lo stesso sorteggio (stesso seme, stesso ordine) dopo quelli già usati,
# i primi N_VALIDAZIONE con dati completi. Non sono stati guardati prima di fissare le ipotesi: servono a confermare.
N_VALIDAZIONE = 150
SEME = 2026
SEDUTE_MINIME_PRIMA = 420     # sedute prima dell'inizio del test: 200 per la media lenta più i 200 giorni per contare gli incroci

# --- Scenario dell'investitore (identico agli articoli precedenti) ----------
CAPITALE = 500.0
COMMISSIONE = 1.0
ALIQUOTA = 0.26
ANNI_TEST = 5
SMA_VELOCE = 50
SMA_LENTA = 200
MODO_PRINCIPALE = "apertura"

# --- Caratteristiche dei titoli, misurate PRIMA del primo ordine -------------
FINESTRA_VOLATILITA = 252     # sedute precedenti l'inizio del test
FINESTRA_RENDIMENTO = 252
FINESTRA_INCROCI = 200

# --- Statistica ----------------------------------------------------------
N_PERMUTAZIONI = 10000
N_BOOTSTRAP = 2000
SEME_STAT = 7
CASO_STUDIO = "BAX"           # Baxter International, ultimo in classifica per il buy & hold nell'articolo precedente

# --- Ipotesi, scritte PRIMA di guardare come le caratteristiche si legano al risultato -------------------
# Il segno si riferisce alla correlazione (di rango) tra la caratteristica e la differenza finale regola meno
# buy & hold: positivo = la regola va meglio quando la caratteristica è alta.
IPOTESI = {
    "vol": ("+", "Volatilità annualizzata dei rendimenti giornalieri nell'anno precedente. Han, Yang e Zhou (2013): "
                 "le medie mobili battono il buy & hold soprattutto sui titoli più volatili, quelli con più incertezza "
                 "sull'informazione."),
    "ret": ("-", "Rendimento dei dodici mesi precedenti. Zakamulin (2015): le regole a medie mobili tendono a battere "
                 "il mercato nelle fasi ribassiste; Moskowitz, Ooi e Pedersen (2012): i rendimenti passati tendono a "
                 "proseguire per mesi. Un titolo che arriva da un anno brutto ha più probabilità di proseguire in "
                 "ribasso, e la regola, che sta fuori, ne trae vantaggio."),
    "inc": ("-", "Numero di incroci tra le due medie nei 200 giorni precedenti. Zakamulin (2015): le regole generano "
                 "molti falsi segnali quando il titolo non ha un trend chiaro. Più incroci già visti, più falsi "
                 "segnali ci aspettiamo, e peggio va alla regola."),
}
IPOTESI_COMPOSITO = ("Un indice che somma, senza alcuna stima dai dati, i ranghi percentuali della volatilità, "
                     "meno quelli del rendimento passato, meno quelli degli incroci, ordina i titoli dal meno al più "
                     "favorevole alla regola. Ci aspettiamo che la regola vinca più spesso nel terzo dei titoli con "
                     "l'indice più alto che nel terzo con l'indice più basso, anche sui titoli di validazione.")
