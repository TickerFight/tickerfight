# Il Santa Claus rally esiste? Sette sedute a cavallo dell'anno, sette indici e la fortuna

**Domanda:** le ultime cinque sedute di dicembre e le prime due di gennaio rendono davvero più di sette sedute qualunque, o è fortuna?

L'articolo completo, con risultati e grafici, è sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Strategia:** si compra alla chiusura della sesta-ultima seduta di dicembre e si vende alla chiusura della seconda seduta di gennaio (ultime cinque sedute dell'anno più prime due del nuovo: sette sedute); il resto dell'anno si sta in cassa, che non rende. Il calendario è noto in anticipo: nessun look-ahead.
- **Indici:** S&P 500, Dow Jones, Nasdaq Composite, DAX, FTSE 100, CAC 40, Nikkei 225, scelti prima di guardare i dati. Valuta locale, indici di prezzo (senza dividendi).
- **Confronti:** buy & hold sullo stesso indice; il rendimento medio di una finestra di sette sedute qualunque; scimmie con la stessa dieta (una finestra di sette sedute per anno, piazzata a caso dentro il suo anno); una griglia di varianti della finestra (da tre a sette sedute di dicembre, da zero a quattro di gennaio) per misurare quanto il risultato dipende dalla definizione.
- **Test:** intervallo bootstrap sugli anni, scimmie con correzione di Holm sugli indici, confronto prima e dopo il 1999.
- **Costi:** 1 unità di valuta a ordine, tassa del 26% con compensazione delle minusvalenze.

## Cosa c'è in questa cartella

```
163-il-santa-claus-rally/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica sette indici azionari
    ├── 02_backtest_e_test.py  finestra, buy & hold, finestre generiche, griglia di varianti, scimmie, test
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              indici, parametri e ipotesi, scritti prima dei risultati
    ├── finestre.py            ricerca delle finestre, motore veloce per le scimmie
    ├── simulazione.py         motore: ordini, commissioni, tassa e minusvalenze
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd 163-il-santa-claus-rally
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.

## Fonti citate nell'articolo

- Patel, J. B. (2023), *The Santa Claus Rally in U.S. Stock Market Returns*, Journal of Accounting and Finance 23(1).
- Nippani, S., Washer, K. M., Johnson, R. R. (2015), *Yes, Virginia, There Is a Santa Claus Rally: Statistical Evidence Supports Higher Returns Globally*, Journal of Financial Planning 28(3), 55-60.
