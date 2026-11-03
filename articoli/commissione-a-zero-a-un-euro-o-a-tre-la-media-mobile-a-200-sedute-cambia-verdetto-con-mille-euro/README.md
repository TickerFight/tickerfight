# Commissione a zero, a un euro o a tre: la media mobile a 200 sedute cambia verdetto con mille euro?

**Domanda:** una regola di trend fissa (chiusura sopra la media a 200 sedute, segnale guardato a ogni seduta) cambia verdetto se la commissione per ordine passa da 0 a 1 e a 3 euro? Condizioni di chi parte con 1.000 €: tassa del 26% con minusvalenze riportate, azioni frazionate.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Regola:** investito se la chiusura sta sopra la media mobile semplice a 200 sedute; ordine alla chiusura della seduta successiva (nessun look-ahead). Non cambia mai: cambia solo la commissione.
- **Condizioni:** 1.000 €; commissione fissa 0, 1 e 3 € per ordine; tassa 26% con compensazione delle minusvalenze; dividendi, bollo e spread non considerati.
- **Test:** griglia di commissioni da 0 a 10 € per trovare l'eventuale punto di pareggio con il buy & hold; scimmie (stessa durata investita e stesso numero di periodi), 9 test con la correzione di Holm.

## Cosa c'è in questa cartella

```
commissione-a-zero-a-un-euro-o-a-tre-la-media-mobile-a-200-sedute-cambia-verdetto-con-mille-euro/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica due ETF, l'indice S&P 500 e il cambio euro-dollaro
    ├── 02_backtest_e_test.py  buy & hold e trend nei tre scenari, griglia 0-10 euro, scimmie, correzione di Holm
    ├── 03_grafici.py          i tre grafici
    ├── config.py              strumenti, parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore in euro: ordini, commissioni, tassa, minusvalenze, scimmie
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/commissione-a-zero-a-un-euro-o-a-tre-la-media-mobile-a-200-sedute-cambia-verdetto-con-mille-euro
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
