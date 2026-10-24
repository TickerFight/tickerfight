# Che cos'è davvero un backtest, e che cosa non è?

**Domanda:** che cosa dice, e che cosa non dice, un backtest? Si costruisce il più semplice possibile (segnale, esecuzione, rendimenti) con la regola più nota, lo SPY sopra la media a 200 giorni, e lo si legge contro il buy & hold, le epoche, le finestre di dieci anni e mille calendari casuali.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Segnale:** la chiusura è sopra la media a 200 giorni (calcolata sulla chiusura non corretta).
- **Esecuzione:** il segnale della chiusura di ieri decide la posizione di oggi (`shift(1)`); nella variante prudente l'ordine è eseguito alla chiusura successiva (`shift(2)`).
- **Rendimenti:** dalla chiusura corretta per i dividendi; in cassa il rendimento è zero.
- **Confronti:** buy & hold, tre epoche, finestre mobili di dieci anni (una ogni mese di borsa), 1.000 calendari casuali con gli stessi periodi dentro e fuori della regola (stessi blocchi, ordine mescolato).
- **Niente commissioni né tasse:** i valori sono lordi.

## Cosa c'è in questa cartella

```
che-cos-e-davvero-un-backtest-e-che-cosa-non-e/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica lo SPY dal 1993
    ├── 02_backtest_e_test.py  regola, buy & hold, epoche, finestre di dieci anni, calendari casuali
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── motore_vettoriale.py   segnale, posizione con ritardo, valore, rendimento annuo, perdita massima, calendari casuali
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/che-cos-e-davvero-un-backtest-e-che-cosa-non-e
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
