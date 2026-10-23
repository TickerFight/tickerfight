# Il look-ahead bias in 10 righe di codice: quanto vale l'illusione?

**Domanda:** se calcolo il segnale con la chiusura di oggi e lo applico al rendimento di oggi, quanto vale l'illusione? E come mi accorgo di averlo fatto?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Il look-ahead:** posizione[t] = segnale[t], cioè la chiusura di oggi decide se oggi si è già dentro. La versione onesta usa il segnale di ieri: `segnale.shift(1)`.
- **Tre regole, dalla più veloce alla più lenta:** chiusura sopra quella di ieri; chiusura sopra la media a 20 giorni; media a 50 giorni sopra la media a 200.
- **Il test del ritardo:** si sposta il segnale di 0, 1, 2 ... 10 sedute. Un rendimento che crolla appena si ritarda di un giorno è il segno del look-ahead.
- **Griglia di medie:** l'illusione per 29 coppie veloce/lenta, per vedere come cresce con la velocità della regola.
- **Niente commissioni né tasse:** l'obiettivo è isolare l'effetto del look-ahead.

## Cosa c'è in questa cartella

```
il-look-ahead-bias-in-10-righe-di-codice-quanto-vale-l-illusione/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927
    ├── 02_backtest_e_test.py  tre regole con e senza look-ahead, test del ritardo, griglia di medie, sottoperiodi
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri, regole e ipotesi, scritti prima dei risultati
    ├── motore_vettoriale.py   segnale, posizione con ritardo, valore, rendimento annuo, perdita massima
    └── verifica_motore.py     17 controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/il-look-ahead-bias-in-10-righe-di-codice-quanto-vale-l-illusione
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
