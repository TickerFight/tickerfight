# «Vendi a maggio e vai via»: otto indici europei, la fortuna e il buy & hold

**Domanda:** il vecchio proverbio «vendi a maggio e vai via» funziona sugli indici azionari europei, o la differenza tra novembre-aprile e maggio-ottobre è fortuna?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Strategia:** si compra alla chiusura dell'ultima seduta di ottobre e si vende alla chiusura dell'ultima seduta di aprile; da maggio a ottobre si sta in cassa (che non rende). Il calendario è noto in anticipo: nessun look-ahead.
- **Indici:** DAX, FTSE 100, CAC 40, SMI, IBEX 35, AEX, Euro Stoxx 50, FTSE MIB, scelti prima di guardare i dati. Valuta locale, senza cambio. Il DAX include i dividendi, gli altri no; il confronto è sempre dentro lo stesso indice.
- **Confronti:** buy & hold sullo stesso indice; i dodici calendari possibili di sei mesi; scimmie con la stessa dieta (stesso numero di ordini e stessa durata di ogni periodo investito, piazzati a caso dentro ogni anno).
- **Test:** differenza media tra i due semestri con bootstrap sugli anni, correzione di Holm sugli indici, confronto prima e dopo il 2002.
- **Costi:** 1 unità di valuta a ordine, tassa del 26% con compensazione delle minusvalenze.

## Cosa c'è in questa cartella

```
vendi-a-maggio-e-vai-via-otto-indici-europei-la-fortuna-e-il-buy-hold/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica otto indici europei
    ├── 02_backtest_e_test.py  strategia, buy & hold, dodici calendari, scimmie, test
    ├── 03_grafici.py          i cinque grafici
    ├── config.py              indici, parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore: ordini, commissioni, tassa e minusvalenze
    └── verifica_motore.py     19 controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/vendi-a-maggio-e-vai-via-otto-indici-europei-la-fortuna-e-il-buy-hold
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

- Bouman, S., Jacobsen, B. (2002), *The Halloween Indicator, "Sell in May and Go Away": Another Puzzle*, American Economic Review 92(5), 1618-1635.
- Maberly, E. D., Pierce, R. M. (2004), *Stock Market Efficiency Withstands Another Challenge: Solving the "Sell in May/Buy after Halloween" Puzzle*, Econ Journal Watch 1(1), 29-46.
