# Un ordine al mese contro uno a settimana: chi guarda meno guadagna di più?

**Domanda:** la stessa regola di trend (chiusura sopra la media a 200 sedute) rende di più se il segnale si guarda ogni seduta, una volta a settimana o una volta al mese? Condizioni di chi parte con 1.000 €: commissione per ordine in tre scenari, tassa del 26% con minusvalenze riportate, azioni frazionate.

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Regola:** investito se la chiusura sta sopra la media mobile semplice a 200 sedute. Cambia solo quando si guarda il segnale: ogni seduta, l'ultima seduta della settimana, l'ultima del mese. Ordine alla chiusura della seduta successiva (nessun look-ahead).
- **Strumenti:** ETF azionario mondiale e ETF sull'S&P 500 (euro, Milano), indice S&P 500 in dollari convertito in euro.
- **Condizioni:** 1.000 €; commissione 0 €, 2 € a ordine e 0,1%; tassa 26% con compensazione delle minusvalenze; dividendi, bollo e spread non considerati.
- **Test:** scimmie (stessa durata investita e stesso numero di periodi), 9 test con la correzione di Holm.

## Cosa c'è in questa cartella

```
un-ordine-al-mese-contro-uno-a-settimana-chi-guarda-meno-guadagna-di-piu/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica due ETF, l'indice S&P 500 e il cambio euro-dollaro
    ├── 02_backtest_e_test.py  buy & hold, tre frequenze di decisione, scimmie, correzione di Holm
    ├── 03_grafici.py          i quattro grafici
    ├── config.py              strumenti, parametri e ipotesi, scritti prima dei risultati
    ├── simulazione.py         motore in euro: ordini, commissioni, tassa, minusvalenze, scimmie
    └── verifica_motore.py     controlli su dati inventati
```

## Come si rifà

```bash
cd articoli/un-ordine-al-mese-contro-uno-a-settimana-chi-guarda-meno-guadagna-di-piu
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
