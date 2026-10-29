# L'intervallo di confidenza dello Sharpe ratio: quanto vale davvero uno Sharpe di backtest

L'articolo, con risultati e grafici, uscirà a breve sul blog [TickerFight](https://ticker-fight.blogspot.com).

## Cosa c'è in questa cartella

```
l-intervallo-di-confidenza-dello-sharpe-ratio-quanto-vale-davvero-uno-sharpe-di-backtest/
├── requirements.txt   librerie Python, versioni fissate
└── flusso/
    ├── 01_scarica_dati.py
    ├── 02_backtest_e_test.py
    ├── 03_grafici.py
    ├── config.py
    ├── funzioni.py
    └── verifica_motore.py
```

## Come si rifà

```bash
cd articoli/l-intervallo-di-confidenza-dello-sharpe-ratio-quanto-vale-davvero-uno-sharpe-di-backtest
python -m venv .venv
source .venv/bin/activate          # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

python flusso/verifica_motore.py
python flusso/01_scarica_dati.py
python flusso/02_backtest_e_test.py
python flusso/03_grafici.py
```

Il primo passo controlla il motore di simulazione su dati inventati (se c'è); poi si scaricano i prezzi da Yahoo Finance in `dati/`, si calcolano i risultati in `risultati/` e i grafici in `figure/`. Parametri, ipotesi e seme dei sorteggi sono in `flusso/config.py`. Yahoo a volte corregge i prezzi storici: con dati scaricati in un altro giorno i numeri possono differire di poco da quelli dell'articolo.
