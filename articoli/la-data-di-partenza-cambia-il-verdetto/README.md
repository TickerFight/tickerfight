# La data di partenza cambia il verdetto

**Domanda:** il verdetto su una regola di trading, qui un filtro di tendenza a 200 sedute sull'S&P 500 contro il buy & hold, dipende dalla data in cui si comincia a guardarla?

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Il disegno

- **Regola:** investiti se la chiusura sta sopra la media delle ultime 200 chiusure, altrimenti liquidità a rendimento zero; segnale eseguito alla chiusura successiva; 10 punti base per ogni cambio.
- **Misure:** rendimento annuo composto, Sharpe e perdita massima su finestre che partono da ogni mese dal 1928.
- **Confronti:** buy & hold sullo stesso indice; due decenni di riferimento (partenze a gennaio 1990 e 2000).

## Cosa c'è in questa cartella

```
la-data-di-partenza-cambia-il-verdetto/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py     scarica l'S&P 500 dal 1927 (i dati sono quelli già usati negli articoli 301 e 426)
    ├── 02_backtest_e_test.py  regola e buy & hold da ogni mese di partenza, finestre di 5, 10 e 20 anni
    ├── 03_grafici.py          i grafici
    ├── config.py              parametri e ipotesi, scritti prima dei risultati
    ├── funzioni.py            filtro a 200 sedute, metriche su finestre, inizi di mese
    └── verifica_motore.py     controlli su dati inventati (ritardo del segnale, costi, metriche)
```

## Come si rifà

```bash
cd articoli/la-data-di-partenza-cambia-il-verdetto
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
